"""
la_sources.py
Rebuilt readers for RA, DICE, Shotgun and SceneStar (Los Angeles only).
Written against pages saved from a real browser on Nov 4, 2026:
  RA        __NEXT_DATA__ -> apolloState holds Event/Venue/Artist records
  DICE      __NEXT_DATA__ -> pageProps.events (status, sale dates, venue, price)
  Shotgun   event cards with the day heading above them, genre tags on each card
  SceneStar the weekly concert calendar (all genres, so only house-hosting rooms are kept)
Pages are opened in a headless browser first (they fill in with JavaScript); a plain
download is the fallback. Each parser takes HTML text so it can be tested offline.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.scrapers import HEADERS, normalize_event, is_house
from scrapers.venues import MONTHS, _fmt

RA_URL = "https://ra.co/events/us/losangeles"
DICE_URLS = [
    "https://dice.fm/browse/losangeles-5982e13c613de866017c3e3a/music/dj",
    "https://dice.fm/browse/losangeles-5982e13c613de866017c3e3a/music/party",
]
SHOTGUN_URL = "https://shotgun.live/en/cities/los-angeles"
SCENESTAR_URL = "https://thescenestar.com/los-angeles-show-list-by-the-scenestar/"

DICE_ANNOUNCED = []   # announced-not-on-sale shows found on DICE, read by main.py
LAST = {}             # source -> (count, error) for the health table


def fetch_html(url, scrolls=0):
    """Headless browser first, plain download second."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            page = b.new_page(user_agent=HEADERS["User-Agent"])
            page.goto(url, wait_until="domcontentloaded", timeout=40000)
            page.wait_for_timeout(3000)
            for _ in range(scrolls):
                page.mouse.wheel(0, 6000)
                page.wait_for_timeout(1200)
            html = page.content()
            b.close()
            if len(html) > 20000:
                return html
    except Exception as e:
        print(f"    browser fetch failed for {url}: {e}")
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    return r.text


def _next_data(html):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    return json.loads(m.group(1)) if m else {}


# --- RA --------------------------------------------------------------
def parse_ra(html, city="los_angeles"):
    ap = _next_data(html).get("props", {}).get("apolloState", {})
    ref = lambda r: ap.get(r.get("__ref", ""), {}) if isinstance(r, dict) else {}
    out = []
    for key, ev in ap.items():
        if not key.startswith("Event:") or not ev.get("title"):
            continue
        d = re.match(r"(\d{4})-(\d{2})-(\d{2})", ev.get("date", ""))
        if not d:
            continue
        artists = [ref(a).get("name", "") for a in ev.get("artists", [])]
        artists = [a for a in artists if a]
        venue = ref(ev.get("venue", {})).get("name", "")
        out.append(normalize_event(
            title=ev["title"], artist=", ".join(artists) or ev["title"], venue=venue, city=city,
            date_str=_fmt(int(d.group(2)), int(d.group(3)), int(d.group(1))), genres=[],
            ticket_url="https://ra.co" + ev.get("contentUrl", ""), price="", source="RA"))
    return out


# --- DICE ------------------------------------------------------------
def parse_dice(html, city="los_angeles"):
    """Returns (events, announced). Announced = a sale start date still in the future."""
    now = datetime.now(timezone.utc)
    events, announced = [], []
    for e in _next_data(html).get("props", {}).get("pageProps", {}).get("events") or []:
        dt = e.get("dates", {})
        start = re.match(r"(\d{4})-(\d{2})-(\d{2})", dt.get("event_start_date") or "")
        if not start:
            continue
        v0 = (e.get("venues") or [{}])[0]
        venue, address = v0.get("name", ""), v0.get("address", "")
        url = f"https://dice.fm/event/{e['id']}"
        pr = e.get("price") or {}
        amt = pr.get("amount") or pr.get("amount_from")
        price = f"${amt / 100:,.2f}" if isinstance(amt, (int, float)) and amt else ""
        date_str = _fmt(int(start.group(2)), int(start.group(3)), int(start.group(1)))
        ev = normalize_event(title=e["name"], artist=e["name"], venue=venue, city=city,
                             date_str=date_str, genres=[], ticket_url=url, price=price, source="DICE")
        ev["address"] = address
        sale = dt.get("sale_start_date") or dt.get("pre_sale_start_date")
        try:
            when = datetime.fromisoformat(sale) if sale else None
        except ValueError:
            when = None
        if when and when > now:
            announced.append({"city": city, "artist": e["name"], "title": e["name"], "venue": venue,
                              "date_str": date_str, "ticket_url": url, "source": "DICE",
                              "on_sale_text": "On sale " + when.astimezone().strftime("%a %b %-d, %-I:%M %p"),
                              "sort_key": when.isoformat()})
        elif e.get("status") in ("on-sale", "sold-out", None):
            ev["ticket_status"] = "sold out" if e.get("status") == "sold-out" else "on sale"
            events.append(ev)
    return events, announced


# --- Shotgun ---------------------------------------------------------
_SG_DAY = re.compile(r"^[A-Za-z]{3}\s+(\d{1,2})\s+([A-Za-z]{3})$")


