"""
ogimage.py - the picture that shows up when someone shares the site in Messages, WhatsApp, IG DMs, etc.

Builds docs/og.jpg (1200x630, under ~150KB, the size those apps expect) from a small HTML card using the
same headless browser the radar already installs, and returns the <meta> tags that point to it.
The card says what's on: tonight's count and the Highlight, so a shared link tells people why to tap.
"""
import html
import re
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "og.jpg")
e = html.escape


def image_name(style="classic"):
    return "og.jpg" if style == "classic" else f"og-{style}.jpg"


def _card_html(headline, sub, stamp, hero):
    """Written in the base colors (#001515 background, #fff text, #00b9bc accent); each style's palette is
    swapped in afterwards by theme.apply, exactly like the pages."""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;box-sizing:border-box}}
body{{width:1200px;height:630px;background:#001515;color:#fff;font-family:'DejaVu Sans',Arial,sans-serif;overflow:hidden;position:relative}}
.hero{{position:absolute;left:0;right:0;bottom:12px;height:340px;
 -webkit-mask-image:linear-gradient(to bottom,transparent 0,#000 26%);mask-image:linear-gradient(to bottom,transparent 0,#000 26%)}}
.hero svg{{display:block;width:1200px;height:340px;border:0!important;border-radius:0!important}}
.txt{{position:absolute;left:64px;top:46px;right:64px}}
.k{{font:700 20px 'DejaVu Sans Mono',monospace;letter-spacing:6px;color:#00b9bc}}
h1{{font-size:62px;line-height:1.05;margin-top:10px;font-weight:800;white-space:nowrap}}
.h{{margin-top:20px;font-size:32px;font-weight:700}}.s{{margin-top:8px;font-size:25px;color:#00a5a7}}
.f{{margin-top:10px;font:18px 'DejaVu Sans Mono',monospace;color:#009092}}
.bar{{position:absolute;left:0;right:0;bottom:0;height:12px;background:#00b9bc}}
</style></head><body><div class="hero">{hero}</div>
<div class="txt"><div class="k">LOS ANGELES · HOUSE</div><h1>Mo's House Music Radar</h1>
<div class="h">{e(headline)}</div><div class="s">{e(sub)}</div><div class="f">{e(stamp)}</div></div>
<div class="bar"></div></body></html>"""


RUG = '<div style="position:absolute;left:0;right:0;bottom:0;height:12px;background:linear-gradient(90deg,#b8451f 0 22%,#d9772b 22% 44%,#7d7a2c 44% 66%,#e8d2a6 66% 84%,#6a3418 84%)"></div>'


def build_all(events, highlight, now, styles, run_no=0):
    """One share image per style (docs/og.jpg for Classic, docs/og-<style>.jpg for the rest), each with
    that style's own picture and colors. Returns how many were made."""
    from digest import theme
    from digest.dates import day_label
    from digest.render import make_hero, group_events
    groups = group_events(events, now)
    tonight, total = len(groups["tonight"]), sum(len(v) for v in groups.values())
    if highlight:
        who = highlight.get("artist") or highlight.get("title") or ""
        where = highlight.get("venue") or "venue TBA"
        sub = f"★ {who} · {where} · {day_label(highlight.get('date_str', ''))}"
    else:
        sub = "Every house night in LA, updated twice a day"
    headline = (f"{tonight} house shows tonight" if tonight else "Tonight, this week and what's next") \
        + (f" · {total} upcoming" if total else "")
    stamp = now.strftime("Updated %a %b %-d · lilsnowflakes.github.io/house-music-radar")
    made = 0
    try:
        from playwright.sync_api import sync_playwright
        from PIL import Image
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1200, "height": 630})
            for style in styles:
                th = theme.choose() if style == "classic" else (style, 0, "set")
                # wide band along the bottom; tall pictures (deck, console) are cropped around their middle
                align = "xMidYMid slice" if th[0] in ("deck", "console", "holo") else "xMidYMax slice"
                hero = make_hero(th[0], events, groups, now, run_no).replace("<svg ", f'<svg preserveAspectRatio="{align}" ', 1)
                if th[0] == "minimal":   # the card already says it; drop the drawing's own labels
                    hero = re.sub(r"<text\b.*?</text>", "", hero, flags=re.S)
                html_ = _card_html(headline, sub, stamp, hero)
                if th[0] == "mahogany":
                    html_ = html_.replace('<div class="bar"></div>', RUG)
                pg.set_content(theme.apply(html_, th))
                pg.wait_for_timeout(120)
                png = os.path.join(os.path.dirname(OUT), "_og.png")
                pg.screenshot(path=png)
                Image.open(png).convert("RGB").save(os.path.join(os.path.dirname(OUT), image_name(style)),
                                                   "JPEG", quality=84, optimize=True, progressive=True)
                os.remove(png)
                made += 1
            b.close()
    except Exception as ex:
        print(f"  share images: {made} made, then stopped: {ex}")
    return made


def meta_tags(site_url, title, description, page_path="", version="", image="og.jpg"):
    """Open Graph + Twitter tags. The ?v= changes daily so apps don't keep showing an old picture."""
    if not site_url:
        return ""
    base = site_url if site_url.endswith("/") else site_url + "/"
    img = f"{base}{image}?v={version}"
    return (f'<meta property="og:type" content="website"><meta property="og:site_name" content="Mo\'s House Music Radar">'
            f'<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}">'
            f'<meta property="og:url" content="{e(base + page_path)}"><meta property="og:image" content="{e(img)}">'
            f'<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
            f'<meta property="og:image:alt" content="Mo\'s House Music Radar: house music in Los Angeles tonight">'
            f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{e(img)}">'
            f'<meta name="description" content="{e(description)}">')
