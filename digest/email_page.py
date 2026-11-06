"""
email_page.py - the Monday email.
Built for reading in an inbox: light background, dark text, table layout, inline styles only,
no scripts, no collapsing, PNG icons. The website has its own dark styles (render.py).
"""
import html as _html
from collections import OrderedDict

from config.config import CODE_VERSION, HEARD_HOME
from digest.artist_links import links_html
from digest.share import email_links
from digest.colors import chips_for
from digest.dates import bucket, day_label, now_pt, sort_key
from digest.venue_links import maps_url
from digest import theme as _theme
from digest import highlight as _hl

INK, MUTED, LINE, CARD, BG = "#1b1b2f", "#5b5b72", "#e4e1ec", "#ffffff", "#f1eff6"
ACC, ACC_DK = "#0b7a75", "#08524f"
F = "font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;"
e = _html.escape


def _initials(name):
    w = [x for x in (name or "?").replace("&", " ").split() if x[:1].isalnum()]
    return ("".join(x[0] for x in w[:2]) or "?").upper()


def _row(ev, base):
    artist = ev.get("artist") or ev.get("title") or "Unknown"
    star = "★ " if ev.get("watched") else ""
    link = ev.get("ticket_url", "")
    name = (f'<a href="{e(link)}" style="color:{INK};text-decoration:none;">{e(artist)}</a>' if link else e(artist))
    if ev.get("image"):
        pic = (f'<img src="{e(ev["image"])}" width="44" height="44" alt="" '
               f'style="border-radius:22px;display:block;border:0;">')
    else:
        pic = (f'<div style="width:44px;height:44px;border-radius:22px;background:#d9efec;color:{ACC_DK};'
               f'font-weight:700;font-size:15px;line-height:44px;text-align:center;{F}">{e(_initials(artist))}</div>')
    venue = ev.get("venue", "")
    price = ev.get("price", "")
    btn = (f'<a href="{e(link)}" style="background:{ACC};color:#ffffff;text-decoration:none;font-weight:600;'
           f'font-size:13px;padding:8px 14px;border-radius:6px;display:inline-block;white-space:nowrap;{F}">'
           f'Tickets{" · " + e(price) if price else ""}</a>') if link else ""
    srcs = " + ".join(e(s) for s in (ev.get("sources") or [ev.get("source", "")]) if s)
    return f"""<tr><td style="padding:0 0 10px 0;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{CARD};border:1px solid {LINE};border-radius:10px;">
<tr><td width="44" valign="top" style="padding:14px 0 14px 14px;">{pic}</td>
<td valign="top" style="padding:14px 12px;{F}">
<div style="font-size:16px;font-weight:700;color:{INK};line-height:1.25;">{star}{name}</div>
<div style="font-size:13px;color:{MUTED};margin-top:3px;">📍 <a href="{e(maps_url(venue, ev.get('address', '')))}" style="color:{ACC_DK};text-decoration:underline;">{e(venue)}</a></div>
<div style="margin-top:8px;line-height:1.9;">{chips_for(ev, light=True)}</div>
<div style="margin-top:6px;">{links_html(ev, mode="email", base=base)}</div>
<div style="margin-top:6px;">{email_links(ev)}</div>
<div style="font-size:11px;color:#8a8aa0;margin-top:6px;">via {srcs}</div>
</td><td valign="middle" align="right" style="padding:14px 14px 14px 0;">{btn}</td></tr></table></td></tr>"""


def _days(evs, base, today):
    evs = sorted(evs, key=lambda x: (sort_key(x.get("date_str", ""), today),
                                     (x.get("artist") or "").casefold()))
    days = OrderedDict()
    for x in evs:
        days.setdefault(day_label(x.get("date_str", "")) or "Date unclear", []).append(x)
    out = ""
    for label, items in days.items():
        out += (f'<tr><td style="padding:14px 0 8px;{F}font-size:12px;font-weight:700;letter-spacing:1.2px;'
                f'text-transform:uppercase;color:{ACC_DK};">{e(label)}</td></tr>')
        out += "".join(_row(x, base) for x in items)
    return out


def _section(title, count, inner):
    return (f'<tr><td style="padding:26px 0 4px;{F}font-size:20px;font-weight:800;color:{INK};'
            f'border-bottom:2px solid {ACC};">{title} <span style="color:{MUTED};font-weight:500;font-size:15px;">({count})</span></td></tr>'
            + inner)


def _announced(r):
    link = (f'<a href="{e(r["ticket_url"])}" style="color:{ACC_DK};">Event page</a>' if r.get("ticket_url") else "")
    return (f'<tr><td style="padding:0 0 10px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="background:{CARD};border:1px solid {LINE};border-radius:10px;"><tr><td style="padding:14px;{F}">'
            f'<div style="font-size:16px;font-weight:700;color:{INK};">{e(r["artist"])}</div>'
            f'<div style="font-size:13px;color:{MUTED};margin-top:3px;">📅 {e(r["date_str"])} · '
            f'📍 <a href="{e(maps_url(r["venue"], r.get("address", "")))}" style="color:{ACC_DK};">{e(r["venue"])}</a></div>'
            f'<div style="font-size:13px;color:#9a5200;margin-top:6px;font-weight:600;">⏳ {e(r["on_sale_text"])}</div>'
            f'<div style="margin-top:6px;">{links_html(r, mode="email", base="")}</div>'
            f'<div style="font-size:13px;margin-top:6px;">{link}</div></td></tr></table></td></tr>')


