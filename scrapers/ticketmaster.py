"""
ticketmaster.py
Finds shows that are ANNOUNCED but NOT YET ON SALE at your Ticketmaster rooms.

Uses the official Ticketmaster Discovery API (free key). An event counts as
"not on sale yet" when its public on-sale start is in the future, or when
Ticketmaster lists the on-sale date as TBD.

Assumption to verify on the first live run: the genre filter below
("Dance/Electronic") is Ticketmaster's genre name for house/electronic shows.
If a room's shows come back empty, loosen CLASSIFICATION to "" and re-run.
"""

import sys
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import TICKETMASTER_API_KEY, TM_LOOKAHEAD_DAYS

BASE = "https://app.ticketmaster.com/discovery/v2"
CLASSIFICATION = "Dance/Electronic"
PACIFIC = ZoneInfo("America/Los_Angeles")


def _get(path: str, params: dict) -> dict:
    params = {**params, "apikey": TICKETMASTER_API_KEY}
    resp = requests.get(f"{BASE}/{path}", params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def find_venue_id(name: str, state: str):
    """Return (id, official name) only when the name really matches."""
    data = _get("venues.json", {
        "keyword": name, "stateCode": state, "countryCode": "US", "size": 10,
    })
    venues = data.get("_embedded", {}).get("venues", [])
    want = name.lower().replace("the ", "")
    for v in venues:
        got = v.get("name", "").lower().replace("the ", "")
        if want in got or got in want:
            return v["id"], v["name"]
    return None, None


def sale_status(ev: dict, now: datetime):
    """Return ('UPCOMING', dt) / ('TBD', None) / ('ON_SALE', None)."""
    pub = ev.get("sales", {}).get("public", {})
    if pub.get("startTBD"):
        return "TBD", None
    start = pub.get("startDateTime")
    if start:
        dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        if dt > now:
            return "UPCOMING", dt
    return "ON_SALE", None


def parse_event(ev: dict, venue_name: str, city: str, now: datetime):
    """Turn one API event into a digest row, or None if already on sale."""
    code = ev.get("dates", {}).get("status", {}).get("code", "")
    if code in ("cancelled", "canceled", "postponed"):
        return None
    status, dt = sale_status(ev, now)
    if status == "ON_SALE":
        return None

    attractions = ev.get("_embedded", {}).get("attractions", [])
    names = [a.get("name", "") for a in attractions if a.get("name")]
    if status == "UPCOMING":
        local = dt.astimezone(PACIFIC)
        on_sale = local.strftime("On sale %a %b %-d, %-I:%M %p PT")
    else:
        on_sale = "On-sale date not announced yet"

    return {
        "city": city,
        "artist": ", ".join(names) or ev.get("name", ""),
        "title": ev.get("name", ""),
        "venue": venue_name,
        "date_str": ev.get("dates", {}).get("start", {}).get("localDate", ""),
        "on_sale_text": on_sale,
        "sort_key": dt.isoformat() if dt else "9999",
        "ticket_url": ev.get("url", ""),
        "source": "Ticketmaster",
    }


def announced_not_on_sale(venues_by_city: dict, now: datetime = None):
    """
    venues_by_city: {"los_angeles": [("The Wiltern", "CA"), ...], ...}
    Returns (rows, notes). notes is a list of (label, status, detail) so the
    page can show what worked and what didn't.
    """
    now = now or datetime.now(timezone.utc)
    rows, notes = [], []

    if not TICKETMASTER_API_KEY:
        notes.append(("Ticketmaster", "skipped", "no TICKETMASTER_API_KEY set"))
        return rows, notes

    end = (now + timedelta(days=TM_LOOKAHEAD_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    start = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    for city, venues in venues_by_city.items():
        for name, state in venues:
            label = f"Ticketmaster / {name}"
            try:
                vid, official = find_venue_id(name, state)
                if not vid:
                    notes.append((label, "empty", "venue not found on Ticketmaster"))
                    continue
                params = {
                    "venueId": vid, "size": 50, "sort": "date,asc",
                    "startDateTime": start, "endDateTime": end,
                }
                if CLASSIFICATION:
                    params["classificationName"] = CLASSIFICATION
                data = _get("events.json", params)
                events = data.get("_embedded", {}).get("events", [])
                found = [r for r in (parse_event(e, official, city, now) for e in events) if r]
                rows.extend(found)
                notes.append((label, "ok",
                              f"{len(events)} upcoming, {len(found)} not on sale yet"))
            except Exception as e:
                notes.append((label, "error", str(e)[:120]))

    rows.sort(key=lambda r: (r["sort_key"], r["date_str"]))
    return rows, notes
