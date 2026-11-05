"""
theme.py - the page color swatch.
All pages are written in one base ramp (turquoise); apply() swaps that ramp for the active theme.
Pick the theme in config/theme.txt (or the RADAR_THEME env var): auto, turquoise, violet, magenta,
amber, green, blue, red. "auto" rotates to the next color on every run (by the run number).
"""
import colorsys
import os
import re

BASE = ["#001515", "#00292a", "#003e3f", "#005254", "#007c7d", "#009092", "#00a5a7", "#00b9bc"]
HUES = [("turquoise", 181), ("violet", 262), ("magenta", 322), ("amber", 36),
        ("green", 140), ("blue", 215), ("red", 355)]
# Hand-built palettes (same 8 stops as BASE, dark to bright). "extra" swaps text colors; "css" adds a style block.
CUSTOM = {
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
    allnames = [n for n, _ in HUES] + list(CUSTOM)
    name = allnames[run_number() % len(allnames)]
    return name, dict(HUES).get(name, 0), "auto"


def apply(page, theme=None):
    name, hue, _ = theme or choose()
    if name in CUSTOM:
        c = CUSTOM[name]
        for b, new in zip(BASE, c["stops"]):
            page = re.sub(re.escape(b), "@@" + new[1:], page, flags=re.I)
        page = page.replace("@@", "#")
        for old, new in c["extra"].items():
            page = re.sub(re.escape(old) + r"\b", new, page, flags=re.I)
        return page.replace("</head>", c["css"] + "</head>", 1) if c["css"] else page
    if name == "turquoise":
        return page
    for b in BASE:
        page = re.sub(re.escape(b), _recolor(b, hue), page, flags=re.I)
    return page
