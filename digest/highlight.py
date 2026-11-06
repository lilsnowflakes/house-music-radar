"""highlight.py - the one featured show at the top of the page and the email."""
import os
import re

from digest.dates import bucket, sort_key, now_pt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _n(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _manual():
    try:
        lines = open(os.path.join(ROOT, "config", "highlight.txt"), encoding="utf-8").read().splitlines()
    except OSError:
        return []
    out = []
    for l in lines:
        l = l.strip()
        if l and not l.startswith("#"):
            key, _, note = l.partition("|")
            out.append((key.strip(), note.strip()))
    return out


def _is_pm(ev):
    t = (" ".join(ev.get("genres") or []) + " " + ev.get("title", "")).lower()
    return "progressive" in t or "melodic" in t


def pick(events, now=None):
    """Returns (event, note, how) with how = "picked by you" or "auto pick", or (None, "", "")."""
    now = now or now_pt()
    upcoming = [e for e in events if bucket(e.get("date_str", ""), now) not in ("past", "unknown")]
    upcoming.sort(key=lambda e: sort_key(e.get("date_str", ""), now))
    for key, note in _manual():
        k = _n(key)
        for e in upcoming:
            if k and (k in _n(e.get("artist")) or k in _n(e.get("title")) or key in e.get("ticket_url", "")):
                return e, note, "picked by you"
    soon = [e for e in upcoming if bucket(e.get("date_str", ""), now) in ("tonight", "tomorrow", "week", "next")][:200]
    if not soon:
        return None, "", ""

    def rank(e):
        v = (e.get("house_check") or {}).get("verdict")
        return (3 * bool(e.get("watched")) + 2 * _is_pm(e) + (v == "house") + e.get("score", 0) / 100,
                -sort_key(e.get("date_str", ""), now)[2])
    best = max(soon[:60], key=rank)
    return best, "", "auto pick"
