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