def build_email(events, announced, health, site_url="", dupes_removed=0):
    now = now_pt()
    base = site_url if site_url.endswith("/") or not site_url else site_url + "/"
    run_no = _theme.run_number()
    run_txt = f"Run #{run_no}" if run_no else "Local build"
    groups = {k: [] for k in ("tonight", "week", "next", "later", "unknown")}
    # Edmtrain's terms: their data must not be shown older than 24h, and an email can sit unread for days.
    events = [x for x in events if (x.get("sources") or [x.get("source")]) != ["Edmtrain"]]
    for x in events:
        b = bucket(x.get("date_str", ""), now)
        if b != "past":
            groups[b].append(x)
    later = groups["later"] + groups["unknown"]
    spots = sum(1 for x in events if x.get("watched") and bucket(x.get("date_str", ""), now) != "past")

    stats = [(len(groups["tonight"]), "tonight"), (len(groups["week"]), "this week"),
             (len(groups["next"]), "next week"), (spots, "at your spots"), (len(announced), "announced")]
    cells = "".join(
        f'<td align="center" style="padding:10px 4px;{F}"><div style="font-size:22px;font-weight:800;color:#ffffff;">{n}</div>'
        f'<div style="font-size:11px;color:#bfe9e5;">{lab}</div></td>' for n, lab in stats)

    body = ""
    hl, note, how = _hl.pick(events, now)
    if hl:
        n_html = f'<div style="font-size:14px;color:{INK};margin:4px 0 8px;">{e(note)}</div>' if note else ""
        body += (f'<tr><td style="padding:22px 0 8px;{F}font-size:12px;font-weight:800;letter-spacing:2px;color:{ACC_DK};">'
                 f'★ HIGHLIGHT · {e(how.upper())}</td></tr>'
                 + (f'<tr><td style="{F}">{n_html}</td></tr>' if note else "") + _row(hl, base))
    for key, title in (("tonight", "🔥 Tonight"), ("week", "This week"), ("next", "Next week")):
        if groups[key] or key == "tonight":
            inner = _days(groups[key], base, now) if groups[key] else \
                f'<tr><td style="padding:14px 0;{F}color:{MUTED};font-size:14px;">Nothing listed.</td></tr>'
            body += _section(title, len(groups[key]), inner)
    if later:
        months = OrderedDict()
        for x in sorted(later, key=lambda x: sort_key(x.get("date_str", ""), now)):
            y, m, _ = sort_key(x.get("date_str", ""), now)
            months.setdefault("Date unclear" if y == 9999 else now.replace(year=y, month=m, day=1).strftime("%B %Y"), []).append(x)
        lines = "".join(f'<div style="padding:3px 0;">{e(k)}: <b>{len(v)}</b></div>' for k, v in months.items())
        body += _section("Later", len(later),
                         f'<tr><td style="padding:14px 0;{F}font-size:14px;color:{INK};">{lines}'
                         f'<div style="margin-top:10px;"><a href="{e(base)}" style="color:{ACC_DK};font-weight:600;">'
                         f'See every later show on the website →</a></div></td></tr>')
    if announced:
        body += _section("⏳ Announced, not on sale yet", len(announced), "".join(_announced(r) for r in announced))

    dots = {"ok": "#2e9e4f", "empty": "#d19a00", "error": "#c83a3a", "skipped": "#8a8aa0"}
    hl = "".join(f'<span style="display:inline-block;margin:0 14px 4px 0;white-space:nowrap;">'
                 f'<span style="color:{dots.get(s, "#8a8aa0")};">●</span> {e(l)}</span>' for l, s, _ in health)
    dup = f" · {dupes_removed} duplicate listings merged" if dupes_removed else ""
    health_html = (f'<tr><td style="padding:28px 0 6px;{F}font-size:13px;font-weight:700;color:{INK};">Source health{dup}</td></tr>'
                   f'<tr><td style="{F}font-size:12px;color:{MUTED};line-height:1.7;">{hl}<br>'
                   f'Green worked, yellow returned nothing, red errored. Details are on the website.</td></tr>')

    site = (f'<a href="{e(base)}" style="color:#ffffff;font-weight:700;">Open the website</a> · '
            f'<a href="{e(base)}list.html" style="color:#ffffff;">Full list by night</a> · '
            f'<a href="{e(HEARD_HOME)}" style="color:#ffffff;">Heard</a>') if base else ""

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light only"><meta name="supported-color-schemes" content="light only">
<title>Mo's House Music Radar</title></head>
<body style="margin:0;padding:0;background:{BG};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG};"><tr><td align="center" style="padding:18px 10px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;">
<tr><td style="background:#0b4f4c;border-radius:14px 14px 0 0;padding:26px 22px 8px;{F}">
<div style="font-size:12px;letter-spacing:2px;color:#9fe3dc;font-weight:700;">LOS ANGELES · {now:%A, %B %-d}</div>
<div style="font-size:28px;font-weight:800;color:#ffffff;line-height:1.15;margin-top:6px;">🎛 Mo's House Music Radar</div></td></tr>
<tr><td style="background:#0b4f4c;padding:8px 12px 4px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>{cells}</tr></table></td></tr>
<tr><td style="background:#08524f;border-radius:0 0 14px 14px;padding:12px 22px;{F}font-size:13px;color:#d6f3f0;">{site}</td></tr>
<tr><td style="padding:4px 0 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{body}{health_html}</table></td></tr>
<tr><td style="padding:26px 0 8px;{F}font-size:11px;color:#8a8aa0;text-align:center;line-height:1.7;">
{run_txt} · {now:%b %-d, %Y %-I:%M %p} PT · code v{CODE_VERSION}<br>
Shows are listed by date, A to Z within each day. The website has a dark version with three style choices.</td></tr>
</table></td></tr></table></body></html>"""
