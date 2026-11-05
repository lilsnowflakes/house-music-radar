"""
render.py
Builds the one HTML page used for BOTH the website (docs/index.html) and the
Monday email. Sections, in order:
  1. Announced, not on sale yet (Ticketmaster rooms)
  2. Your spots (watched venues / promoters)
  3. All house shows, by city
  4. Source health (what actually returned data this run)
"""

import html as _html
from digest.venue_links import venue_html
from config.config import HEARD_HOME
from datetime import datetime
from zoneinfo import ZoneInfo

from collections import Counter, OrderedDict
import os
from digest.dates import bucket, sort_key, day_label, to_date, now_pt
from digest import theme as _theme
from digest.hero import hero_svg, vapor_svg, console_svg
from config.config import CODE_VERSION
from digest.colors import legend_html, chips_for

PACIFIC = ZoneInfo("America/Los_Angeles")
ORANGE = "#00b9bc"


def esc(x) -> str:
    return _html.escape(str(x or ""))


def announced_card(r: dict) -> str:
    link = (f'<a href="{esc(r["ticket_url"])}" style="color:{ORANGE};">Event page</a>'
            if r.get("ticket_url") else "")
    return f"""
    <div style="background:#00292a;border:1px solid #005254;border-radius:8px;
                padding:14px;margin-bottom:10px;font-family:monospace;">
      <div style="font-size:16px;font-weight:bold;color:#fff;">{esc(r['artist'])}</div>
      <div style="color:#ccc;font-size:13px;margin:6px 0;">
        📅 {esc(r['date_str'])} &nbsp;|&nbsp; 📍 {venue_html(r['venue'], r.get('address',''))}
      </div>
      <div style="color:{ORANGE};font-size:13px;">⏳ {esc(r['on_sale_text'])}</div>
      <div style="font-size:12px;margin-top:6px;">{link}</div>
    </div>"""


def section(title: str, body: str, note: str = "") -> str:
    note_html = (f'<div style="color:#009092;font-size:12px;margin-bottom:10px;">{note}</div>'
                 if note else "")
    return f"""
    <div style="margin-bottom:32px;">
      <h2 style="color:{ORANGE};border-bottom:1px solid #005254;padding-bottom:8px;
                 font-family:monospace;">{title}</h2>
      {note_html}{body}
    </div>"""


def health_table(rows) -> str:
    colors = {"ok": "#5ec269", "empty": "#e0b341", "error": "#e5534b",
              "skipped": "#00a5a7"}
    trs = ""
    for label, status, detail in rows:
        c = colors.get(status, "#00a5a7")
        trs += (f'<tr><td style="padding:4px 10px;color:#ccc;">{esc(label)}</td>'
                f'<td style="padding:4px 10px;color:{c};">{esc(status)}</td>'
                f'<td style="padding:4px 10px;color:#00a5a7;">{esc(detail)}</td></tr>')
    return ('<table style="font-family:monospace;font-size:12px;border-collapse:collapse;">'
            f"{trs}</table>")



FONT = "font-family:monospace;"


def _initials(name):
    w = [x for x in (name or "?").replace("&", " ").split() if x[:1].isalnum()]
    return ("".join(x[0] for x in w[:2]) or "?").upper()


