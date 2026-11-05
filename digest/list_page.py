"""
list_page.py
Second web page (docs/list.html): the "LA House Radar" list.
Sticky filter bar, one block per night, color chips, and a block of venue calendars
pulled straight from the venue sources. Built from the same events as the main page.
"""
import html
import re
from collections import OrderedDict
from datetime import datetime
from zoneinfo import ZoneInfo

from digest.colors import chips_for, legend_html
from digest.venue_links import venue_html
from config.config import HEARD_HOME

e = html.escape
MON = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}
CAL_SOURCES = ("DICE venue", "Discotech", "Framework")


def sort_key(date_str, today):
    m = re.search(r"([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2})(?:,\s*(\d{4}))?", re.sub(r"^[A-Za-z]{3,9}:?\s", "", date_str or ""))
    if not m or m.group(1).lower() not in MON:
        return (9999, 12, 31)
    mo, d = MON[m.group(1).lower()], int(m.group(2))
    y = int(m.group(3)) if m.group(3) else today.year + (1 if mo < today.month - 1 else 0)
    return (y, mo, d)


def day_label(date_str):
    return re.sub(r"\s*\(.*$", "", (date_str or "").replace(": ", " ")).strip()


def build_list_page(events, site_url="", home_url="index.html"):
    today = datetime.now(ZoneInfo("America/Los_Angeles"))
    evs = sorted(events, key=lambda x: (sort_key(x.get("date_str", ""), today), -x.get("score", 0)))

    cal = OrderedDict()
    for x in evs:
        if x.get("source") in CAL_SOURCES:
            cal.setdefault(x["venue"], []).append(x)
    vh = ""
    for venue, items in cal.items():
        lis = "".join(
            f'<li><b>{e(day_label(i["date_str"]))}</b> {e(i["artist"] or i["title"])}'
            f' <i>{e(i.get("price", ""))}</i></li>' for i in items)
        vh += (f'<div class="vn"><div class="vt">{venue_html(venue, items[0].get("address", ""), "#9d8bff")}</div>'
               f'<span class="vs">{e(items[0]["source"])}</span><ul>{lis}</ul></div>')
    vblock = (f'<section class="vsec"><h2>Straight from the venue calendars</h2>'
              f'<p class="vnote">Read directly from venue calendars. Tap a venue name for Google Maps.</p>'
              f'<div class="vg">{vh}</div></section>') if vh else ""

    days = OrderedDict()
    for x in evs:
        days.setdefault(day_label(x.get("date_str", "")), []).append(x)
    out = []
    for label, items in days.items():
        out.append(f'<section class="day"><h2>{e(label)}</h2>')
        for x in items:
            kind = ("s" if x.get("watched") else "") + ("g" if any(
                w in " ".join(x.get("genres") or []).lower() + x.get("title", "").lower()
                for w in ("progressive", "melodic")) else "")
            star = '<span class="b s">★ your spot</span>' if x.get("watched") else ""
            link = x.get("ticket_url", "")
            lk = (f'<a href="{e(link)}" target="_blank" rel="noopener">{e(x.get("source") or "Tickets")} ↗</a>' if link else "")
            title = e(x.get("artist") or x.get("title", ""))
            t = f'<a class="t" href="{e(link)}" target="_blank" rel="noopener">{title}</a>' if link else f'<span class="t">{title}</span>'
            out.append(
                f'<article class="ev" data-k="{kind}"><div class="main">{t}'
                f'<div class="v">{venue_html(x.get("venue", ""), x.get("address", ""), "#9d8bff")}</div>'
                f'<div class="bs">{chips_for(x)}{star}</div></div>'
                f'<div class="side"><div class="pr">{e(x.get("price", ""))}</div>'
                f'<div class="lk">{lk}'
                '</div></div></article>')
        out.append("</section>")

    n = len(evs)
    pm = sum(1 for x in evs if "progressive" in " ".join(x.get("genres") or []).lower() + x.get("title", "").lower()
             or "melodic" in " ".join(x.get("genres") or []).lower() + x.get("title", "").lower())
    ns = sum(1 for x in evs if x.get("watched"))
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"><title>LA House Radar</title>
<style>
:root{{--bg:#12101a;--fg:#ece9f5;--mut:#9b95ad;--line:#2b2740;--card:#1b1828;--acc:#9d8bff}}
*{{box-sizing:border-box}}body{{background:var(--bg);color:var(--fg);font-family:system-ui,sans-serif;font-size:15px;line-height:1.4;margin:0;padding:20px 16px 48px}}
.wrap{{max-width:820px;margin:0 auto}}h1{{font-weight:800;font-size:clamp(30px,6vw,46px);letter-spacing:-.02em;margin:0 0 6px}}
.sub{{color:var(--mut);font-size:14px;margin:0 0 18px;max-width:62ch}}.sub a,.nav a{{color:var(--acc)}}
.nav{{font:12px monospace;margin-bottom:12px}}
.bar{{position:sticky;top:0;background:var(--bg);padding:10px 0;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid var(--line);z-index:5}}
.bar button{{font:500 13px monospace;border:1px solid var(--line);background:var(--card);color:var(--fg);padding:7px 12px;border-radius:999px;cursor:pointer}}
.bar button[aria-pressed=true]{{background:var(--acc);border-color:var(--acc);color:#12101a}}
.vsec{{margin:18px 0 6px}}.vsec h2{{font:500 13px monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--acc);margin:0 0 6px}}
.vnote{{color:var(--mut);font-size:13px;margin:0 0 10px}}.vg{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}}
.vn{{background:var(--card);border:1px solid var(--acc);border-radius:10px;padding:12px 14px;min-width:0}}.vt{{font-weight:800;display:inline}}
.vs{{font:11px monospace;color:var(--mut);margin-left:8px}}.vn ul{{margin:8px 0 0;padding-left:18px;font-size:13px}}.vn i{{font-style:normal;color:var(--mut);font:12px monospace}}
.day h2{{font:500 13px monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--mut);margin:26px 0 8px}}
.ev{{display:flex;gap:16px;justify-content:space-between;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-bottom:8px}}
.main{{min-width:0}}.side{{text-align:right;font:12px monospace;color:var(--mut);flex:none;max-width:42%}}
.t{{font-weight:800;font-size:17px;color:var(--fg);text-decoration:none;overflow-wrap:anywhere}}a.t:hover{{color:var(--acc);text-decoration:underline}}
.v{{color:var(--mut);font-size:13px;margin-top:2px}}.bs{{margin-top:8px}}
.b.s{{display:inline-block;background:#3d2a0a;color:#ffc16b;font-size:11px;padding:2px 8px;border-radius:4px}}
.lk a{{color:var(--acc);text-decoration:none}}
@media(max-width:520px){{.ev{{flex-direction:column;gap:8px}}.side{{text-align:left;max-width:none}}}}
</style></head><body><div class="wrap">
<div class="nav"><a href="{e(home_url)}">← Weekly digest</a> · Smaller rooms and tonight's live music: <a href="{HEARD_HOME}">Heard</a></div>
<h1>LA House Radar</h1>
<p class="sub">Updated {today:%b %-d, %Y}. {n} Los Angeles house listings from 19hz, RA, DICE, Shotgun, SceneStar, venue calendars and Heard. Titles link to the ticket page.</p>
{legend_html()}
<div class="bar" role="group" aria-label="Filter"><button data-f="" aria-pressed="true">All {n}</button><button data-f="g" aria-pressed="false">Progressive / melodic {pm}</button><button data-f="s" aria-pressed="false">Your spots {ns}</button></div>
{vblock}
{''.join(out)}
</div>
<script>
document.querySelectorAll('.bar button').forEach(b=>b.addEventListener('click',()=>{{
 document.querySelectorAll('.bar button').forEach(x=>x.setAttribute('aria-pressed',x===b));
 const f=b.dataset.f;
 document.querySelectorAll('.ev').forEach(el=>el.hidden=!!f&&!el.dataset.k.includes(f));
 document.querySelectorAll('.day').forEach(d=>d.hidden=![...d.querySelectorAll('.ev')].some(el=>!el.hidden));
}}));
</script></body></html>"""
