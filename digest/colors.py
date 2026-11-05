"""
colors.py
One place for the digest's color coding, so the email and the website match.
Genre buckets, ticket status and genre-check result each get their own chip color.
Inline styles only (email clients ignore stylesheets).
"""

GENRE = [  # (label, keywords, text color, background)
    ("Progressive / melodic", ("progressive", "melodic"), "#b39dff", "#2a2250"),
    ("Deep / organic / afro", ("deep", "organic", "afro", "soulful"), "#4fd1c5", "#0f3a36"),
    ("Tech / minimal", ("tech", "minimal", "techno"), "#ffb454", "#3d2a0a"),
    ("Disco / funky / garage", ("disco", "funky", "garage", "french", "jackin"), "#ff8fc8", "#40152e"),
]
OTHER_HOUSE = ("House", "#9fb4c7", "#222d38")

STATUS = {
    "on sale": ("On sale", "#5ec269", "#14301a"),
    "announced": ("Not on sale yet", "#ff9f43", "#40280c"),
    "sold out": ("Sold out", "#ff6b6b", "#401717"),
}
CHECK = {
    "house": ("✓ Confirmed house", "#5ec269", "#14301a"),
    "unverified": ("? Genre unverified", "#e0b341", "#3a2f0c"),
    "tagged": ("Tagged house by source", "#9aa0a6", "#262626"),
}


def genre_bucket(genres, title=""):
    text = " ".join(genres or []).lower() or title.lower()
    for label, words, fg, bg in GENRE:
        if any(w in text for w in words):
            return label, fg, bg
    return OTHER_HOUSE


def chip(label, fg, bg):
    return (f'<span style="display:inline-block;background:{bg};color:{fg};font-size:11px;'
            f'padding:2px 8px;border-radius:4px;margin:0 6px 4px 0;">{label}</span>')


def chips_for(ev):
    """Genre + ticket status + genre-check chips for one show."""
    label, fg, bg = genre_bucket(ev.get("genres"), ev.get("title", ""))
    out = chip(label, fg, bg)
    status = ev.get("ticket_status") or ("on sale" if ev.get("ticket_url") else "")
    if "sold out" in (ev.get("title", "") + " " + ev.get("price", "")).lower():
        status = "sold out"
    if status in STATUS:
        out += chip(*STATUS[status])
    verdict = (ev.get("house_check") or {}).get("verdict") or "tagged"
    if verdict in CHECK:
        out += chip(*CHECK[verdict])
    return out


def legend_html():
    parts = [chip(l, fg, bg) for l, _, fg, bg in GENRE] + [chip(*OTHER_HOUSE)]
    parts += [chip(*v) for v in STATUS.values()] + [chip(*v) for v in CHECK.values()]
    return ('<div style="margin:0 0 16px;font-family:monospace;"><div style="color:#777;font-size:11px;'
            'margin-bottom:6px;">Color key: genre, ticket status, genre check</div>' + "".join(parts) + "</div>")
