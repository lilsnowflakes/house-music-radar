"""
venue_links.py
Turns a venue name into a Google Maps link, and into a getheard.live venue link when Heard has one.
"""
import re
from urllib.parse import quote_plus

from config.config import VENUE_ADDRESSES, HEARD_VENUES, HEARD_HOME


def _clean(name):
    n = re.sub(r"\s*\((?:los angeles|[^)]*)\)\s*$", "", name or "", flags=re.I)
    n = re.sub(r"(?i)\b(indoors|outdoors)\b", "", n)
    return re.sub(r"^(the)\s+", "", n.strip(), flags=re.I).strip() or (name or "")


def address_for(venue, given=""):
    if given:
        return given
    v = (venue or "").lower()
    for key, addr in VENUE_ADDRESSES.items():
        if key in v:
            return addr
    return ""


def maps_url(venue, address=""):
    q = f"{venue}, {address_for(venue, address)}" if address_for(venue, address) else f"{venue}, Los Angeles, CA"
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(q)


def heard_url(venue):
    v = (venue or "").lower()
    for name, slug in HEARD_VENUES.items():
        if name in v or v in name and len(v) > 4:
            return f"{HEARD_HOME}venue/{slug}"
    return ""


def venue_html(venue, address="", color="#00b9bc"):
    """Venue name linked to Google Maps, plus a small 'Heard' link when it exists."""
    if not venue:
        return ""
    out = f'<a href="{maps_url(venue, address)}" style="color:#ccc;text-decoration:underline;">{venue}</a>'
    h = heard_url(venue)
    if h:
        out += f' <a href="{h}" style="color:{color};font-size:11px;">Heard</a>'
    return out
