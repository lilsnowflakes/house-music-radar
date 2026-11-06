"""
memory.py - the radar's memory of artists between runs.

Every GitHub run starts on a blank machine, so without this the radar would forget everything
Spotify told it. This file (data/artist_memory.json) is carried from run to run by the workflow's
cache step. Rules:
  - Fresh answers (under REFRESH_DAYS old) are reused without asking Spotify again.
  - Older answers are refreshed when Spotify works.
  - If Spotify fails on a run, the last good answer is used instead of losing it.
"""
import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "artist_memory.json")
REFRESH_DAYS = 14
STATS = {"reused": 0, "refreshed": 0, "fallback": 0}
_mem = None


def _load():
    global _mem
    if _mem is None:
        try:
            with open(PATH, encoding="utf-8") as f:
                _mem = json.load(f)
        except (OSError, ValueError):
            _mem = {}
    return _mem


def _key(name):
    from digest.dedupe import _n
    return _n(name)


def age_days(rec):
    try:
        t = datetime.fromisoformat(rec["updated"])
        return (datetime.now(timezone.utc) - t).days
    except (KeyError, ValueError, TypeError):
        return 9999


def get(name, field, fresh_only=True):
    """The remembered value, or None. fresh_only=False returns it however old (used when Spotify is down)."""
    rec = _load().get(_key(name))
    if not rec or field not in rec:
        return None
    if fresh_only and age_days(rec) > REFRESH_DAYS:
        return None
    return rec[field]


def put(name, **fields):
    m = _load()
    rec = m.setdefault(_key(name), {"name": name})
    rec.update({k: v for k, v in fields.items() if v not in (None, "", [])})
    rec["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")


def save():
    m = _load()
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=0, sort_keys=True)
    os.replace(tmp, PATH)


def meta(key, value=None):
    """Small run-to-run notes that aren't about an artist (e.g. when Spotify's penalty ends)."""
    m = _load().setdefault("__meta__", {})
    if value is not None:
        m[key] = value
    return m.get(key)


def summary():
    m = {k: v for k, v in _load().items() if not k.startswith("__")}
    with_link = sum(1 for r in m.values() if r.get("spotify_url"))
    return (f"{len(m)} artists remembered ({with_link} with a Spotify page) · this run: "
            f"{STATS['refreshed']} looked up, {STATS['reused']} reused from memory, "
            f"{STATS['fallback']} kept from memory because the lookup failed")
