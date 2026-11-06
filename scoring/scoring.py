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

_token_failed = [False]
SPOTIFY_ERRORS = []   # first few error messages, shown in Source health


def get_spotify_token():
    global _spotify_token
    if _spotify_token:
        return _spotify_token
    if _token_failed[0]:
        return None
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None
    try:
        resp = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
            timeout=10,
        )
        _spotify_token = resp.json().get("access_token") if resp.status_code == 200 else None
        if not _spotify_token:
            _token_failed[0] = True
            SPOTIFY_ERRORS.append(f"token {resp.status_code}: {resp.text[:120]}")
        return _spotify_token
    except Exception as e:
        print(f"[Spotify] Token error: {e}")
        return None


def _from_memory(artist_name, fresh_only):
    from scoring import memory
    f = memory.get(artist_name, "spotify_followers", fresh_only)
    if f is None:
        return None
    url, img = memory.get(artist_name, "spotify_url", False), memory.get(artist_name, "image", False)
    if url:
        _spotify_urls[artist_name] = url
    if img:
        _images[artist_name] = img
    return f


def get_spotify_listeners(artist_name: str) -> int:
    """Followers from the shared Spotify lookup (one call per artist, remembered between runs)."""
    from scoring.spotify import lookup
    res = lookup(artist_name)
    if not res:
        return 0
    if res.get("url"):
        _spotify_urls[artist_name] = res["url"]
    if res.get("image"):
        _images[artist_name] = res["image"]
    return res.get("followers", 0) or 0


def get_spotify_monthly_listeners(artist_name: str) -> int:
    """
    Scrape monthly listeners from Spotify artist page.
    Falls back to follower count from API if scrape fails.
    """
    cache_key = f"spotify_ml_{artist_name}"
    if cache_key in _cache:
        return _cache[cache_key]

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
        from digest.artist_links import artist_name
        artist = artist_name(ev)
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


def spotify_selftest():
    """One known artist, end to end. Returns (status, detail) for the Source health table."""
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return ("error", "SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET are empty in this run: check the secret names "
                         "and that radar.yml passes them under env:")
    tok = get_spotify_token()
    if not tok:
        return ("error", "could not get a token. " + "; ".join(SPOTIFY_ERRORS[:1]) +
                " (invalid_client = wrong ID/secret pair)")
    try:
        r = requests.get("https://api.spotify.com/v1/search", headers={"Authorization": f"Bearer {tok}"},
                         params={"q": 'artist:"Peggy Gou"', "type": "artist", "market": "US", "limit": 10}, timeout=10)
        if r.status_code != 200:
            return ("error", f"search refused: {r.status_code} {r.text[:140]}")
        items = r.json().get("artists", {}).get("items", [])
        hit = next((i for i in items if i.get("name", "").lower() == "peggy gou"), None)
        if not hit:
            return ("empty", f"token ok, search ok, but test artist not found ({len(items)} results)")
        return ("ok", f"token ok · search ok · test artist found · genres: {'yes' if hit.get('genres') else 'EMPTY'} "
                      f"· photo: {'yes' if hit.get('images') else 'none'} · link: {'yes' if hit.get('external_urls') else 'none'}")
    except Exception as e:
        return ("error", f"search failed: {e}")
