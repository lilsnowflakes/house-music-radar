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

VENUE_SOURCES = {"DICE venue", "Discotech", "Framework", "RA", "DICE", "SceneStar", "Heard", "SeatGeek", "Edmtrain", "Reddit", "Ticketmaster"}
UA = {"User-Agent": "HouseMusicRadar/1.0 (personal event digest)"}
EXTRA_HOUSE = {"nu disco", "nu-disco", "disco", "uk garage", "garage", "minimal", "minimal techno house",
               "deep tech", "organic", "afro tech", "melodic house and techno",
               # techno family: same rooms, same crowd (Framework, Sound); kept, not dropped
               "techno", "melodic techno", "minimal techno", "tech-house", "peak time techno", "progressive"}
_cache = {}
_last_mb = [0.0]


def norm(s):
    import unicodedata
    s = ''.join(c for c in unicodedata.normalize('NFKD', s or '') if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _promoters():
    try:
        from config.config import WATCH_PROMOTERS
        return {norm(p) for p in WATCH_PROMOTERS}
    except Exception:
        return set()


def split_acts(title):
    """'Framework Afterparty ft. Pete Tong' -> ['Pete Tong']; 'Kyle Starkey & Paige Tomlinson' -> both.
    'Clinic Wednesdays: Clinic' -> [] (the part before ':' is the party name, and a party or promoter
    name is never looked up as a band)."""
    t = re.sub(r"\(.*?\)", " ", title)
    prefix = ""
    if ":" in t:
        prefix, t = t.split(":", 1)
        # "Bedouin Presents: Saga" -> the act is Bedouin; "Saga" is the name of the night
        m = re.match(r"(?i)^\s*(.+?)\s+(?:presents?|pres\.)\s*$", prefix)
        if m:
            return [m.group(1).strip()]
    # "Only Fire & Friends - Los Angeles": drop place names and "& friends"
    t = re.sub(r"(?i)\s*-\s*(los angeles|la|hollywood|dtla|socal)\s*$", " ", t)
    t = re.sub(r"(?i)\s*(?:&|and)\s+friends\b", " ", t)
    t = re.sub(r"(?i)\b(live|dj set|hybrid set|extended set|opening party|second date|presents?)\b", " ", t)
    parts = re.split(r"(?i)\s+(?:ft\.?|feat\.?|w/|with|b2b|x|&|and|vs\.?|\+)\s+|,|\s-\s|:", t)
    acts = [p.strip() for p in parts if len(p.strip()) > 1]
    promos, np = _promoters(), norm(prefix)
    acts = [a for a in acts if norm(a) not in promos and not (np and norm(a) in np)]
    if not acts:
        return []
    # a party-name prefix ("Framework Afterparty") is not an act
    return [a for a in acts if not re.search(r"(?i)afterparty|after party|nye|new years|warehouse|night|party|passes|tour$", a)] or acts[:1]


# Genres that clearly aren't a house night. Only these can get a show dropped.
NOT_HOUSE = ("rock", "pop", "punk", "metal", "country", "hip hop", "hip-hop", "rap", "jazz", "folk", "indie", "ska",
             "emo", "classical", "reggaeton", "dembow", "corrido", "banda", "christian", "blues", "singer-songwriter",
             "grunge", "hardcore", "merseybeat", "boy group", "girl group", "musical", "comedy", "drum and bass",
             "drum n bass", "jungle", "dubstep", "trap", "riddim", "hardstyle", "americana", "bluegrass", "gospel", "downtempo", "trip hop", "chillwave", "lo-fi")
# Tags that say nothing either way ("electronic", or MusicBrainz housekeeping tags like "lidarr")
VAGUE = ("electronic", "electronica", "dance", "edm", "club", "dj", "lidarr", "seen live", "vocalist", "producer")


def is_clearly_not_house(g):
    g = g.lower()
    return any(w in g for w in NOT_HOUSE) and not is_house_genre(g)


def is_house_genre(g):
    g = g.lower()
    return "house" in g or g in EXTRA_HOUSE


def _spotify_genres(name):
    from scoring.spotify import lookup
    res = lookup(name)
    return (res or {}).get("genres") or []

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
            return [t["name"] for t in tags[:8] if t["name"].lower() not in ("lidarr", "seen live")]
    return []


def genres_for(name):
    from scoring import memory
    if name in _cache:
        return _cache[name]
    rem = memory.get(name, "genres", fresh_only=True)
    if rem is not None:
        memory.STATS["reused"] += 1
        _cache[name] = (rem, memory.get(name, "genres_by", False) or "memory")
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
    if out[0]:
        memory.put(name, genres=out[0], genres_by=out[1])
    else:
        old = memory.get(name, "genres", fresh_only=False)
        if old:
            memory.STATS["fallback"] += 1
            out = (old, memory.get(name, "genres_by", False) or "memory")
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
    clear = [x for x in seen_any if is_clearly_not_house(x)]
    if clear:
        return {"verdict": "not_house", "genres": list(dict.fromkeys(clear))[:4], "by": by}
    if seen_any:   # only vague tags like "electronic": keep it, flagged "?"
        return {"verdict": "unverified", "genres": [], "by": by}
    return {"verdict": "unverified", "genres": [], "by": ""}


def filter_venue_events(events):
    """Checks venue-calendar events only (19hz etc. already come with genre tags).
    Returns (kept, dropped)."""
    kept, dropped = [], []
    for ev in events:
        if ev.get("source") not in VENUE_SOURCES:
            kept.append(ev)
            continue
        own = [x for x in (ev.get("genres") or []) if x and x.lower() not in ("house", "dance/electronic", "electronic")]
        if ev.get("source") in ("Ticketmaster", "SeatGeek") and own:
            # the ticket site already gave a specific genre (e.g. subGenre "House", "Trance"): trust it, save a lookup
            if any(is_house_genre(x) for x in own):
                ev["house_check"] = {"verdict": "house", "genres": [x for x in own if is_house_genre(x)][:3], "by": ev["source"]}
                kept.append(ev)
                continue
            if any(is_clearly_not_house(x) for x in own):
                ev["house_check"] = {"verdict": "not_house", "genres": own[:3], "by": ev["source"]}
                dropped.append(ev)
                continue
        ev["house_check"] = verify(ev)
        if ev["house_check"]["verdict"] == "not_house":
            dropped.append(ev)
            continue
        if ev["house_check"]["verdict"] == "house":
            ev["genres"] = ev["house_check"]["genres"]
        kept.append(ev)
    return kept, dropped
