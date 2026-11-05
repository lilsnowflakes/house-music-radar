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


def _n(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


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
    srcs = keep.setdefault("sources", [keep.get("source", "")])
    for s in other.get("sources") or [other.get("source", "")]:
        if s and s not in srcs:
            srcs.append(s)
    for f in ("ticket_url", "price", "address", "image", "ticket_status"):
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
