"""
venues.py
Reads the venues' own calendars, one venue at a time, for rooms that host house music.
Three page styles, all parsed from the page's visible text:
  discotech   app.discotech.me/<city>/<venue>      (Origin, The Spotlight, ...)
  dice_venue  dice.fm/venue/<slug>                 (Sound Nightclub, ...)
  framework   thisisframework.com/events           (Reframe Studios + other Framework shows)
Each parser takes plain text so it can be tested offline against saved pages.
"""

import re
import sys
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import VENUE_CALENDARS, VENUE_SKIP_WORDS
from scrapers.scrapers import HEADERS, normalize_event

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
DAY = r"(?:Mon|Tues?|Wed(?:nes)?|Thu(?:rs)?|Fri|Sat(?:ur)?|Sun)(?:day)?"


def _lines(text):
    return [l.strip() for l in text.splitlines() if l.strip()]


def _skip(title):
    t = title.lower()
    return any(w in t for w in VENUE_SKIP_WORDS)


def _fmt(month, day, year=None):
    """'Sat Nov 7' style, the format the rest of the digest shows."""
    now = datetime.now()
    y = year or (now.year if (month, day) >= (now.month, now.day) else now.year + 1)
    try:
        d = datetime(y, month, day)
    except ValueError:
        return ""
    return d.strftime("%a %b %-d") + (f", {y}" if y != now.year else "")


# --- Discotech -------------------------------------------------------
_DT_DATE = re.compile(rf"^{DAY},\s+([A-Za-z]+)\s+(\d{{1,2}})$")


def parse_discotech(text, venue, page_url, city):
    out, L = [], _lines(text)
    for i, line in enumerate(L):
        m = _DT_DATE.match(line)
        if not m or i + 1 >= len(L):
            continue
        mon = MONTHS.get(m.group(1)[:3].lower())
        title = L[i + 1]
        if not mon or _skip(title):
            continue
        out.append(normalize_event(
            title=title, artist=title, venue=venue, city=city,
            date_str=_fmt(mon, int(m.group(2))), genres=["house"],
            ticket_url=page_url, price="", source="Discotech"))
    return out


# --- DICE venue page -------------------------------------------------
_DICE_DATE = re.compile(rf"^{DAY},?\s+(\d{{1,2}})\s+([A-Za-z]{{3}})[a-z]*(?:\s+(\d{{4}}))?$")


def parse_dice_venue(text, venue, page_url, city, event_urls=()):
    out, L, n = [], _lines(text), 0
    for i, line in enumerate(L):
        m = _DICE_DATE.match(line)
        if not m or i == 0:
            continue
        title = L[i - 1]
        mon = MONTHS.get(m.group(2).lower())
        price = L[i + 2] if i + 2 < len(L) and L[i + 2].startswith("$") else ""
        url = event_urls[n] if n < len(event_urls) else page_url
        n += 1
        if not mon or _skip(title):
            continue
        out.append(normalize_event(
            title=title, artist=title, venue=venue, city=city,
            date_str=_fmt(mon, int(m.group(1)), int(m.group(3)) if m.group(3) else None),
            genres=["house"], ticket_url=url, price=price, source="DICE venue"))
    return out


# --- Framework -------------------------------------------------------
_FW_DATE = re.compile(r"^(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day,\s+([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)$")


def parse_framework(text, page_url, city_label="Los Angeles"):
    out, L = [], _lines(text)
    for i, line in enumerate(L):
        m = _FW_DATE.match(line)
        if not m or i == 0 or i + 2 >= len(L):
            continue
        mon = MONTHS.get(m.group(1)[:3].lower())
        title, venue = L[i - 1], L[i + 1].rstrip(",")
        if L[i + 2].rstrip(",") != city_label or not mon or _skip(title):
            continue  # Miami / Vegas / passes etc.
        sold = "SOLD OUT" in L[i + 3:i + 5]
        out.append(normalize_event(
            title=title + (" (SOLD OUT)" if sold else ""), artist=title, venue=venue,
            city="los_angeles", date_str=_fmt(mon, int(m.group(2))), genres=["house"],
            ticket_url=page_url, price="", source="Framework"))
    return out


# --- fetching --------------------------------------------------------
def _page_text(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    return soup, soup.get_text("\n")


def rendered_text(url, more_text="Load more", max_clicks=15):
    """Opens the page in a real headless browser, presses every 'Load more' button until
    it is gone, and returns the visible text. Returns None if Playwright is not installed
    or the page fails, so the caller can fall back to a plain download."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            page = b.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2500)
            for _ in range(max_clicks):
                btn = page.get_by_text(re.compile(more_text, re.I)).first
                if btn.count() == 0 or not btn.is_visible():
                    break
                before = len(page.inner_text("body"))
                btn.click()
                page.wait_for_timeout(1200)
                if len(page.inner_text("body")) <= before:
                    break
            text = page.inner_text("body")
            b.close()
            return text
    except Exception as e:
        print(f"    rendered_text failed for {url}: {e}")
        return None


def scrape_venue_calendars(city):
    """Returns events for every calendar in VENUE_CALENDARS for this city.
    Raises nothing: a failed page is recorded in LAST_ERRORS for the health table."""
    events = []
    for cal in VENUE_CALENDARS.get(city, []):
        try:
            soup, text = _page_text(cal["url"])
            if cal["kind"] == "discotech":
                text = rendered_text(cal["url"]) or text  # presses "Load more" so later months show
                found = parse_discotech(text, cal["venue"], cal["url"], city)
            elif cal["kind"] == "dice_venue":
                hrefs, seen = [], set()
                for a in soup.select('a[href*="/event/"]'):
                    h = a["href"].split("?")[0]
                    h = h if h.startswith("http") else "https://dice.fm" + h
                    if h not in seen:
                        seen.add(h); hrefs.append(h)
                found = parse_dice_venue(text, cal["venue"], cal["url"], city, hrefs)
            elif cal["kind"] == "framework":
                found = parse_framework(text, cal["url"])
            else:
                found = []
            print(f"    {cal['venue']}: {len(found)} shows")
            LAST[cal["venue"]] = (len(found), "")
            events.extend(found)
        except Exception as e:
            LAST[cal["venue"]] = (0, str(e)[:100])
    return events


LAST = {}  # venue -> (count, error), read by main.py for the health table
