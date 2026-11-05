"""
email_builder.py
Builds and sends the weekly HTML email digest.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config.config import (
    EMAIL_TO,
    EMAIL_FROM,
    EMAIL_PASSWORD,
    SMTP_HOST,
    SMTP_PORT,
)


CITY_LABELS = {
    "los_angeles": "Los Angeles",
}

SCORE_EMOJI = {
    (80, 100): "🔥🔥🔥",
    (60, 80):  "🔥🔥",
    (40, 60):  "🔥",
    (20, 40):  "⚡",
    (0, 20):   "🎵",
}

def get_score_emoji(score: float) -> str:
    for (low, high), emoji in SCORE_EMOJI.items():
        if low <= score <= high:
            return emoji
    return "🎵"

def format_number(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}K"
    return str(n)

from digest.colors import chips_for
from digest.venue_links import venue_html


def build_event_card(ev: dict) -> str:
    score = ev.get("score", 0)
    emoji = get_score_emoji(score)
    artist = ev.get("artist") or ev.get("title") or "Unknown Artist"
    star = "★ " if ev.get("watched") else ""
    venue = ev.get("venue", "")
    date_str = ev.get("date_str", "")
    genres = ev.get("genres", [])
    genres_str = " · ".join(g.title() for g in genres[:4]) if genres else ""
    chips_html = chips_for(ev)
    ticket_url = ev.get("ticket_url", "")
    source = ev.get("source", "")
    price = ev.get("price", "")

    spotify = ev.get("spotify_listeners", 0)
    ra_f = ev.get("ra_followers", 0)
    sc_f = ev.get("soundcloud_followers", 0)
    yt_set = ev.get("youtube_set_url", "")
    yt_tracks = ev.get("youtube_track_urls", [])

    # Score bar (visual)
    filled = int(score / 10)
    bar = "█" * filled + "░" * (10 - filled)

    # YouTube links
    yt_html = ""
    if yt_set:
        yt_html += f'<a href="{yt_set}" style="color:#ff6b35;">▶ Watch DJ Set</a>'
    elif yt_tracks:
        links = " &nbsp;|&nbsp; ".join(
            [f'<a href="{u}" style="color:#ff6b35;">▶ Track {i+1}</a>'
             for i, u in enumerate(yt_tracks[:2])]
        )
        yt_html = links

    ticket_html = ""
    if ticket_url:
        price_label = f" — {price}" if price else ""
        ticket_html = f'<a href="{ticket_url}" style="background:#ff6b35;color:#fff;padding:4px 12px;border-radius:4px;text-decoration:none;font-size:12px;">GET TICKETS{price_label}</a>'

    return f"""
    <div style="background:#1a1a1a;border:1px solid #333;border-radius:8px;
                padding:16px;margin-bottom:12px;font-family:monospace;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
          <span style="font-size:18px;font-weight:bold;color:#fff;">{star}{emoji} {artist}</span>
          <span style="color:#888;font-size:12px;margin-left:8px;">via {source}</span>
        </div>
        <div style="text-align:right;color:#ff6b35;font-size:20px;font-weight:bold;">
          {score:.0f}<span style="font-size:11px;color:#888;">/100</span>
        </div>
      </div>

      <div style="color:#aaa;font-size:12px;margin:6px 0 2px;">
        <span style="color:#ff6b35;">{bar}</span>
      </div>

      <div style="color:#ccc;font-size:13px;margin:8px 0 4px;">
        📅 {date_str} &nbsp;|&nbsp; 📍 {venue_html(venue, ev.get('address', ''))}
      </div>

      <div style="margin:8px 0 2px;">{chips_html}</div>
      {f'<div style="color:#888;font-size:11px;margin:4px 0;">{genres_str}</div>' if genres_str else ''}

      <div style="color:#888;font-size:11px;margin:8px 0;">
        {"🎵 Spotify: " + format_number(spotify) if spotify else ""}
        {"&nbsp;·&nbsp; 🎛 RA: " + format_number(ra_f) if ra_f else ""}
        {"&nbsp;·&nbsp; ☁️ SoundCloud: " + format_number(sc_f) if sc_f else ""}
      </div>

      <div style="margin-top:10px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
        {ticket_html}
        {f'<span style="color:#888;font-size:12px;">{yt_html}</span>' if yt_html else ''}
      </div>
    </div>
    """


def build_html(events: list) -> str:
    today = datetime.now().strftime("%B %d, %Y")

    # Split by city
    by_city = {}
    for ev in events:
        city = ev.get("city", "unknown")
        by_city.setdefault(city, []).append(ev)

    city_sections = ""
    for city, city_events in by_city.items():
        label = CITY_LABELS.get(city, city.replace("_", " ").title())
        cards = "".join([build_event_card(ev) for ev in city_events])
        city_sections += f"""
        <div style="margin-bottom:32px;">
          <h2 style="color:#ff6b35;border-bottom:1px solid #333;
                     padding-bottom:8px;font-family:monospace;">
            📍 {label} — {len(city_events)} shows
          </h2>
          {cards}
        </div>
        """

    if not city_sections:
        city_sections = """
        <p style="color:#888;text-align:center;padding:40px 0;">
          No house music events found this week. Check back next Monday.
        </p>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="background:#0d0d0d;color:#fff;font-family:monospace;
                 max-width:680px;margin:0 auto;padding:20px;">

      <div style="text-align:center;padding:24px 0 16px;">
        <div style="font-size:28px;font-weight:bold;color:#ff6b35;
                    letter-spacing:2px;">🎛 HOUSE MUSIC RADAR</div>
        <div style="color:#888;font-size:13px;margin-top:4px;">
          Weekly drop · {today} · Next 30 days
        </div>
        <div style="color:#555;font-size:11px;margin-top:4px;">
          Sources: RA · 19hz · DICE · Shotgun · Scenestar · EDMtrain · Songkick
        </div>
      </div>

      <div style="background:#111;border:1px solid #222;border-radius:6px;
                  padding:12px 16px;margin-bottom:24px;font-size:12px;color:#888;">
        🔥🔥🔥 = Top tier (80–100) &nbsp;|&nbsp;
        🔥🔥 = Strong (60–80) &nbsp;|&nbsp;
        🔥 = Solid (40–60) &nbsp;|&nbsp;
        ⚡ = Up & coming (20–40) &nbsp;|&nbsp;
        🎵 = Local/underground (0–20)
      </div>

      {city_sections}

      <div style="text-align:center;color:#444;font-size:11px;
                  padding:24px 0;border-top:1px solid #222;margin-top:16px;">
        House Music Radar · Auto-generated every Monday 8:30am PT<br>
        Scoring: Spotify listeners (50%) + RA followers (30%) + SoundCloud (20%)
      </div>

    </body>
    </html>
    """


def send_email(events: list):
    if not EMAIL_FROM or not EMAIL_PASSWORD:
        print("[Email] No credentials set. Printing digest to console instead.\n")
        print_console_digest(events)
        return

    html = build_html(events)
    today = datetime.now().strftime("%b %d")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎛 House Music Radar — {today}"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    part = MIMEText(html, "html")
    msg.attach(part)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print(f"[Email] Sent to {EMAIL_TO}")
    except Exception as e:
        print(f"[Email] Send failed: {e}")
        print("[Email] Printing digest to console instead.\n")
        print_console_digest(events)


def print_console_digest(events: list):
    """Fallback: prints a simple text digest to terminal."""
    print("\n" + "="*60)
    print("🎛  HOUSE MUSIC RADAR")
    print("="*60)

    by_city = {}
    for ev in events:
        by_city.setdefault(ev.get("city", "unknown"), []).append(ev)

    for city, city_events in by_city.items():
        label = CITY_LABELS.get(city, city)
        print(f"\n📍 {label.upper()} — {len(city_events)} shows\n")
        for ev in city_events:
            artist = ev.get("artist") or ev.get("title") or "Unknown"
            score = ev.get("score", 0)
            date = ev.get("date_str", "")
            venue = ev.get("venue", "")
            url = ev.get("ticket_url", "")
            yt = ev.get("youtube_set_url", "") or (ev.get("youtube_track_urls") or [""])[0]
            print(f"  [{score:.0f}/100] {artist}")
            print(f"         {date} @ {venue}")
            if url:
                print(f"         Tickets: {url}")
            if yt:
                print(f"         YouTube: {yt}")
            print()

    print("="*60 + "\n")


def send_html(subject: str, html: str) -> bool:
    """Send an already-built HTML digest. Returns True if sent."""
    if not (EMAIL_FROM and EMAIL_PASSWORD and EMAIL_TO):
        print("[Email] EMAIL_FROM / EMAIL_PASSWORD / EMAIL_TO not all set. Skipping send.")
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.attach(MIMEText(html, "html"))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print("[Email] Sent.")
        return True
    except Exception as e:
        print(f"[Email] Send failed: {e}")
        return False
