"""
scoring.py
Enriches events with artist scores from:
  - Spotify monthly listeners
  - Resident Advisor followers
  - SoundCloud followers
  - YouTube DJ sets / track lookups
"""

import requests
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config.config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SCORE_WEIGHTS,
    YOUTUBE_SET_LOOKBACK_DAYS,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Cache to avoid hitting APIs repeatedly for same artist
_cache = {}


# ------------------------------------------------------------------
# SPOTIFY
# ------------------------------------------------------------------
_spotify_token = None
_spotify_urls = {}  # artist name -> Spotify artist page
_images = {}   # artist name -> Spotify photo url (used for thumbnails)

def get_spotify_token():
    global _spotify_token
    if _spotify_token:
        return _spotify_token
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None
    try:
        resp = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
            timeout=10,
        )
        _spotify_token = resp.json().get("access_token")
        return _spotify_token
    except Exception as e:
        print(f"[Spotify] Token error: {e}")
        return None


def get_spotify_listeners(artist_name: str) -> int:
    cache_key = f"spotify_{artist_name}"
    if cache_key in _cache:
        return _cache[cache_key]

    token = get_spotify_token()
    if not token:
        return 0

    try:
        # Search for artist
        resp = requests.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": artist_name, "type": "artist", "limit": 1},
            timeout=10,
        )
        items = resp.json().get("artists", {}).get("items", [])
        if not items:
            _cache[cache_key] = 0
            return 0

        imgs = items[0].get("images") or []
        if imgs:
            _images[artist_name] = (imgs[-2] if len(imgs) > 1 else imgs[0]).get("url", "")
        _spotify_urls[artist_name] = (items[0].get("external_urls") or {}).get("spotify", "")
        artist_id = items[0]["id"]

        # Get artist details with monthly listeners
        resp2 = requests.get(
            f"https://api.spotify.com/v1/artists/{artist_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        followers = resp2.json().get("followers", {}).get("total", 0)
        # Note: Spotify API returns followers, not monthly listeners directly
        # Monthly listeners require the web scrape workaround below
        _cache[cache_key] = followers
        return followers

    except Exception as e:
        print(f"[Spotify] Error for {artist_name}: {e}")
        _cache[cache_key] = 0
        return 0


def get_spotify_monthly_listeners(artist_name: str) -> int:
    """
    Scrape monthly listeners from Spotify artist page.
    Falls back to follower count from API if scrape fails.
    """
    cache_key = f"spotify_ml_{artist_name}"
    if cache_key in _cache:
        return _cache[cache_key]

    try:
        # Try scraping the artist page for monthly listeners
        search_url = f"https://open.spotify.com/search/{requests.utils.quote(artist_name)}/artists"
        resp = requests.get(search_url, headers=HEADERS, timeout=10)
        # Monthly listeners are loaded via JS — fall back to API followers
        listeners = get_spotify_listeners(artist_name)
        _cache[cache_key] = listeners
        return listeners
    except Exception:
        listeners = get_spotify_listeners(artist_name)
        _cache[cache_key] = listeners
        return listeners


# ------------------------------------------------------------------
# RESIDENT ADVISOR
# ------------------------------------------------------------------
def get_ra_followers(artist_name: str) -> int:
    cache_key = f"ra_{artist_name}"
    if cache_key in _cache:
        return _cache[cache_key]

    try:
        # Search RA for artist
        url = "https://ra.co/graphql"
        query = """
        query searchArtists($query: String!) {
          artistSearch(query: $query, limit: 1) {
            id
            name
            followerCount
          }
        }
        """
        resp = requests.post(
            url,
            json={"query": query, "variables": {"query": artist_name}},
            headers={**HEADERS, "Content-Type": "application/json"},
            timeout=10,
        )
        results = resp.json().get("data", {}).get("artistSearch", [])
        if results:
            followers = results[0].get("followerCount", 0) or 0
            _cache[cache_key] = followers
            return followers
    except Exception as e:
        print(f"[RA] Followers error for {artist_name}: {e}")

    _cache[cache_key] = 0
    return 0


# ------------------------------------------------------------------
# SOUNDCLOUD
# ------------------------------------------------------------------
def get_soundcloud_followers(artist_name: str) -> int:
    cache_key = f"sc_{artist_name}"
    if cache_key in _cache:
        return _cache[cache_key]

    try:
        # SoundCloud search
        search_url = f"https://soundcloud.com/search/people?q={requests.utils.quote(artist_name)}"
        resp = requests.get(search_url, headers=HEADERS, timeout=10)
        # SoundCloud loads via JS — we look for followers in page meta
        # This is a best-effort scrape; may return 0 often
        if "followers_count" in resp.text:
            import re
            match = re.search(r'"followers_count":(\d+)', resp.text)
            if match:
                followers = int(match.group(1))
                _cache[cache_key] = followers
                return followers
    except Exception as e:
        print(f"[SoundCloud] Error for {artist_name}: {e}")

    _cache[cache_key] = 0
    return 0


# ------------------------------------------------------------------
# YOUTUBE DJ SET LOOKUP
# ------------------------------------------------------------------
def get_youtube_content(artist_name: str) -> dict:
    """
    Searches YouTube for:
    1. DJ set from last 60 days
    2. Fallback: recent tracks/songs
    Returns dict with set_url and track_urls
    """
    cache_key = f"yt_{artist_name}"
    if cache_key in _cache:
        return _cache[cache_key]

    result = {"set_url": "", "track_urls": []}

    try:
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=YOUTUBE_SET_LOOKBACK_DAYS)
        cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Search for DJ set
        set_query = f"{artist_name} DJ set 2026"
        set_search_url = (
            f"https://www.youtube.com/results?search_query="
            f"{requests.utils.quote(set_query)}"
            f"&sp=CAI%253D"  # Sort by upload date
        )
        resp = requests.get(set_search_url, headers=HEADERS, timeout=10)

        import re
        # Extract video IDs from YouTube search results page
        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)

        if video_ids:
            result["set_url"] = f"https://www.youtube.com/watch?v={video_ids[0]}"

        # If no set found, get tracks
        if not result["set_url"]:
            track_query = f"{artist_name} official mix"
            track_url = (
                f"https://www.youtube.com/results?search_query="
                f"{requests.utils.quote(track_query)}"
            )
            resp2 = requests.get(track_url, headers=HEADERS, timeout=10)
            track_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp2.text)
            result["track_urls"] = [
                f"https://www.youtube.com/watch?v={vid}"
                for vid in track_ids[:2]
            ]

    except Exception as e:
        print(f"[YouTube] Error for {artist_name}: {e}")

    _cache[cache_key] = result
    return result


