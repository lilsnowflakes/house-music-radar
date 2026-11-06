"""
ogimage.py - the picture that shows up when someone shares the site in Messages, WhatsApp, IG DMs, etc.

Builds docs/og.jpg (1200x630, under ~150KB, the size those apps expect) from a small HTML card using the
same headless browser the radar already installs, and returns the <meta> tags that point to it.
The card says what's on: tonight's count and the Highlight, so a shared link tells people why to tap.
"""
import html
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "og.jpg")
e = html.escape


def _card_html(headline, sub, stamp, hero_svg):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;box-sizing:border-box}}
body{{width:1200px;height:630px;background:#1a0b07;color:#fff3e2;font-family:'DejaVu Sans',Arial,sans-serif;overflow:hidden;position:relative}}
.hero{{position:absolute;inset:0}}.hero svg{{width:1200px;height:630px;border:0!important;border-radius:0!important}}
.fade{{position:absolute;inset:0;background:linear-gradient(90deg,#1a0b07f5 0%,#1a0b07d9 40%,#1a0b0740 72%,#1a0b0700 100%)}}
.txt{{position:absolute;left:64px;top:70px;right:420px}}
.k{{font:700 22px 'DejaVu Sans Mono',monospace;letter-spacing:6px;color:#f0893a}}
h1{{font-size:68px;line-height:1.02;margin-top:14px;font-weight:800}}
.h{{margin-top:34px;font-size:34px;font-weight:700}}.s{{margin-top:10px;font-size:26px;color:#e6c79a}}
.f{{position:absolute;left:64px;bottom:48px;font:22px 'DejaVu Sans Mono',monospace;color:#c9a064}}
.bar{{position:absolute;left:0;right:0;bottom:0;height:12px;
 background:linear-gradient(90deg,#b8451f 0 22%,#d9772b 22% 44%,#7d7a2c 44% 66%,#e8d2a6 66% 84%,#6a3418 84%)}}
</style></head><body><div class="hero">{hero_svg}</div><div class="fade"></div>
<div class="txt"><div class="k">LOS ANGELES · HOUSE</div><h1>Mo's House<br>Music Radar</h1>
<div class="h">{e(headline)}</div><div class="s">{e(sub)}</div></div>
<div class="f">{e(stamp)}</div><div class="bar"></div></body></html>"""


def build(tonight_count, total, highlight, now):
    """Writes docs/og.jpg. Returns True if it worked."""
    from digest.hero import hero_svg
    from digest import theme
    from digest.dates import day_label
    if highlight:
        who = highlight.get("artist") or highlight.get("title") or ""
        where = highlight.get("venue") or "venue TBA"
        sub = f"★ {who} · {where} · {day_label(highlight.get('date_str', ''))}"
    else:
        sub = "Every house night in LA, updated twice a day"
    headline = (f"{tonight_count} house shows tonight" if tonight_count else "Tonight, this week and what's next") \
        + (f" · {total} upcoming" if total else "")
    page = theme.apply(_card_html(headline, sub, now.strftime("Updated %a %b %-d · lilsnowflakes.github.io/house-music-radar"),
                                  hero_svg(7).replace("<svg ", '<svg preserveAspectRatio="xMaxYMax slice" ', 1)), ("mahogany", 0, "set"))
    try:
        from playwright.sync_api import sync_playwright
        from PIL import Image
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        png = OUT.replace(".jpg", ".png")
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1200, "height": 630})
            pg.set_content(page)
            pg.wait_for_timeout(150)
            pg.screenshot(path=png)
            b.close()
        Image.open(png).convert("RGB").save(OUT, "JPEG", quality=84, optimize=True, progressive=True)
        os.remove(png)
        return True
    except Exception as ex:
        print(f"  share image not made: {ex}")
        return False


def meta_tags(site_url, title, description, page_path="", version=""):
    """Open Graph + Twitter tags. The ?v= changes daily so apps don't keep showing an old picture."""
    if not site_url:
        return ""
    base = site_url if site_url.endswith("/") else site_url + "/"
    img = f"{base}og.jpg?v={version}"
    return (f'<meta property="og:type" content="website"><meta property="og:site_name" content="Mo\'s House Music Radar">'
            f'<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}">'
            f'<meta property="og:url" content="{e(base + page_path)}"><meta property="og:image" content="{e(img)}">'
            f'<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
            f'<meta property="og:image:alt" content="Mo\'s House Music Radar: house music in Los Angeles tonight">'
            f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{e(img)}">'
            f'<meta name="description" content="{e(description)}">')
