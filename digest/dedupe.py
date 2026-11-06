"""
dedupe.py - one show, one row.
Two listings are the same show when they fall on the same day and either
  (a) have the same artist, or
  (b) are at the same venue and one's artist name appears in the other's title.
The merged row keeps the richest data (ticket link, price, address, genres) and lists
every source that carried it in ev["sources"].
"""
import re
from digest.dates import day_key


def _fold(s):
    """'Christian Löffler' -> 'christian loffler' so accents never block a match."""
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c)).lower()


def _n(s):
    return re.sub(r"[^a-z0-9]", "", _fold(s))


def _known_venues():
    try:
        from config.config import WATCH_VENUES, VENUE_CALENDARS
        names = list(WATCH_VENUES.get("los_angeles", [])) if isinstance(WATCH_VENUES, dict) else list(WATCH_VENUES)
        names += [v["venue"] for c in VENUE_CALENDARS.values() for v in c]
        return {_n(x.split("/")[0]): x.split("/")[0].strip() for x in names if x}
    except Exception:
        return {}


def split_venue_prefix(ev):
    """'Origin: Christian Loffler' with no venue -> venue 'Origin', artist 'Christian Loffler'."""
    a = ev.get("artist") or ""
    m = re.match(r"^\s*([^:]{2,40}):\s+(.+)$", a)
    if not m:
        return
    known = _known_venues()
    v = known.get(_n(m.group(1)))
    if v and (not ev.get("venue") or _n(ev.get("venue")) in (_n(v), "")):
        ev["venue"] = ev.get("venue") or v
        ev["artist"] = m.group(2).strip()


def _richness(ev):
    return (bool(ev.get("ticket_url")) * 2 + bool(ev.get("price")) + bool(ev.get("address"))
            + bool(ev.get("genres")))


def _same(a, b):
    aa, ba = _n(a.get("artist")), _n(b.get("artist"))
    if aa and ba and aa[:18] == ba[:18]:
        return True
    va, vb = _n(a.get("venue")), _n(b.get("venue"))
    if va and vb and (va == vb or (len(va) >= 4 and va in vb) or (len(vb) >= 4 and vb in va)):
        for x, y in ((a, b), (b, a)):
            n = _n(x.get("artist"))
            if len(n) >= 4 and n in _n(y.get("title")) + _n(y.get("artist")):
                return True
    return False


def _merge(keep, other):
    oa, ka = _n(other.get("artist")), _n(keep.get("artist"))
    if oa and ka and oa != ka and oa in _n(keep.get("title")) and len(oa) < len(ka):
        keep["artist"] = other["artist"]     # a real artist name beats an event title
    srcs = keep.setdefault("sources", [keep.get("source", "")])
    for s in other.get("sources") or [other.get("source", "")]:
        if s and s not in srcs:
            srcs.append(s)
    for f in ("reddit_url", "moved_from", "promoter"):
        if other.get(f) and not keep.get(f):
            keep[f] = other[f]
    if other.get("source") == "Edmtrain" and other.get("ticket_url"):
        keep["edmtrain_url"] = other["ticket_url"]   # their event link stays visible, unmodified
    for f in ("ticket_url", "price", "address", "image", "ticket_status", "age", "venue", "start_iso", "time_text"):
        if not keep.get(f) and other.get(f):
            keep[f] = other[f]
    if not keep.get("genres") and other.get("genres"):
        keep["genres"] = other["genres"]
    keep["watched"] = bool(keep.get("watched") or other.get("watched"))
    if "sold out" in (other.get("price", "") + other.get("title", "")).lower():
        keep["ticket_status"] = "sold out"
    if other.get("house_check") and not keep.get("house_check"):
        keep["house_check"] = other["house_check"]


def dedupe(events):
    """Returns (merged_list, number_removed)."""
    by_day, order = {}, []
    for ev in events:
        split_venue_prefix(ev)
    for ev in sorted(events, key=_richness, reverse=True):
        k = day_key(ev.get("date_str", ""))
        kept = by_day.setdefault(k, [])
        for t in kept:
            if _same(t, ev):
                _merge(t, ev)
                break
        else:
            ev.setdefault("sources", [ev.get("source", "")])
            kept.append(ev)
            order.append(ev)
    return order, len(events) - len(order)