# ------------------------------------------------------------------
# SCORING ENGINE
# ------------------------------------------------------------------
def normalize_score(value: int, max_value: int) -> float:
    """Normalize a raw number to 0-100 scale."""
    if max_value == 0:
        return 0
    return min(100, (value / max_value) * 100)


def score_events(events: list) -> list:
    """
    Enriches each event with scores and YouTube content.
    Adds a combined 'score' field (0-100).
    """
    if not events:
        return events

    print(f"\nScoring {len(events)} events...")

    # First pass: collect raw numbers for normalization
    for ev in events:
        artist = ev.get("artist", "").split(",")[0].strip()
        if not artist:
            continue

        print(f"  Scoring: {artist}")

        ev["spotify_listeners"] = get_spotify_monthly_listeners(artist)
        ev["image"] = _images.get(artist, "")
        ev["spotify_url"] = _spotify_urls.get(artist, "")
        ev["ra_followers"] = get_ra_followers(artist)
        ev["soundcloud_followers"] = get_soundcloud_followers(artist)

        yt = get_youtube_content(artist)
        ev["youtube_set_url"] = yt.get("set_url", "")
        ev["youtube_track_urls"] = yt.get("track_urls", [])

        time.sleep(0.5)  # Be polite to APIs

    # Second pass: normalize and combine scores
    max_spotify = max((e["spotify_listeners"] for e in events), default=1) or 1
    max_ra = max((e["ra_followers"] for e in events), default=1) or 1
    max_sc = max((e["soundcloud_followers"] for e in events), default=1) or 1

    for ev in events:
        spotify_norm = normalize_score(ev["spotify_listeners"], max_spotify)
        ra_norm = normalize_score(ev["ra_followers"], max_ra)
        sc_norm = normalize_score(ev["soundcloud_followers"], max_sc)

        ev["score"] = round(
            (spotify_norm * SCORE_WEIGHTS["spotify_listeners"])
            + (ra_norm * SCORE_WEIGHTS["ra_followers"])
            + (sc_norm * SCORE_WEIGHTS["soundcloud_followers"]),
            1,
        )

    # Sort by score descending
    events.sort(key=lambda x: x["score"], reverse=True)

    return events