def event_row(ev: dict) -> str:
    """One compact line per show: photo or initials, artist, venue (Maps), chips, tickets."""
    artist = ev.get("artist") or ev.get("title") or "Unknown"
    star = "★ " if ev.get("watched") else ""
    link = ev.get("ticket_url", "")
    name = (f'<a href="{esc(link)}" style="color:#fff;text-decoration:none;font-weight:bold;">{esc(artist)}</a>'
            if link else f'<span style="color:#fff;font-weight:bold;">{esc(artist)}</span>')
    if ev.get("image"):
        pic = (f'<img src="{esc(ev["image"])}" alt="" width="44" height="44" loading="lazy" '
               f'style="border-radius:50%;object-fit:cover;border:1px solid #005254;flex:none;">')
    else:
        pic = (f'<div style="width:44px;height:44px;border-radius:50%;background:#003e3f;color:#00b9bc;'
               f'display:flex;align-items:center;justify-content:center;font-weight:bold;flex:none;">'
               f'{esc(_initials(artist))}</div>')
    title = ev.get("title", "")
    sub = esc(title) if title and title != artist and len(title) < 90 else ""
    srcs = ev.get("sources") or [ev.get("source", "")]
    via = " + ".join(esc(s) for s in srcs if s)
    score = ev.get("score", 0)
    sc = f'<span style="color:#00b9bc;font-weight:bold;">{score:.0f}</span>' if score else ""
    btn = (f'<a href="{esc(link)}" style="background:#00b9bc;color:#001515;padding:3px 10px;border-radius:4px;'
           f'text-decoration:none;font-size:11px;white-space:nowrap;">Tickets{" " + esc(ev.get("price")) if ev.get("price") else ""}</a>'
           if link else "")
    return (f'<div style="display:flex;gap:12px;align-items:center;background:#00292a;border:1px solid #005254;'
            f'border-radius:8px;padding:10px 12px;margin-bottom:6px;{FONT}">{pic}'
            f'<div style="min-width:0;flex:1;"><div style="font-size:15px;">{star}{name}</div>'
            f'<div style="color:#ccc;font-size:12px;margin-top:2px;">📍 {venue_html(ev.get("venue", ""), ev.get("address", ""))}'
            f'{" · " + sub if sub else ""}</div>'
            f'<div style="margin-top:6px;">{chips_for(ev)}</div>'
            f'<div style="color:#009092;font-size:11px;">via {via}</div></div>'
            f'<div style="text-align:right;flex:none;">{sc}<div style="margin-top:6px;">{btn}</div></div></div>')


def _by_day(evs, today):
    """Chronological, A-Z by artist inside each day."""
    evs = sorted(evs, key=lambda e: (sort_key(e.get("date_str", ""), today),
                                     (e.get("artist") or e.get("title") or "").casefold()))
    days = OrderedDict()
    for e in evs:
        days.setdefault(day_label(e.get("date_str", "")) or "Date unclear", []).append(e)
    return days


def _days_html(evs, today):
    out = ""
    for label, items in _by_day(evs, today).items():
        out += (f'<div style="color:#00a5a7;font-size:12px;letter-spacing:1px;text-transform:uppercase;'
                f'margin:14px 0 6px;{FONT}">{esc(label)}</div>' + "".join(event_row(e) for e in items))
    return out


def _details(id_, title, count, body, open_=False, level=2):
    size = "17px" if level == 2 else "14px"
    empty = f'<div style="color:#00a5a7;font-size:13px;padding:6px 0;{FONT}">Nothing listed.</div>'
    return (f'<details id="{id_}" {"open" if open_ else ""} style="margin-bottom:10px;background:#001515;'
            f'border:1px solid #005254;border-radius:10px;padding:0 12px;">'
            f'<summary style="cursor:pointer;padding:12px 0;color:#00b9bc;font-weight:bold;font-size:{size};{FONT}">'
            f'{title} <span style="color:#00a5a7;font-weight:normal;">({count})</span></summary>'
            f'<div style="padding-bottom:10px;">{body or empty}</div></details>')


def source_map(events, health):
    """Which source supplied how many of the final rows, then the per-source health table."""
    c = Counter(s for e in events for s in (e.get("sources") or [e.get("source", "")]) if s)
    if c:
        rows = "".join(f'<span style="display:inline-block;background:#003e3f;color:#ccc;border-radius:4px;'
                       f'padding:2px 8px;margin:0 6px 6px 0;font-size:12px;">{esc(k)} <b style="color:#00b9bc;">{v}</b></span>'
                       for k, v in c.most_common())
        counts = (f'<div style="{FONT}color:#00a5a7;font-size:12px;margin-bottom:8px;">Shows on this page by source '
                  f'(a show carried by two sources counts for both):</div><div>{rows}</div>')
    else:
        counts = ""
    return counts + health_table(health)


STYLES = [("classic", "Classic", "index.html", "list.html"), ("outrun", "Outrun", "index-outrun.html", "list-outrun.html"),
          ("console", "Console", "index-console.html", "list-console.html")]


