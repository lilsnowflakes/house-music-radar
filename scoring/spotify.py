"""
spotify.py - every Spotify lookup goes through here: ONE search call per artist, ever.

The search result already includes the artist's page link, photo, followers and genres, so the
genre check and the scorer share one answer (before this, each artist cost Spotify three calls).
Answers are kept in scoring/memory.py between runs.

Rate limits (Spotify doesn't publish a number; it counts calls in a rolling 30-second window and
answers 429 with a Retry-After header):
  - calls are paced (MIN_GAP seconds apart),
  - a 429 with a short Retry-After is waited out once,
  - a long one stops Spotify calls for the rest of the run; remembered answers are used instead,
    and the next run picks up where this one stopped.
"""
import re
import time
import unicodedata

import requests

MIN_GAP = 1.0           # seconds between calls (at most 30 per 30-second window)
MAX_NEW_PER_RUN = 150   # new artists asked about per run; the memory fills in the rest over the next days
MAX_WAIT = 30           # longest Retry-After we'll sit through
STATE = {"calls": 0, "blocked": False, "retry_after": 0, "blocked_at": 0, "errors": []}
_run = {}               # this run's answers
_last = [0.0]


def _n(s):
    s = "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _get(url, token, params):
    wait = MIN_GAP - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    _last[0] = time.time()
    STATE["calls"] += 1
    return requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=10)


def _remembered(name, fresh_only):
    from scoring import memory
    if memory.get(name, "sp_checked", fresh_only) is None:
        return None
    return {"url": memory.get(name, "spotify_url", False) or "", "image": memory.get(name, "image", False) or "",
            "followers": memory.get(name, "spotify_followers", False) or 0,
            "genres": memory.get(name, "sp_genres", False) or [], "found": bool(memory.get(name, "spotify_url", False))}


def lookup(name):
    """Returns {"url","image","followers","genres","found"} or None if Spotify can't be asked and nothing is remembered."""
    from scoring import memory
    from scoring.scoring import get_spotify_token
    k = _n(name)
    if not k:
        return None
    if k in _run:
        return _run[k]
    fresh = _remembered(name, fresh_only=True)
    if fresh is not None:
        memory.STATS["reused"] += 1
        _run[k] = fresh
        return fresh
    old = _remembered(name, fresh_only=False)
    if STATE["calls"] >= MAX_NEW_PER_RUN and not STATE["blocked"]:
        STATE.update(capped=True)
    token = None if (STATE["blocked"] or STATE.get("capped")) else get_spotify_token()
    if not token:
        if old is not None:
            memory.STATS["fallback"] += 1
        _run[k] = old
        return old
    params = {"q": f'artist:"{name}"', "type": "artist", "market": "US", "limit": 10}
    try:
        r = _get("https://api.spotify.com/v1/search", token, params)
        if r.status_code == 429:
            ra = int(r.headers.get("Retry-After", "60") or 60)
            if ra <= MAX_WAIT:
                time.sleep(ra)
                r = _get("https://api.spotify.com/v1/search", token, params)
            if r.status_code == 429:
                STATE.update(blocked=True, retry_after=int(r.headers.get("Retry-After", ra) or ra), blocked_at=STATE["calls"])
                print(f"[Spotify] rate limited (Retry-After {STATE['retry_after']}s); using memory for the rest of this run")
        if r.status_code != 200:
            if len(STATE["errors"]) < 3 and r.status_code != 429:
                STATE["errors"].append(f"search {r.status_code}: {r.text[:100]}")
            if old is not None:
                memory.STATS["fallback"] += 1
            _run[k] = old
            return old
        items = r.json().get("artists", {}).get("items", [])
        match = [i for i in items if _n(i.get("name", "")) == k]
        pick = max(match, key=lambda i: i.get("popularity", 0)) if match else None   # exact name only; never guess
        if pick:
            imgs = pick.get("images") or []
            res = {"url": (pick.get("external_urls") or {}).get("spotify", ""),
                   "image": (imgs[-2] if len(imgs) > 1 else imgs[0]).get("url", "") if imgs else "",
                   "followers": (pick.get("followers") or {}).get("total") or pick.get("popularity", 0) * 1000,
                   "genres": pick.get("genres") or [], "found": True}
        else:
            res = {"url": "", "image": "", "followers": 0, "genres": [], "found": False}
        memory.put(name, sp_checked=True, spotify_url=res["url"], image=res["image"],
                   spotify_followers=res["followers"], sp_genres=res["genres"])
        memory.STATS["refreshed"] += 1
        _run[k] = res
        return res
    except Exception as e:
        if len(STATE["errors"]) < 3:
            STATE["errors"].append(f"error: {e}"[:110])
        if old is not None:
            memory.STATS["fallback"] += 1
        _run[k] = old
        return old


def health_note():
    s = f"{STATE['calls']} Spotify calls this run"
    if STATE.get("capped"):
        s += f" · reached this run's limit of {MAX_NEW_PER_RUN} new lookups (soonest shows first); the rest fill in on later runs"
    if STATE["blocked"]:
        s += (f" · RATE LIMITED after {STATE['blocked_at']} calls (Spotify asked to wait {STATE['retry_after']}s); "
              f"remembered answers were used and the next run continues where this one stopped")
    if STATE["errors"]:
        s += " · errors: " + " | ".join(STATE["errors"])
    return s
