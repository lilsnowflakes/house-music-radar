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
    ("HOUSE·LA", "https://www.housemusicla.com/", "2026-11-05: Allow / (the event rows are on the home page)"),
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


# ---------------------------------------------------------------------------
# HOUSE·LA (housemusicla.com/events/): server-rendered rows, read with a plain download (no browser needed).
#   <a class="row-ev" href=".../events/adriatique-2026-11-07"><span class="date">11.07 <small>SAT</small></span>
#    <span class="what"><h3>Adriatique</h3><p>Reframe Studios · Atwater Village · 6 PM to 12 AM</p></span>
#    <span class="price">$79+</span></a>
# Rows marked "geo-off" are outside LA (San Diego, Palm Springs...) and are skipped.
# Weekly rows ("WEDS WEEKLY") become the next two dates; "DAILY ALL WEEK" becomes tonight and tomorrow.
# ---------------------------------------------------------------------------
_DOW = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def _fix_time(t):
    """'3 to 9 PM' -> '3 PM to 9 PM' so the start time isn't read as 9 PM."""
    return re.sub(r"(?i)\b(\d{1,2}(?::\d{2})?)\s+to\s+(\d{1,2}(?::\d{2})?)\s*(AM|PM)\b", r"\1 \3 to \2 \3", t or "")


def parse_house_la(html, city="los_angeles", today=None):
    from bs4 import BeautifulSoup
    from datetime import timedelta
    today = today or datetime.now()
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for a in soup.select("a.row-ev"):
        if "geo-off" in (a.get("class") or []):
            continue
        h3, p, pr, dt = a.select_one("h3"), a.select_one(".what p"), a.select_one(".price"), a.select_one(".date")
        if not h3 or not dt:
            continue
        title = h3.get_text(" ", strip=True)
        parts = [x.strip() for x in (p.get_text(" ", strip=True) if p else "").split("·")]
        venue, hood, detail = (parts + ["", "", ""])[:3]
        date_txt = dt.get_text(" ", strip=True)
        price = pr.get_text(" ", strip=True) if pr else ""
        url = a.get("href", "")
        dates, recurring = [], ""
        m = re.match(r"(\d{2})\.(\d{2})", date_txt)
        if m:
            ys = re.search(r"(\d{4})-(\d{2})-(\d{2})$", url.rstrip("/"))
            y = int(ys.group(1)) if ys else today.year + (1 if int(m.group(1)) < today.month - 1 else 0)
            try:
                dates = [datetime(y, int(m.group(1)), int(m.group(2)))]
            except ValueError:
                continue
        elif "weekly" in date_txt.lower():
            k = _DOW.get(date_txt.lower()[:3])
            if k is None:
                continue
            first = today + timedelta(days=(k - today.weekday()) % 7)
            dates, recurring = [first, first + timedelta(days=7)], "Weekly"
        elif "daily" in date_txt.lower():
            dates, recurring = [today, today + timedelta(days=1)], "Daily"
        for d in dates:
            ev = normalize_event(title=title, artist=title, venue=venue, city=city, date_str=_fmt(d), genres=["house"],
                                 ticket_url=url, price="" if price.lower() in ("on sale", "at venue") else price,
                                 source="HOUSE·LA")
            ev["time_text"] = _fix_time(detail)
            if "21+" in detail:
                ev["age"] = "21+"
            if pr and "soldout" in (pr.get("class") or []):
                ev["ticket_status"] = "sold out"
            if hood:
                ev["neighborhood"] = hood
            if recurring:
                ev["recurring"] = recurring
            out.append(ev)
    return out


def scrape_calendars(city):
    if city != "los_angeles":
        return []
    found = []
    for name, url, _robots in CALENDARS:
        try:
            if name == "HOUSE·LA":
                # fast path: the page is plain HTML, a normal download is enough (no browser start-up)
                import requests
                r = requests.get(url, timeout=20, headers={"User-Agent": "HouseMusicRadar/1.0 (personal digest)"})
                r.raise_for_status()
                evs = parse_house_la(r.text, city)
                if not evs:   # fall back to the /events/ page, then to the browser
                    r2 = requests.get(url + "events/", timeout=20, headers={"User-Agent": "HouseMusicRadar/1.0 (personal digest)"})
                    evs = parse_house_la(r2.text, city) if r2.status_code == 200 else []
                if not evs:
                    evs = parse_house_la(fetch_html(url, scrolls=1), city)
                LAST[name] = (len(evs), "" if evs else "page read, but no event rows found (layout may have changed)")
                found += evs
                continue
            html = fetch_html(url, scrolls=2)
            evs = parse_jsonld(html, name, city)
            LAST[name] = (len(evs), "" if evs else "page read, but it has no machine-readable events: needs a custom reader")
            found += evs
        except Exception as e:
            LAST[name] = (0, str(e)[:120])
    return found
