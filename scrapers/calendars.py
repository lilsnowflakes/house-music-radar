"""
calendars.py - extra event calendars (checked robots.txt before adding each one).

Each site is read once per run. The reader first looks for machine-readable events
(schema.org "Event" JSON-LD, which many event sites publish for Google). A site that
doesn't publish that needs a custom reader, built from a saved copy of its page; until then
it shows in Source health as "needs a custom reader" instead of silently returning nothing.
"""
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.scrapers import normalize_event
from scrapers.la_sources import fetch_html

# name, url, robots.txt checked (date)
CALENDARS = [
    ("HOUSE·LA", "https://www.housemusicla.com/events/", "2026-11-05: Allow /"),
]
LAST = {}


def _fmt(d):
    return d.strftime("%a %b %-d") + ("" if d.year == datetime.now().year else f", {d.year}")


def _walk(x):
    if isinstance(x, list):
        for i in x:
            yield from _walk(i)
    elif isinstance(x, dict):
        t = x.get("@type")
        types = t if isinstance(t, list) else [t]
        if any(str(tt).endswith("Event") for tt in types if tt):
            yield x
        for k in ("@graph", "itemListElement", "item", "subEvent", "event", "events"):
            if k in x:
                yield from _walk(x[k])


def parse_jsonld(html, source, city="los_angeles"):
    out = []
    for block in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html, re.S | re.I):
        try:
            data = json.loads(block.strip())
        except ValueError:
            continue
        for ev in _walk(data):
            start = str(ev.get("startDate", ""))[:10]
            try:
                d = datetime.strptime(start, "%Y-%m-%d")
            except ValueError:
                continue
            loc = ev.get("location") or {}
            loc = loc[0] if isinstance(loc, list) and loc else loc
            venue = loc.get("name", "") if isinstance(loc, dict) else str(loc)
            addr = loc.get("address", "") if isinstance(loc, dict) else ""
            if isinstance(addr, dict):
                addr = ", ".join(str(addr.get(k, "")) for k in ("streetAddress", "addressLocality") if addr.get(k))
            perf = ev.get("performer") or []
            perf = perf if isinstance(perf, list) else [perf]
            names = [p.get("name", "") if isinstance(p, dict) else str(p) for p in perf]
            names = [n for n in names if n]
            offers = ev.get("offers") or {}
            offers = offers[0] if isinstance(offers, list) and offers else offers
            url = (offers.get("url") if isinstance(offers, dict) else "") or ev.get("url", "")
            title = ev.get("name", "")
            e = normalize_event(title=title, artist=names[0] if names else title, venue=venue, city=city,
                                date_str=_fmt(d), genres=[], ticket_url=url, price="", source=source)
            e["address"] = addr
            out.append(e)
    return out


def scrape_calendars(city):
    if city != "los_angeles":
        return []
    found = []
    for name, url, _robots in CALENDARS:
        try:
            html = fetch_html(url, scrolls=2)
            evs = parse_jsonld(html, name, city)
            LAST[name] = (len(evs), "" if evs else "page read, but it has no machine-readable events: needs a custom reader")
            found += evs
        except Exception as e:
            LAST[name] = (0, str(e)[:120])
    return found
