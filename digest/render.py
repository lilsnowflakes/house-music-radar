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
from datetime import datetime
from zoneinfo import ZoneInfo

from digest.email_builder import build_event_card, CITY_LABELS
from digest.colors import legend_html

PACIFIC = ZoneInfo("America/Los_Angeles")
ORANGE = "#ff6b35"


def esc(x) -> str:
    return _html.escape(str(x or ""))


def announced_card(r: dict) -> str:
    link = (f'<a href="{esc(r["ticket_url"])}" style="color:{ORANGE};">Event page</a>'
            if r.get("ticket_url") else "")
    return f"""
    <div style="background:#1a1a1a;border:1px solid #333;border-radius:8px;
                padding:14px;margin-bottom:10px;font-family:monospace;">
      <div style="font-size:16px;font-weight:bold;color:#fff;">{esc(r['artist'])}</div>
      <div style="color:#ccc;font-size:13px;margin:6px 0;">
        📅 {esc(r['date_str'])} &nbsp;|&nbsp; 📍 {esc(r['venue'])}
      </div>
      <div style="color:{ORANGE};font-size:13px;">⏳ {esc(r['on_sale_text'])}</div>
      <div style="font-size:12px;margin-top:6px;">{link}</div>
    </div>"""


def section(title: str, body: str, note: str = "") -> str:
    note_html = (f'<div style="color:#777;font-size:12px;margin-bottom:10px;">{note}</div>'
                 if note else "")
    return f"""
    <div style="margin-bottom:32px;">
      <h2 style="color:{ORANGE};border-bottom:1px solid #333;padding-bottom:8px;
                 font-family:monospace;">{title}</h2>
      {note_html}{body}
    </div>"""


def health_table(rows) -> str:
    colors = {"ok": "#5ec269", "empty": "#e0b341", "error": "#e5534b",
              "skipped": "#888"}
    trs = ""
    for label, status, detail in rows:
        c = colors.get(status, "#888")
        trs += (f'<tr><td style="padding:4px 10px;color:#ccc;">{esc(label)}</td>'
                f'<td style="padding:4px 10px;color:{c};">{esc(status)}</td>'
                f'<td style="padding:4px 10px;color:#888;">{esc(detail)}</td></tr>')
    return ('<table style="font-family:monospace;font-size:12px;border-collapse:collapse;">'
            f"{trs}</table>")


def build_page(events, announced, health, site_url="", demo=False) -> str:
    now = datetime.now(PACIFIC)
    stamp = now.strftime("%A, %B %-d, %Y")

    banner = ""
    if demo:
        banner = (f'<div style="background:#5a1a1a;color:#fff;padding:10px;'
                  f'text-align:center;font-family:monospace;margin-bottom:16px;">'
                  f'DEMO DATA. These are made-up shows, not real listings.</div>')
    elif site_url:
        banner = (f'<div style="text-align:center;margin-bottom:16px;font-family:monospace;'
                  f'font-size:12px;"><a href="{esc(site_url)}" style="color:{ORANGE};">'
                  f'Open the live page</a></div>')

    # 1. Announced, not on sale
    if announced:
        body = "".join(announced_card(r) for r in announced)
    else:
        body = '<p style="color:#888;font-family:monospace;">Nothing announced-but-unsold found this run.</p>'
    s1 = section(f"⏳ Announced, not on sale yet ({len(announced)})", body,
                 "Ticketmaster rooms only. AXS is not covered (its site blocks automated checks).")

    # 2. Your spots
    watched = [e for e in events if e.get("watched")]
    if watched:
        body = "".join(build_event_card(e) for e in watched)
    else:
        body = '<p style="color:#888;font-family:monospace;">No shows at your watched venues or promoters this run.</p>'
    s2 = section(f"★ Your spots ({len(watched)})", body,
                 "Shows at venues or from promoters you have bought tickets from before.")

    # 3. Everything else, by city
    rest = [e for e in events if not e.get("watched")]
    by_city = {}
    for e in rest:
        by_city.setdefault(e.get("city", "unknown"), []).append(e)
    s3 = ""
    for city, evs in by_city.items():
        label = CITY_LABELS.get(city, city.replace("_", " ").title())
        s3 += section(f"📍 {label} ({len(evs)})", "".join(build_event_card(e) for e in evs))
    if not s3:
        s3 = section("📍 Other house shows", '<p style="color:#888;font-family:monospace;">None this run.</p>')

    # 4. Health
    s4 = section("Source health", health_table(health),
                 "Yellow or red means that source returned nothing this run. Check it before trusting the lists above.")

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>House Music Radar</title></head>
<body style="background:#0d0d0d;color:#fff;font-family:monospace;max-width:680px;margin:0 auto;padding:20px;">
  {banner}
  <div style="text-align:center;padding:16px 0;">
    <div style="font-size:28px;font-weight:bold;color:{ORANGE};letter-spacing:2px;">🎛 HOUSE MUSIC RADAR</div>
    <div style="color:#888;font-size:13px;margin-top:4px;">{stamp} · Los Angeles</div>
  </div>
  {legend_html()}
  {s1}{s2}{s3}{s4}
  <div style="text-align:center;color:#444;font-size:11px;padding:24px 0;border-top:1px solid #222;">
    Updated every Monday morning. Scores: Spotify 50% · RA 30% · SoundCloud 20%.
  </div>
</body></html>"""
