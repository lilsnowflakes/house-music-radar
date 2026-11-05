"""
theme.py - the page color swatch.
All pages are written in one base ramp (turquoise); apply() swaps that ramp for the active theme.
Pick the theme in config/theme.txt (or the RADAR_THEME env var): auto (= mahogany), mahogany, turquoise,
violet, magenta, amber, green, blue, red, outrun, console, or "rotate" for a new color on every run.
"""
import colorsys
import os
import re

BASE = ["#001515", "#00292a", "#003e3f", "#005254", "#007c7d", "#009092", "#00a5a7", "#00b9bc"]
HUES = [("turquoise", 181), ("violet", 262), ("magenta", 322), ("amber", 36),
        ("green", 140), ("blue", 215), ("red", 355)]
# Hand-built palettes (same 8 stops as BASE, dark to bright). "extra" swaps text colors; "css" adds a style block.
RED_FILTER = ('<svg width="0" height="0" style="position:absolute" aria-hidden="true"><filter id="nightred" color-interpolation-filters="sRGB">'
              '<feColorMatrix type="matrix" values="0.28 0.62 0.06 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"/>'
              '<feComponentTransfer><feFuncR type="gamma" amplitude="1" exponent="0.5"/></feComponentTransfer></filter></svg>')

CUSTOM = {
    # Low-light version modeled on dark app dashboards: navy, soft gradients, rounded panels.
    "night": dict(stops=["#0b1630", "#12254a", "#1a3263", "#25407a", "#4a6bb5", "#8fa6d6", "#b4c6ea", "#9a7bff"],
                  extra={"#e6fafa": "#e9f0ff"},
                  css="<style>body{background:linear-gradient(180deg,#0b1630 0%,#10224a 100%) fixed!important}"
                      "details{border-radius:18px!important}a[style*='background:#9a7bff']{background:linear-gradient(90deg,#29b6ff,#9a3cff)!important;color:#fff!important}"
                      "#styles a,div[style*='position:sticky'] a{border-radius:999px!important}</style>"),
    # Pioneer-style DJ deck: black metal, silver print, orange LEDs.
    "deck": dict(stops=["#0d0d0f", "#17181b", "#222428", "#3a3d44", "#6b6f78", "#9aa0ab", "#c3c8d0", "#ff9d1a"],
                 extra={"#e6fafa": "#e8edf5"},
                 css="<style>body{background:repeating-linear-gradient(90deg,#0d0d0f 0 3px,#111215 3px 6px)!important}"
                     "summary{text-transform:uppercase;letter-spacing:1.6px;font-size:13px!important}details{border-radius:6px!important;box-shadow:inset 0 0 0 1px #2a2c31}"
                     "a[style*='background:#ff9d1a']{color:#000!important;font-weight:bold}</style>"),
    # Red on black: low light, protects night vision. Everything is filtered to red only.
    "redline": dict(stops=["#020000", "#140404", "#280808", "#521212", "#8a2222", "#b83434", "#e05a5a", "#ff9080"],
                    extra={}, body=RED_FILTER,
                    css="<style>body{filter:url(#nightred);background:#020000!important}html{background:#000}</style>"),
    # Palette taken from a retro 80s living room photo: mahogany wood, brass, cream walls, burnt-orange rug.
    "mahogany": dict(stops=["#1a0b07", "#2b130b", "#3d1d10", "#6a3418", "#a0663a", "#c9a064", "#e6c79a", "#f0893a"],
                     extra={"#fff": "#fff3e2", "#ccc": "#ead5b8", "#bbb": "#e0c9ab", "#aaa": "#cdb08a", "#e6fafa": "#fff3e2"},
                     css="<style>h2,summary{letter-spacing:.3px}</style>"),
    "outrun": dict(stops=["#0d0221", "#1b0b3a", "#2d1160", "#541388", "#7b2cbf", "#b967ff", "#01cdfe", "#ff71ce"],
                   extra={},
                   css="<style>html{background:#0d0221}body{background:linear-gradient(180deg,#0d0221 0%,#1b0b3a 55%,#3a0f6b 100%) fixed!important}"
                       "h2,summary{text-shadow:0 0 8px rgba(255,113,206,.55)}"
                       "div[style*='letter-spacing:2px']{text-shadow:0 0 6px #ff71ce,0 0 18px #b967ff}</style>"),
    "console": dict(stops=["#000a00", "#001a05", "#003a0c", "#00661a", "#00a82b", "#14cc3c", "#2bea55", "#39ff6a"],
                    extra={"#fff": "#aaffbb", "#ccc": "#5ff58a", "#bbb": "#5ff58a", "#aaa": "#3fd96a"},
                    css="<style>body,body *{text-shadow:0 0 5px rgba(57,255,106,.45)}"
                        "body{background-image:repeating-linear-gradient(0deg,rgba(0,0,0,.25) 0 1px,transparent 1px 3px)!important}"
                        "</style>"),
}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lum(r, g, b):
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _recolor(hexv, hue):
    """Same brightness as the turquoise stop, different hue (so every theme stays readable)."""
    r, g, b = (int(hexv[i:i + 2], 16) / 255 for i in (1, 3, 5))
    target = _lum(r, g, b)
    _, l0, s = colorsys.rgb_to_hls(r, g, b)
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = (lo + hi) / 2
        y = _lum(*colorsys.hls_to_rgb(hue / 360, mid, s))
        lo, hi = (mid, hi) if y < target else (lo, mid)
    r2, g2, b2 = colorsys.hls_to_rgb(hue / 360, (lo + hi) / 2, s)
    return "#{:02x}{:02x}{:02x}".format(round(r2 * 255), round(g2 * 255), round(b2 * 255))


def run_number():
    try:
        return int(os.environ.get("GITHUB_RUN_NUMBER", ""))
    except ValueError:
        return 0


def choose():
    """Returns (theme_name, hue, how) where how is 'auto' or 'set'."""
    want = (os.environ.get("RADAR_THEME") or "").strip().lower()
    if not want:
        try:
            want = open(os.path.join(ROOT, "config", "theme.txt")).read().strip().lower()
        except OSError:
            want = "auto"
    names = dict(HUES)
    if want in names:
        return want, names[want], "set"
    if want in CUSTOM:
        return want, 0, "set"
    if want == "rotate":
        allnames = [n for n, _ in HUES] + list(CUSTOM)
        name = allnames[run_number() % len(allnames)]
        return name, dict(HUES).get(name, 0), "rotate"
    return "mahogany", 0, "auto"


def apply(page, theme=None):
    name, hue, _ = theme or choose()
    if name in CUSTOM:
        c = CUSTOM[name]
        for b, new in zip(BASE, c["stops"]):
            page = re.sub(re.escape(b), "@@" + new[1:], page, flags=re.I)
        page = page.replace("@@", "#")
        for old, new in c["extra"].items():
            page = re.sub(re.escape(old) + r"\b", new, page, flags=re.I)
        if c.get("body"):
            page = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + c["body"], page, count=1)
        return page.replace("</head>", c["css"] + "</head>", 1) if c["css"] else page
    if name == "turquoise":
        return page
    for b in BASE:
        page = re.sub(re.escape(b), _recolor(b, hue), page, flags=re.I)
    return page