def style_switcher(active, base, page="index"):
    """Three check-box style links at the top. The choice is remembered in the browser."""
    idx = 2 if page == "index" else 3
    items = "".join(
        f'<a href="{base}{s[idx]}" data-style="{s[0]}" style="color:#00b9bc;text-decoration:none;padding:5px 12px;'
        f'border:1px solid #005254;border-radius:6px;{"background:#003e3f;font-weight:bold;" if s[0] == active else ""}">'
        f'{"☑" if s[0] == active else "☐"} {s[1]}</a>' for s in STYLES)
    return (f'<div id="styles" style="display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin:0 0 12px;'
            f'font-family:monospace;font-size:12px;"><span style="color:#00a5a7;padding:5px 0;">Style:</span>{items}</div>')


STYLE_JS = ("<script>try{var k='radarStyle',cur=document.body.dataset.style;"
            "document.querySelectorAll('#styles a').forEach(function(a){a.addEventListener('click',function(){localStorage.setItem(k,a.dataset.style)})});"
            "var want=localStorage.getItem(k);if(want&&want!==cur&&!location.search){var l=document.querySelector('#styles a[data-style='+want+']');"
            "if(l)location.replace(l.getAttribute('href'))}}catch(e){}</script>")


def build_page(events, announced, health, site_url="", demo=False, dupes_removed=0, style="classic") -> str:
    now = now_pt()
    stamp = now.strftime("%A, %B %-d, %Y")
    th = _theme.choose() if style == "classic" else (style, 0, "set")
    base = site_url if (site_url and site_url.endswith("/")) else (site_url + "/" if site_url else "")
    run_no = _theme.run_number()
    run_txt = f"Run #{run_no}" if run_no else "Local build"
    ran = now.strftime("%b %-d, %Y %-I:%M %p PT")

    banner = ""
    if demo:
        banner = (f'<div style="background:#5a1a1a;color:#fff;padding:10px;text-align:center;{FONT}'
                  f'margin-bottom:16px;">DEMO DATA. These are made-up shows, not real listings.</div>')
    elif site_url:
        banner = (f'<div style="text-align:center;margin-bottom:12px;{FONT}font-size:12px;">'
                  f'<a href="{esc(site_url)}" style="color:{ORANGE};">Open the live page</a></div>')
    banner += (f'<div style="background:#00292a;border:1px solid #005254;border-radius:6px;padding:10px;'
               f'text-align:center;{FONT}font-size:12px;color:#bbb;margin-bottom:16px;">'
               f'🎧 <a href="{base}{dict((s[0], s[3]) for s in STYLES)[style]}" style="color:{ORANGE};">Full list by night</a> · tap a venue for Google Maps · '
               f'Smaller rooms and tonight\'s live music: <a href="{HEARD_HOME}" style="color:{ORANGE};">Heard (getheard.live)</a></div>')

    # bucket the shows
    groups = {k: [] for k in ("tonight", "week", "next", "later", "unknown")}
    for e in events:
        b = bucket(e.get("date_str", ""), now)
        if b != "past":
            groups[b].append(e)

    s_tonight = _details("tonight", "🔥 Tonight", len(groups["tonight"]),
                         _days_html(groups["tonight"], now), open_=bool(groups["tonight"]))
    s_week = _details("week", "This week", len(groups["week"]), _days_html(groups["week"], now))
    s_next = _details("next", "Next week", len(groups["next"]), _days_html(groups["next"], now))

    months = OrderedDict()
    for e in sorted(groups["later"] + groups["unknown"], key=lambda e: sort_key(e.get("date_str", ""), now)):
        y, m, _ = sort_key(e.get("date_str", ""), now)
        key = "Date unclear" if y == 9999 else datetime(y, m, 1).strftime("%B %Y")
        months.setdefault(key, []).append(e)
    later_body = "".join(_details("m-" + k.replace(" ", "-").lower(), k, len(v), _days_html(v, now), level=3)
                         for k, v in months.items())
    s_later = _details("later", "Later", sum(len(v) for v in months.values()), later_body)

    ann_body = "".join(announced_card(r) for r in announced) or \
        f'<div style="color:#00a5a7;{FONT}font-size:13px;">Nothing announced-but-unsold found this run.</div>'
    s_ann = _details("announced", "⏳ Announced, not on sale yet", len(announced),
                     f'<div style="color:#009092;font-size:12px;margin-bottom:8px;{FONT}">Ticketmaster and DICE rooms only. '
                     f'AXS is not covered (its site blocks automated checks).</div>' + ann_body)

    spots = [e for e in events if e.get("watched") and bucket(e.get("date_str", ""), now) != "past"]
    s_spots = _details("spots", "★ Your spots", len(spots), _days_html(spots, now))

    nav_link = f"color:{ORANGE};text-decoration:none;padding:6px 12px;border:1px solid #005254;border-radius:999px;"
    nav = (f'<div style="position:sticky;top:0;background:#001515;padding:8px 0;margin:0 0 12px;z-index:5;{FONT}'
           f'font-size:13px;display:flex;gap:8px;flex-wrap:wrap;justify-content:center;border-bottom:1px solid #003e3f;">'
           f'<a href="#tonight" style="{nav_link}">Tonight</a><a href="#week" style="{nav_link}">This week</a>'
           f'<a href="#next" style="{nav_link}">Next week</a><a href="#later" style="{nav_link}">Later</a></div>')

    dup_note = f" · {dupes_removed} duplicate listings merged" if dupes_removed else ""
    s_health = (f'<div id="health" style="margin-top:28px;"><h2 style="color:{ORANGE};border-bottom:1px solid #005254;'
                f'padding-bottom:8px;{FONT}">Source health</h2>'
                f'<div style="color:#009092;font-size:12px;margin-bottom:10px;{FONT}">What each source returned on this run{dup_note}. '
                f'Yellow or red means that source returned nothing. Check it before trusting the lists above.</div>'
                f'{source_map(events, health)}</div>')

    how = ("rotates to a new color every run" if th[2] == "auto"
           else "set by config/theme.txt")
    foot = (f'{run_txt} · last ran {ran} · code v{CODE_VERSION} · color: {th[0]} ({how}). '
            f'To pick one, edit config/theme.txt (auto, turquoise, violet, magenta, amber, green, blue, red, outrun, console).<br>'
            f'Updated every Monday morning. Within each day shows are A to Z by artist. '
            f'Scores: Spotify 50% · RA 30% · SoundCloud 20%.')

    page = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mo's House Music Radar</title></head>