def parse_shotgun(html, city="los_angeles"):
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for a in soup.select('a[href*="/events/"]'):
        h2 = a.find_previous("h2")
        m = _SG_DAY.match(h2.get_text(strip=True)) if h2 else None
        t = list(a.stripped_strings)
        if not m or len(t) < 4:
            continue
        mon = MONTHS.get(m.group(2).lower())
        pi = next((i for i, x in enumerate(t) if x.startswith("$") or x.lower() == "free"), None)
        genres = [x.lower() for x in (t[pi + 1:] if pi is not None else []) if re.search("[a-z]", x.lower()) and x != "+"]
        if not mon or not is_house(genres):
            continue
        out.append(normalize_event(
            title=t[0], artist=t[0], venue=t[1], city=city,
            date_str=_fmt(mon, int(m.group(1))), genres=genres, ticket_url=a["href"],
            price=t[pi] if pi is not None else "", source="Shotgun"))
    return out


# --- SceneStar -------------------------------------------------------
_SS_DATE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{2})$")
HOUSE_HINTS = ("house", "disco", "rave", "afterhours", "warehouse")
# SceneStar lists every genre, so only rooms that mostly book house are kept by name.
HOUSE_ROOMS = ["sound nightclub", "the spotlight", "jungle", "reframe", "origin", "kiss kiss bang bang",
               "golden hour", "level 8", "union station", "rose room", "dream", "exchange", "avalon",
               "academy", "city market", "optimist", "hotel ziggy", "lure", "space 15", "catch one"]


def parse_scenestar(html, city="los_angeles"):
    """Keeps only shows at house-hosting rooms (or with a house hint in the name)."""
    rooms = HOUSE_ROOMS
    soup = BeautifulSoup(html, "html.parser")
    L = [l.strip() for l in (soup.select_one("main, article, .entry-content") or soup.body).get_text("\n").splitlines() if l.strip()]
    out = []
    for i, line in enumerate(L):
        m = _SS_DATE.match(line)
        if not m or i + 2 >= len(L) or not L[i + 2].lower().startswith("at "):
            continue
        title, at = L[i + 1], L[i + 2][3:]
        venue = re.sub(r"\s*\(.*$", "", at).strip()
        if not (any(r in venue.lower() or r in title.lower() for r in rooms)
                or any(h in title.lower() for h in HOUSE_HINTS)):
            continue
        out.append(normalize_event(
            title=title, artist=re.split(r"\s+w/\s+", title)[0], venue=venue, city=city,
            date_str=_fmt(int(m.group(1)), int(m.group(2)), 2000 + int(m.group(3))), genres=[],
            ticket_url=SCENESTAR_URL, price="", source="SceneStar"))
    return out


# --- Heard (getheard.live) -------------------------------------------
# Heard's robots.txt allows all crawlers. One request per run, no backend or API calls.
HEARD_URL = "https://getheard.live/"
HEARD_GENRE_WORDS = ("house", "disco", "balearic", "italo", "garage", "techno", "electro")


def parse_heard(html, city="los_angeles"):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    soup = BeautifulSoup(html, "html.parser")
    today = datetime.now(ZoneInfo("America/Los_Angeles"))
    date_str = _fmt(today.month, today.day)
    out = []
    for card in soup.select("div.v-card"):
        a = card.select_one("a.v-link")
        if not a:
            continue
        venue = a.get_text(strip=True)
        hood = (card.select_one(".v-hood") or a).get_text(strip=True)
        time_ = (card.select_one(".v-time") or a).get_text(strip=True)
        for s in card.select(".v-set"):
            title = (s.select_one(".v-set-title") or s).get_text(strip=True)
            acts = [p.get_text(strip=True) for p in s.select(".v-performer-link")]
            meta = s.select_one(".v-set-meta")
            genre = ""
            if meta:
                t = meta.get_text(" ", strip=True)
                genre = t.split("Genre:", 1)[1].strip() if "Genre:" in t else ""
            if not any(w in genre.lower() or w in title.lower() for w in HEARD_GENRE_WORDS):
                continue
            toks = [g.strip().lower() for g in genre.split(",")]
            if ("hip hop" in toks or "jazz" in toks) and not any(t in ("house", "deep house", "tech house") for t in toks):
                continue
            out.append(normalize_event(
                title=f"{title} ({time_})", artist=acts[0] if acts else title, venue=venue, city=city,
                date_str=date_str, genres=[g.strip() for g in genre.split(",") if g.strip()],
                ticket_url=a.get("href") or HEARD_URL, price="", source="Heard"))
    return out


def scrape_heard(city):
    return _run("Heard", lambda: parse_heard(fetch_html(HEARD_URL), city)) if city == "los_angeles" else []


# --- registered scrapers (names match config.SOURCES) -----------------
def _run(name, fn):
    try:
        found = fn()
        LAST[name] = (len(found), "")
        return found
    except Exception as e:
        LAST[name] = (0, str(e)[:100])
        return []


def scrape_ra(city):
    return _run("RA", lambda: parse_ra(fetch_html(RA_URL), city)) if city == "los_angeles" else []


def scrape_dice(city):
    def go():
        evs = []
        for u in DICE_URLS:
            e, ann = parse_dice(fetch_html(u, scrolls=3), city)
            evs += e
            DICE_ANNOUNCED.extend(ann)
        return evs
    return _run("DICE", go) if city == "los_angeles" else []


def scrape_shotgun(city):
    return _run("Shotgun", lambda: parse_shotgun(fetch_html(SHOTGUN_URL, scrolls=4), city)) if city == "los_angeles" else []


def scrape_scenestar(city):
    return _run("SceneStar", lambda: parse_scenestar(fetch_html(SCENESTAR_URL), city)) if city == "los_angeles" else []
