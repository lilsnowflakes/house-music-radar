"""
genre_check.py
Venue calendars carry no genre tags, so each act is checked before it can appear:
  1. Spotify artist genres (needs the Spotify keys)
  2. MusicBrainz tags (free, no key) when Spotify has nothing
Verdicts:  house        at least one act on the bill is house -> kept, genres shown
           not_house    genres found, none are house          -> dropped, named in Source health
           unverified   no reliable match for any act         -> kept, flagged "?" for you to judge
"""

import re
import sys
import os
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scoring.scoring import get_spotify_token

VENUE_SOURCES = {"DICE venue", "Discotech", "Framework"}
UA = {"User-Agent": "HouseMusicRadar/1.0 (personal event digest)"}
EXTRA_HOUSE = {"nu disco", "nu-disco", "disco", "uk garage", "garage", "minimal", "minimal techno house",
               "deep tech", "organic", "afro tech", "melodic house and techno"}
_cache = {}
_last_mb = [0.0]


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def split_acts(title):
    """'Framework Afterparty ft. Pete Tong' -> ['Pete Tong']; 'Kyle Starkey & Paige Tomlinson' -> both."""
    t = re.sub(r"\(.*?\)", " ", title)
    t = re.sub(r"(?i)\b(live|dj set|hybrid set|extended set|opening party|second date|presents?)\b", " ", t)
    parts = re.split(r"(?i)\s+(?:ft\.?|feat\.?|w/|with|b2b|x|&|and|vs\.?|\+)\s+|,|\s-\s|:", t)
    acts = [p.strip() for p in parts if len(p.strip()) > 1]
    # a party-name prefix ("Framework Afterparty") is not an act
    return [a for a in acts if not re.search(r"(?i)afterparty|after party|nye|new years|warehouse|night|party|passes|tour$", a)] or acts[:1]


def is_house_genre(g):
    g = g.lower()
    return "house" in g or g in EXTRA_HOUSE


def _spotify_genres(name):
    tok = get_spotify_token()
    if not tok:
        return []
    r = requests.get("https://api.spotify.com/v1/search", headers={"Authorization": f"Bearer {tok}"},
                     params={"q": name, "type": "artist", "limit": 5}, timeout=10)
    for it in r.json().get("artists", {}).get("items", []):
        if norm(it.get("name", "")) == norm(name) and it.get("genres"):
            return it["genres"]
    return []


def _musicbrainz_genres(name):
    wait = 1.1 - (time.time() - _last_mb[0])
    if wait > 0:
        time.sleep(wait)
    _last_mb[0] = time.time()
    r = requests.get("https://musicbrainz.org/ws/2/artist/", headers=UA, timeout=10,
                     params={"query": f'artist:"{name}"', "fmt": "json", "limit": 5})
    for a in r.json().get("artists", []):
        if norm(a.get("name", "")) == norm(name) and a.get("score", 0) >= 90 and a.get("tags"):
            tags = sorted(a["tags"], key=lambda t: -t.get("count", 0))
            return [t["name"] for t in tags[:8]]
    return []


def genres_for(name):
    if name in _cache:
        return _cache[name]
    out = ([], "")
    for label, fn in (("Spotify", _spotify_genres), ("MusicBrainz", _musicbrainz_genres)):
        try:
            g = fn(name)
        except Exception:
            g = []
        if g:
            out = (g, label)
            break
    _cache[name] = out
    return out


def verify(ev):
    seen_any, house_g, by = [], [], ""
    for act in split_acts(ev.get("artist") or ev.get("title", "")):
        g, src = genres_for(act)
        if g:
            seen_any += g
            by = by or src
            house_g += [x for x in g if is_house_genre(x)]
    if house_g:
        return {"verdict": "house", "genres": list(dict.fromkeys(house_g))[:4], "by": by}
    if seen_any:
        return {"verdict": "not_house", "genres": list(dict.fromkeys(seen_any))[:4], "by": by}
    return {"verdict": "unverified", "genres": [], "by": ""}


def filter_venue_events(events):
    """Checks venue-calendar events only (19hz etc. already come with genre tags).
    Returns (kept, dropped)."""
    kept, dropped = [], []
    for ev in events:
        if ev.get("source") not in VENUE_SOURCES:
            kept.append(ev)
            continue
        ev["house_check"] = verify(ev)
        if ev["house_check"]["verdict"] == "not_house":
            dropped.append(ev)
            continue
        if ev["house_check"]["verdict"] == "house":
            ev["genres"] = ev["house_check"]["genres"]
        kept.append(ev)
    return kept, dropped
