"""
apis.py - official, key-based event APIs (no scraping).
  SeatGeek  : free client_id. Concerts within 30 miles of downtown LA.
  Edmtrain  : free client key (apply at edmtrain.com/developer-api). Electronic shows in LA.
Edmtrain terms honored: their event link is shown unmodified, data is refreshed daily (never shown
older than 24h on the site), their shows are left out of the email, and past events are not stored.
Both are skipped quietly (shown as "skipped" in Source health) until their key is added as a GitHub secret.
Every show they return still goes through the house check before it can appear.
"""
import os
import sys
from datetime import datetime, timedelta

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import SEATGEEK_CLIENT_ID, EDMTRAIN_CLIENT_KEY
from scrapers.scrapers import normalize_event

LA_LAT, LA_LON = 34.0522, -118.2437
LAST = {}  # name -> (count, note), read by main.py for Source health
UA = {"User-Agent": "HouseMusicRadar/1.0 (personal weekly digest)"}
GENRE_WORDS = ("house", "electronic", "dance", "techno", "disco", "edm")


def _fmt(d):
    return d.strftime("%a %b %-d") + ("" if d.year == datetime.now().year else f", {d.year}")


def scrape_seatgeek(city):
    if city != "los_angeles":
        return []
    if not SEATGEEK_CLIENT_ID:
        LAST["SeatGeek"] = (0, "skipped: add SEATGEEK_CLIENT_ID secret")
        return []
    out = []
    try:
        now = datetime.utcnow()
        for page in (1, 2, 3):
            r = requests.get("https://api.seatgeek.com/2/events", headers=UA, timeout=20, params={
                "client_id": SEATGEEK_CLIENT_ID, "lat": LA_LAT, "lon": LA_LON, "range": "30mi",
                "taxonomies.name": "concert", "per_page": 100, "page": page,
                "datetime_utc.gte": now.strftime("%Y-%m-%dT%H:%M:%S"),
                "datetime_utc.lte": (now + timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%S")})
            if r.status_code != 200:
                raise RuntimeError(f"{r.status_code}: {r.text[:120]}")
            evs = r.json().get("events", [])
            for e in evs:
                perf = e.get("performers") or []
                genres = [g.get("name", "") for p in perf for g in (p.get("genres") or [])]
                text = " ".join(genres + [e.get("title", "")]).lower()
                if genres and not any(w in text for w in GENRE_WORDS):
                    continue  # clearly another genre (rock, country...) per SeatGeek's own tags
                d = datetime.fromisoformat(e["datetime_local"])
                v = e.get("venue") or {}
                ev = normalize_event(
                    title=e.get("title", ""), artist=(perf[0].get("name") if perf else e.get("short_title", "")),
                    venue=v.get("name", ""), city=city, date_str=_fmt(d), genres=[g for g in genres if g],
                    ticket_url=e.get("url", ""), price="", source="SeatGeek")
                ev["address"] = ", ".join(x for x in (v.get("address"), v.get("extended_address")) if x)
                out.append(ev)
            if len(evs) < 100:
                break
        # your artists' LA dates whatever genre SeatGeek files them under (also covers shows sold on AXS,
        # since SeatGeek lists resale tickets for them)
        from config.config import WATCH_ARTISTS
        seen = {x["ticket_url"] for x in out}
        for artist in dict.fromkeys(WATCH_ARTISTS):
            r = requests.get("https://api.seatgeek.com/2/events", headers=UA, timeout=20, params={
                "client_id": SEATGEEK_CLIENT_ID, "q": artist, "lat": LA_LAT, "lon": LA_LON, "range": "60mi", "per_page": 10})
            for e in (r.json().get("events", []) if r.status_code == 200 else []):
                if e.get("url") in seen:
                    continue
                seen.add(e.get("url"))
                d = datetime.fromisoformat(e["datetime_local"])
                v = e.get("venue") or {}
                ev = normalize_event(title=e.get("title", ""), artist=artist, venue=v.get("name", ""), city=city,
                                     date_str=_fmt(d), genres=[], ticket_url=e.get("url", ""), price="", source="SeatGeek")
                ev["address"] = ", ".join(x for x in (v.get("address"), v.get("extended_address")) if x)
                out.append(ev)
        LAST["SeatGeek"] = (len(out), "")
    except Exception as ex:
        LAST["SeatGeek"] = (0, str(ex)[:120])
    return out


def _edm(path, **params):
    r = requests.get(f"https://edmtrain.com/api/{path}", headers=UA, timeout=20,
                     params={**params, "client": EDMTRAIN_CLIENT_KEY})
    j = r.json()
    if not j.get("success", False):
        raise RuntimeError(j.get("message", f"HTTP {r.status_code}"))
    return j.get("data") or []


def scrape_edmtrain(city):
    if city != "los_angeles":
        return []
    if not EDMTRAIN_CLIENT_KEY:
        LAST["Edmtrain"] = (0, "skipped: add EDMTRAIN_CLIENT_KEY secret (free, apply at edmtrain.com/developer-api)")
        return []
    out = []
    try:
        locs = _edm("locations", state="California", city="Los Angeles")
        ids = ",".join(str(l["id"]) for l in locs if l.get("id"))
        if not ids:
            raise RuntimeError("no Los Angeles location id returned")
        for e in _edm("events", locationIds=ids):
            if e.get("livestreamInd"):
                continue
            d = datetime.strptime(e["date"], "%Y-%m-%d")
            v = e.get("venue") or {}
            artists = [a.get("name", "") for a in (e.get("artistList") or []) if a.get("name")]
            title = e.get("name") or ", ".join(artists)
            ev = normalize_event(
                title=title, artist=artists[0] if artists else title, venue=v.get("name", ""), city=city,
                date_str=_fmt(d), genres=[], ticket_url=e.get("link", ""),   # Edmtrain's event link, unmodified (their terms)
                price="", source="Edmtrain")
            ev["address"] = v.get("address", "")
            out.append(ev)
        LAST["Edmtrain"] = (len(out), "")
    except Exception as ex:
        LAST["Edmtrain"] = (0, str(ex)[:120])
    return out


# ----------------------------------------------------------------------------
# Reddit: one user's posts (u/liverichly posts LA shows to r/avesLA), via Reddit's official API.
# Titles look like:  "Carl Cox at The Living Room - Thurs Nov 5"
#                    "Stranger Than; Polo & Pan NYE - Thurs Dec 31"
#                    "Theo Parrish In Conversation - Thurs Nov 12"
# and updates like:  "Solomun moved from Hollywood Blvd to Reframe Studios Outdoors"
# ----------------------------------------------------------------------------
import re as _re
from config.config import env as _env

REDDIT_USERS = ["liverichly"]
REDDIT_UPDATES = []   # (artist, old venue, new venue) from "X moved from A to B" posts; applied in main.py

_TITLE = _re.compile(
    r"^(?P<what>.+?)\s+[-–—]\s+(?:mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)[a-z]*\.?,?\s+"
    r"(?P<mon>[a-z]{3,9})\.?\s+(?P<day>\d{1,2})(?:,?\s*(?P<year>\d{4}))?\s*$", _re.I)
_MOVE = _re.compile(r"^(?P<who>.+?)\s+(?:has\s+)?moved\s+from\s+(?P<old>.+?)\s+to\s+(?P<new>.+?)\s*$", _re.I)
_MON = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}


def parse_reddit_title(title, permalink="", city="los_angeles"):
    """Returns ("event", ev) or ("move", (who, old, new)) or (None, None)."""
    t = title.strip()
    m = _MOVE.match(t)
    if m:
        return "move", (m["who"], m["old"], m["new"])
    m = _TITLE.match(t)
    if not m or m["mon"][:3].lower() not in _MON:
        return None, None
    what = m["what"].strip()
    venue = ""
    if _re.search(r"\s+at\s+", what):
        what, venue = _re.split(r"\s+at\s+(?=[^@]*$)", what, maxsplit=1) if " at " in what else (what, "")
    promoter = ""
    if ";" in what:
        promoter, what = [x.strip() for x in what.split(";", 1)]
    artist = _re.sub(r"\s+(NYE|NYD|live|dj set)$", "", what, flags=_re.I).strip()
    mon, day = _MON[m["mon"][:3].lower()], int(m["day"])
    now = datetime.now()
    year = int(m["year"]) if m["year"] else now.year + (1 if mon < now.month - 1 else 0)
    try:
        d = datetime(year, mon, day)
    except ValueError:
        return None, None
    ev = normalize_event(title=t.split(" - ")[0], artist=artist, venue=venue, city=city, date_str=_fmt(d),
                         genres=[], ticket_url="", price="", source="Reddit")
    ev["reddit_url"] = permalink
    if promoter:
        ev["promoter"] = promoter
    return "event", ev


def scrape_reddit(city):
    if city != "los_angeles":
        return []
    cid, secret = _env("REDDIT_CLIENT_ID"), _env("REDDIT_CLIENT_SECRET")
    if not cid or not secret:
        LAST["Reddit"] = (0, "skipped: add REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET secrets")
        return []
    ua = {"User-Agent": f"python:mos-house-music-radar:v1.0 (by /u/{_env('REDDIT_USERNAME') or 'house-music-radar'})"}
    out = []
    try:
        t = requests.post("https://www.reddit.com/api/v1/access_token", auth=(cid, secret), headers=ua,
                          data={"grant_type": "client_credentials"}, timeout=20)
        if t.status_code != 200:
            raise RuntimeError(f"token {t.status_code}: {t.text[:100]}")
        h = dict(ua, Authorization=f"bearer {t.json()['access_token']}")
        for user in REDDIT_USERS:
            r = requests.get(f"https://oauth.reddit.com/user/{user}/submitted", headers=h,
                             params={"sort": "new", "limit": 50, "raw_json": 1}, timeout=20)
            if r.status_code != 200:
                raise RuntimeError(f"{user}: {r.status_code} {r.text[:100]}")
            for child in r.json().get("data", {}).get("children", []):
                p = child.get("data", {})
                kind, val = parse_reddit_title(p.get("title", ""), "https://www.reddit.com" + p.get("permalink", ""), city)
                if kind == "event":
                    url = p.get("url_overridden_by_dest") or ""
                    if url and not _re.search(r"redd\.it|reddit\.com|imgur", url):
                        val["ticket_url"] = url     # a link post pointing at tickets
                    out.append(val)
                elif kind == "move":
                    REDDIT_UPDATES.append(val)
        LAST["Reddit"] = (len(out), "")
    except Exception as ex:
        LAST["Reddit"] = (0, str(ex)[:120])
    return out


def apply_moves(events):
    """'Solomun moved from Hollywood Blvd to Reframe Studios Outdoors': fix the venue on matching shows."""
    n = 0
    for who, old, new in REDDIT_UPDATES:
        k = _re.sub(r"[^a-z0-9]", "", who.lower())
        for ev in events:
            a = _re.sub(r"[^a-z0-9]", "", (ev.get("artist") or ev.get("title") or "").lower())
            o = _re.sub(r"[^a-z0-9]", "", old.lower())[:8]
            v = _re.sub(r"[^a-z0-9]", "", ev.get("venue", "").lower())
            if k and k in a and (not v or o in v) and ev.get("venue") != new:
                ev["moved_from"], ev["venue"], ev["address"] = ev.get("venue", ""), new, ""
                n += 1
    return n
