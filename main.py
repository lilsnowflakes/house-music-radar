#!/usr/bin/env python3
"""
main.py — House Music Radar

  python main.py               full run (scrape, score, write site, send email)
  python main.py --no-email    same, but do not send the email
  python main.py --no-score    skip the slow artist scoring (quick test)
  python main.py --demo        offline demo with made-up shows (no network)
"""

import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import (
    CITIES, SOURCES, SONGKICK_API_KEY, WATCH_VENUES, WATCH_PROMOTERS,
    TICKETMASTER_VENUES, SITE_URL, WATCH_ARTISTS,
)
from scrapers.scrapers import SCRAPER_MAP
from scrapers import ticketmaster, venues, la_sources
import re
from scoring.scoring import score_events
from scoring import genre_check
from digest import render, list_page
from digest.email_builder import send_html

SCRAPER_MAP["venue_calendars"] = venues.scrape_venue_calendars
# Rebuilt Los Angeles readers replace the old guessed ones.
SCRAPER_MAP["resident_advisor"] = la_sources.scrape_ra
SCRAPER_MAP["dice"] = la_sources.scrape_dice
SCRAPER_MAP["shotgun"] = la_sources.scrape_shotgun
SCRAPER_MAP["scenestar"] = la_sources.scrape_scenestar
SCRAPER_MAP["heard"] = la_sources.scrape_heard

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")


def day_key(date_str):
    """'Fri: Nov 6 (9pm-2am)' and 'Fri Nov 6' both become 'nov6', so the same
    show from two sources is counted once."""
    m = re.search(r"([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2})", re.sub(r"^[A-Za-z]{3,9}:?\s", "", date_str))
    return (m.group(1).lower() + m.group(2)) if m else date_str


def collect(cities, sources_map):
    """Run every scraper. Returns (events, health) — health lists what worked."""
    events, health = [], []
    for city in cities:
        for source in sources_map.get(city, []):
            label = f"{source} / {city}"
            if source == "songkick" and not SONGKICK_API_KEY:
                health.append((label, "skipped", "no SONGKICK_API_KEY set"))
                continue
            fn = SCRAPER_MAP.get(source)
            if not fn:
                health.append((label, "skipped", "no scraper"))
                continue
            try:
                found = fn(city)
            except Exception as e:  # scrapers should catch their own, but just in case
                health.append((label, "error", str(e)[:120]))
                continue
            if found:
                health.append((label, "ok", f"{len(found)} house events"))
            else:
                health.append((label, "empty",
                               "0 events (blocked, layout changed, or none listed)"))
            events.extend(found)

    for name, (n, err) in la_sources.LAST.items():
        if err:
            health.append((f"{name} / los_angeles detail", "error", err))
    for venue, (n, err) in venues.LAST.items():
        health.append((f"venue calendar / {venue}", "ok" if n else ("error" if err else "empty"),
                       f"{n} shows" if n else (err or "0 shows (page layout changed or blocked)")))

    seen, deduped = set(), []
    for ev in events:
        key = (re.sub(r"[^a-z0-9]", "", ev["artist"].lower())[:18], day_key(ev["date_str"]))
        if key not in seen:
            seen.add(key)
            deduped.append(ev)
    return deduped, health


def tag_watched(events):
    for ev in events:
        text = " ".join([ev.get("venue", ""), ev.get("title", ""),
                         ev.get("artist", "")]).lower()
        names = WATCH_VENUES.get(ev.get("city", ""), []) + WATCH_PROMOTERS + WATCH_ARTISTS
        ev["watched"] = any(n.lower() in text for n in names)


def demo_data():
    base = dict(title="", genres=["house"], ticket_url="https://example.com",
                price="", source="Demo", spotify_listeners=0, ra_followers=0,
                soundcloud_followers=0, youtube_set_url="", youtube_track_urls=[])
    events = [
        dict(base, artist="DEMO Artist A", venue="Sound Nightclub", city="los_angeles",
             date_str="Fri Nov 13", score=82, watched=True),
        dict(base, artist="DEMO Artist B", venue="Some Other Club", city="los_angeles",
             date_str="Sat Nov 14", score=41, watched=False),
        dict(base, artist="DEMO Artist C", venue="Origin", city="los_angeles",
             date_str="Fri Nov 20", score=55, watched=True),
    ]
    announced = [dict(city="los_angeles", artist="DEMO Headliner", title="", venue="The Wiltern",
                      date_str="2027-02-12", on_sale_text="On sale Fri Nov 6, 10:00 AM PT",
                      ticket_url="https://example.com", source="Ticketmaster", sort_key="x")]
    health = [("demo / source", "ok", "fake data"), ("demo / blocked", "empty", "example of a miss")]
    return events, announced, health


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-email", action="store_true")
    ap.add_argument("--no-score", action="store_true")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()

    if args.demo:
        events, announced, health = demo_data()
    else:
        print("Scraping event sources...")
        events, health = collect(CITIES, SOURCES)
        print(f"  {len(events)} house events after de-duplication")
        tag_watched(events)

        print("Verifying genres for venue-calendar shows...")
        events, dropped = genre_check.filter_venue_events(events)
        n_unv = sum(1 for e in events if e.get("house_check", {}).get("verdict") == "unverified")
        n_ok = sum(1 for e in events if e.get("house_check", {}).get("verdict") == "house")
        names = ", ".join(f"{e['artist']} ({'/'.join(e['house_check']['genres'][:2])})" for e in dropped[:12])
        health.append(("house check", "ok",
                       f"{n_ok} confirmed house, {n_unv} unverified (kept, marked ?), "
                       f"{len(dropped)} dropped as not house" + (f": {names}" if names else "")))

        if not args.no_score and events:
            events = score_events(events)
        events.sort(key=lambda e: e.get("score", 0), reverse=True)

        print("Checking Ticketmaster for announced-not-on-sale shows...")
        announced, tm_notes = ticketmaster.announced_not_on_sale(TICKETMASTER_VENUES)
        health.extend(tm_notes)
        announced = sorted(announced + la_sources.DICE_ANNOUNCED, key=lambda r: r.get('sort_key', ''))

    page = render.build_page(events, announced, health,
                             site_url=SITE_URL, demo=args.demo)

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Wrote {OUT_DIR}/index.html")
    with open(os.path.join(OUT_DIR, "list.html"), "w", encoding="utf-8") as f:
        f.write(list_page.build_list_page(events))
    print(f"Wrote {OUT_DIR}/list.html")

    if args.demo or args.no_email:
        print("Email skipped.")
        return
    subject = (f"🎛 House Music Radar — {datetime.now().strftime('%b %-d')} "
               f"({len(announced)} announced, {sum(1 for e in events if e.get('watched'))} at your spots)")
    send_html(subject, page)


if __name__ == "__main__":
    main()
