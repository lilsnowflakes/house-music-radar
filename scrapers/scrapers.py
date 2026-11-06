"""
scrapers.py
Pulls upcoming events from all configured sources.
Returns a list of normalized event dicts.
"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config.config import HOUSE_GENRES, DAYS_AHEAD

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

TODAY = datetime.today()
CUTOFF = TODAY + timedelta(days=DAYS_AHEAD)


def is_house(genre_tags: list) -> bool:
    """Returns True if any tag matches our house genre list."""
    if not genre_tags:
        return False
    tags_lower = [t.lower() for t in genre_tags]
    return any(g in tag for tag in tags_lower for g in HOUSE_GENRES)


def normalize_event(
    title, artist, venue, city, date_str, genres,
    ticket_url, price, source, date_obj=None
):
    return {
        "title": title or "",
        "artist": artist or "",
        "venue": venue or "",
        "city": city,
        "date_str": date_str or "",
        "date_obj": date_obj,
        "genres": genres or [],
        "ticket_url": ticket_url or "",
        "price": price or "",
        "source": source,
        "score": 0,
        "spotify_listeners": 0,
        "ra_followers": 0,
        "soundcloud_followers": 0,
        "youtube_set_url": "",
        "youtube_track_urls": [],
    }


# ------------------------------------------------------------------
# RESIDENT ADVISOR
# ------------------------------------------------------------------
RA_CITY_IDS = {
    "los_angeles": 11,
    "phoenix": 61,
}

def scrape_resident_advisor(city: str) -> list:
    events = []
    city_id = RA_CITY_IDS.get(city)
    if not city_id:
        return events

    url = "https://ra.co/graphql"
    query = """
    query GET_EVENTS($filters: FilterInputDtoInput, $page: Int) {
      eventListings(filters: $filters, pageSize: 50, page: $page, ordering: ASCENDING) {
        data {
          id
          event {
            title
            date
            venue { name }
            artists { name }
            genres { name }
            ticketUrl
            cost
          }
        }
      }
    }
    """
    variables = {
        "filters": {
            "areas": {"eq": city_id},
            "listingDate": {
                "gte": TODAY.strftime("%Y-%m-%d"),
                "lte": CUTOFF.strftime("%Y-%m-%d"),
            },
        },
        "page": 1,
    }

    try:
        resp = requests.post(
            url,
            json={"query": query, "variables": variables},
            headers={**HEADERS, "Content-Type": "application/json"},
            timeout=15,
        )
        data = resp.json()
        listings = (
            data.get("data", {})
            .get("eventListings", {})
            .get("data", [])
        )
        for item in listings:
            ev = item.get("event", {})
            genres = [g["name"] for g in ev.get("genres", [])]
            if not is_house(genres):
                continue
            artists = [a["name"] for a in ev.get("artists", [])]
            artist_str = ", ".join(artists)
            events.append(
                normalize_event(
                    title=ev.get("title", ""),
                    artist=artist_str,
                    venue=ev.get("venue", {}).get("name", ""),
                    city=city,
                    date_str=ev.get("date", ""),
                    genres=genres,
                    ticket_url=ev.get("ticketUrl", ""),
                    price=ev.get("cost", ""),
                    source="Resident Advisor",
                )
            )
    except Exception as e:
        print(f"[RA] Error scraping {city}: {e}")

    return events


# ------------------------------------------------------------------
# 19HZ
# ------------------------------------------------------------------
HZ_URLS = {
    "los_angeles": "https://19hz.info/eventlisting_LosAngeles.php",
    "phoenix": "https://19hz.info/eventlisting_Phoenix.php",
}

def scrape_19hz(city: str) -> list:
    events = []
    url = HZ_URLS.get(city)
    if not url:
        return events

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select("table tr")

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 4:
                continue

            date_text = cells[0].get_text(strip=True)
            event_cell = cells[1]
            tags_text = cells[2].get_text(strip=True).lower() if len(cells) > 2 else ""
            price_text = cells[3].get_text(strip=True) if len(cells) > 3 else ""

            genre_tags = [t.strip() for t in tags_text.split(",")]
            if not is_house(genre_tags):
                continue

            link = event_cell.find("a")
            title = link.get_text(strip=True) if link else event_cell.get_text(strip=True)
            ticket_url = link["href"] if link and link.get("href") else ""

            # Parse venue from title (after @)
            venue = ""
            artist = title
            if " @ " in title:
                parts = title.split(" @ ", 1)
                artist = parts[0].strip()
                venue = parts[1].strip()

            events.append(
                normalize_event(
                    title=title,
                    artist=artist,
                    venue=venue,
                    city=city,
                    date_str=date_text,
                    genres=genre_tags,
                    ticket_url=ticket_url,
                    price=price_text,
                    source="19hz",
                )
            )
            # 19hz's price cell reads like "$35+ | 21+" or "$20 | All ages": split the age out
            ev_ = events[-1]
            parts = [p.strip() for p in price_text.split("|")]
            ages = [p for p in parts if re.fullmatch(r"(?i)all ages|\d{2}\+", p)]
            if ages:
                ev_["age"] = "All ages" if ages[0].lower() == "all ages" else ages[0]
                ev_["price"] = " | ".join(p for p in parts if p not in ages)
    except Exception as e:
        print(f"[19hz] Error scraping {city}: {e}")

    return events


# ------------------------------------------------------------------
# DICE
# ------------------------------------------------------------------
DICE_CITY_SLUGS = {
    "los_angeles": "los-angeles",
    "phoenix": "phoenix",
}

def scrape_dice(city: str) -> list:
    events = []
    slug = DICE_CITY_SLUGS.get(city)
    if not slug:
        return events

    url = f"https://dice.fm/api/v1/events?location={slug}&page=1&per_page=50"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        data = resp.json()
        for ev in data.get("payload", {}).get("events", []):
            genres = ev.get("genre_tags", [])
            if not is_house(genres):
                continue
            lineup = ev.get("lineup", [])
            artist_str = ", ".join([a.get("name", "") for a in lineup])
            events.append(
                normalize_event(
                    title=ev.get("name", ""),
                    artist=artist_str,
                    venue=ev.get("venue", {}).get("name", ""),
                    city=city,
                    date_str=ev.get("date", ""),
                    genres=genres,
                    ticket_url=f"https://dice.fm/event/{ev.get('id','')}",
                    price=ev.get("min_price", ""),
                    source="DICE",
                )
            )
    except Exception as e:
        print(f"[DICE] Error scraping {city}: {e}")

    return events


# ------------------------------------------------------------------
# SHOTGUN
# ------------------------------------------------------------------
SHOTGUN_CITY_IDS = {
    "los_angeles": "los-angeles",
    "phoenix": "phoenix",
}

def scrape_shotgun(city: str) -> list:
    events = []
    slug = SHOTGUN_CITY_IDS.get(city)
    if not slug:
        return events

    url = f"https://shotgun.live/en/events/{slug}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("[data-testid='event-card']")

        for card in cards:
            title_el = card.select_one("h3, h2, .event-title")
            title = title_el.get_text(strip=True) if title_el else ""
            venue_el = card.select_one(".venue-name, .location")
            venue = venue_el.get_text(strip=True) if venue_el else ""
            date_el = card.select_one(".event-date, time")
            date_str = date_el.get_text(strip=True) if date_el else ""
            link_el = card.select_one("a")
            ticket_url = "https://shotgun.live" + link_el["href"] if link_el else ""
            genre_el = card.select(".genre-tag, .tag")
            genres = [g.get_text(strip=True).lower() for g in genre_el]

            if not is_house(genres):
                continue

            events.append(
                normalize_event(
                    title=title,
                    artist=title,
                    venue=venue,
                    city=city,
                    date_str=date_str,
                    genres=genres,
                    ticket_url=ticket_url,
                    price="",
                    source="Shotgun",
                )
            )
    except Exception as e:
        print(f"[Shotgun] Error scraping {city}: {e}")

    return events


# ------------------------------------------------------------------
# SCENESTAR (LA only)
# ------------------------------------------------------------------
def scrape_scenestar(city: str) -> list:
    events = []
    if city != "los_angeles":
        return events

    url = "https://www.scenestar.com/los-angeles/events/electronic"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select(".event-item, .event-card, article")

        for card in cards:
            title_el = card.select_one("h2, h3, .title")
            title = title_el.get_text(strip=True) if title_el else ""
            venue_el = card.select_one(".venue, .location")
            venue = venue_el.get_text(strip=True) if venue_el else ""
            date_el = card.select_one(".date, time")
            date_str = date_el.get_text(strip=True) if date_el else ""
            link_el = card.select_one("a")
            ticket_url = link_el["href"] if link_el else ""
            genre_tags = ["house"]  # Scenestar is pre-filtered to electronic

            events.append(
                normalize_event(
                    title=title,
                    artist=title,
                    venue=venue,
                    city=city,
                    date_str=date_str,
                    genres=genre_tags,
                    ticket_url=ticket_url,
                    price="",
                    source="Scenestar",
                )
            )
    except Exception as e:
        print(f"[Scenestar] Error: {e}")

    return events


# ------------------------------------------------------------------
# EDMTRAIN (Phoenix only)
# ------------------------------------------------------------------
def scrape_edmtrain(city: str) -> list:
    events = []
    if city != "phoenix":
        return events

    url = "https://edmtrain.com/api/events?locationId=30&client=website"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        data = resp.json()
        for ev in data.get("data", []):
            genres = [ev.get("genre", "").lower()]
            if not is_house(genres):
                continue
            artists = ev.get("artists", [])
            artist_str = ", ".join([a.get("name", "") for a in artists])
            events.append(
                normalize_event(
                    title=ev.get("name", ""),
                    artist=artist_str,
                    venue=ev.get("venue", {}).get("name", ""),
                    city=city,
                    date_str=ev.get("date", ""),
                    genres=genres,
                    ticket_url=ev.get("link", ""),
                    price="",
                    source="EDMtrain",
                )
            )
    except Exception as e:
        print(f"[EDMtrain] Error: {e}")

    return events


# ------------------------------------------------------------------
# 1001TRACKLISTS
# ------------------------------------------------------------------
def scrape_1001tracklists(city: str) -> list:
    """
    1001Tracklists doesn't have city-based event listings.
    We use it as an artist lookup tool in scoring.py instead.
    Returning empty here — artist enrichment happens in scoring.
    """
    return []


# ------------------------------------------------------------------
# SONGKICK (LA only)
# ------------------------------------------------------------------
SONGKICK_METRO_IDS = {
    "los_angeles": 17835,
}

def scrape_songkick(city: str) -> list:
    events = []
    metro_id = SONGKICK_METRO_IDS.get(city)
    if not metro_id:
        return events

    url = (
        f"https://api.songkick.com/api/3.0/metro_areas/{metro_id}/calendar.json"
        f"?apikey={os.environ.get('SONGKICK_API_KEY','')}"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        data = resp.json()
        results = (
            data.get("resultsPage", {})
            .get("results", {})
            .get("event", [])
        )
        for ev in results:
            # Filter by genre — Songkick has limited genre data
            # so we check title/artist name for house keywords
            title = ev.get("displayName", "")
            if not any(g in title.lower() for g in ["house", "techno", "electronic", "disco"]):
                continue
            performances = ev.get("performance", [])
            artist_str = ", ".join([p.get("displayName", "") for p in performances])
            venue = ev.get("venue", {}).get("displayName", "")
            date_str = ev.get("start", {}).get("date", "")
            ticket_url = ev.get("uri", "")

            events.append(
                normalize_event(
                    title=title,
                    artist=artist_str,
                    venue=venue,
                    city=city,
                    date_str=date_str,
                    genres=["house"],
                    ticket_url=ticket_url,
                    price="",
                    source="Songkick",
                )
            )
    except Exception as e:
        print(f"[Songkick] Error: {e}")

    return events


# ------------------------------------------------------------------
# MASTER SCRAPER
# ------------------------------------------------------------------
SCRAPER_MAP = {
    "resident_advisor": scrape_resident_advisor,
    "19hz": scrape_19hz,
    "dice": scrape_dice,
    "shotgun": scrape_shotgun,
    "scenestar": scrape_scenestar,
    "edmtrain": scrape_edmtrain,
    "1001tracklists": scrape_1001tracklists,
    "songkick": scrape_songkick,
}

def scrape_all(cities: list, sources_map: dict) -> list:
    all_events = []
    for city in cities:
        sources = sources_map.get(city, [])
        for source in sources:
            scraper = SCRAPER_MAP.get(source)
            if scraper:
                print(f"  Scraping {source} / {city}...")
                results = scraper(city)
                print(f"    → {len(results)} house events found")
                all_events.extend(results)

    # Deduplicate by artist + date
    seen = set()
    deduped = []
    for ev in all_events:
        key = (ev["artist"].lower(), ev["date_str"])
        if key not in seen:
            seen.add(key)
            deduped.append(ev)

    return deduped