<body data-style="{style}" style="background:#001515;color:#fff;font-family:monospace;max-width:680px;margin:0 auto;padding:20px;">
  {banner}
  {style_switcher(style, base)}
  {vapor_svg(run_no) if th[0] == 'outrun' else (console_svg(run_no, len(groups['tonight']), sum(len(v) for v in groups.values())) if th[0] == 'console' else hero_svg(run_no))}
  <div style="text-align:center;padding:14px 0 6px;">
    <div style="font-size:28px;font-weight:bold;color:{ORANGE};letter-spacing:2px;">🎛 MO'S HOUSE MUSIC RADAR</div>
    <div style="color:#00a5a7;font-size:13px;margin-top:4px;">{stamp} · Los Angeles · {run_txt} · last ran {ran}</div>
  </div>
  {nav}
  {legend_html()}
  {s_tonight}{s_week}{s_next}{s_later}{s_ann}{s_spots}
  {s_health}
  <div style="text-align:center;color:#009092;font-size:11px;padding:24px 0;border-top:1px solid #003e3f;margin-top:24px;">
    {foot}
  </div>
<script>
function openFor(id){{var el=id&&document.getElementById(id);if(!el)return;
 for(var p=el;p;p=p.parentElement){{if(p.tagName==='DETAILS')p.open=true;}}
 el.scrollIntoView();}}
addEventListener('hashchange',function(){{openFor(location.hash.slice(1));}});
document.addEventListener('click',function(e){{var a=e.target.closest('a[href^="#"]');
 if(a){{e.preventDefault();history.replaceState(null,'',a.getAttribute('href'));openFor(a.getAttribute('href').slice(1));}}}});
</script>
{STYLE_JS if site_url else ''}
</body></html>"""
    return _theme.apply(page, th)
