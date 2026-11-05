"""artist_links.py - YouTube and Spotify links for an artist.
Direct links are used when the scorer found them (a real latest set, the artist's Spotify page).
Otherwise the link is a search that always works: YouTube sorted by newest upload, Spotify artist search."""
import html
import re
from urllib.parse import quote, quote_plus


def artist_name(ev):
    a = (ev.get("artist") or "").strip()
    a = re.split(r"\s*(?:,|&|\bb2b\b|\bw/\b|\bwith\b|\bx\b|\bpresents\b|\bft\.?\b|\bfeat\.?\b)\s*", a, maxsplit=1, flags=re.I)[0]
    return a


def youtube_url(ev):
    direct = ev.get("youtube_set_url")
    if direct:
        return direct, "Latest set"
    q = quote_plus(artist_name(ev) + " DJ set")
    return f"https://www.youtube.com/results?search_query={q}&sp=CAI%253D", "YouTube sets"


def spotify_url(ev):
    direct = ev.get("spotify_url")
    if direct:
        return direct, "Spotify"
    return f"https://open.spotify.com/search/{quote(artist_name(ev))}", "Spotify"


ICONS = {
    "youtube": '<svg width="18" height="13" viewBox="0 0 18 13" style="vertical-align:-2px;margin-right:5px" aria-hidden="true"><rect width="18" height="13" rx="3.5" fill="#ff0000"/><path d="M7 3.6v5.8L12 6.5z" fill="#fff"/></svg>',
    "spotify": '<svg width="15" height="15" viewBox="0 0 16 16" style="vertical-align:-3px;margin-right:5px" aria-hidden="true"><circle cx="8" cy="8" r="8" fill="#1db954"/><path d="M3.6 5.6c2.9-.9 6.1-.6 8.8.9M4 8.2c2.5-.7 5.2-.5 7.4.8M4.4 10.6c2-.5 4-.3 5.8.6" fill="none" stroke="#000" stroke-width="1.15" stroke-linecap="round"/></svg>',
    "soundcloud": '<svg width="19" height="12" viewBox="0 0 19 12" style="vertical-align:-2px;margin-right:5px" aria-hidden="true"><path d="M7.5 11.5V2.6C8.6 1.7 9.8 1.2 11.1 1.2c2.3 0 4.2 1.7 4.5 3.9.3-.1.6-.2.9-.2 1.4 0 2.5 1.1 2.5 2.5s-1.1 2.5-2.5 2.5z" fill="#ff5500"/><path d="M1 8v3M3 6.5v5M5 5.5v6M6.3 6.5v5" stroke="#ff5500" stroke-width="1.2" stroke-linecap="round"/></svg>',
}


def soundcloud_url(ev):
    direct = ev.get("soundcloud_url")
    if direct:
        return direct, "SoundCloud"
    return f"https://soundcloud.com/search/people?q={quote_plus(artist_name(ev))}", "SoundCloud"


def links_html(ev, color="#00b9bc", size="11px", mode="web", base=""):
    """Three icon-only links (YouTube, Spotify, SoundCloud).
    mode="web": inline SVG icons. mode="email": PNG icons hosted on the site (email apps drop SVG)."""
    if not artist_name(ev):
        return ""
    items = [("youtube", "YouTube", youtube_url(ev)[0]), ("spotify", "Spotify", spotify_url(ev)[0]),
             ("soundcloud", "SoundCloud", soundcloud_url(ev)[0])]
    out = ""
    for key, label, url in items:
        if mode == "email":
            h = {"youtube": 16, "spotify": 20, "soundcloud": 14}[key]
            w = {"youtube": 22, "spotify": 20, "soundcloud": 22}[key]
            icon = (f'<img src="{html.escape(base)}icons/{key}.png" width="{w}" height="{h}" alt="{label}" '
                    f'style="border:0;vertical-align:middle;">')
            out += (f'<a href="{html.escape(url)}" title="{label}" style="text-decoration:none;display:inline-block;'
                    f'margin-right:14px;">{icon}</a>')
        else:
            out += (f'<a href="{html.escape(url)}" title="{label}" aria-label="{label}" style="text-decoration:none;'
                    f'display:inline-block;margin-right:6px;padding:6px 8px 4px 0;">{ICONS[key].replace("margin-right:5px", "margin:0")}</a>')
    return out
