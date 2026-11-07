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

# Minimal style: black on white while the sun is up in Los Angeles, white on black from sunset to sunrise.
# Worked out in the visitor's browser from LA's coordinates (standard sunrise equation), checked every 5 minutes.
MINIMAL_SUN_JS = """<script>(function(){
 function sun(t){var r=Math.PI/180,lat=34.05,lng=-118.24,JD=t/864e5+2440587.5,n=Math.round(JD-2451545+lng/360),
  J=n-lng/360,M=(357.5291+.98560028*J)%360,C=1.9148*Math.sin(M*r)+.02*Math.sin(2*M*r)+.0003*Math.sin(3*M*r),
  L=(M+C+282.9372)%360,Jt=2451545+J+.0053*Math.sin(M*r)-.0069*Math.sin(2*L*r),
  sd=Math.sin(L*r)*Math.sin(23.4397*r),cd=Math.cos(Math.asin(sd)),
  w=Math.acos((Math.sin(-.833*r)-Math.sin(lat*r)*sd)/(Math.cos(lat*r)*cd))/r,ms=function(j){return(j-2440587.5)*864e5;};
  return[ms(Jt-w/360),ms(Jt+w/360)];}
 function set(){var t=Date.now(),s=sun(t),night=t<s[0]||t>s[1];
  document.documentElement.classList.toggle('mnight',night);
  var m=document.querySelector('meta[name=theme-color]');if(m)m.content=night?'#000000':'#ffffff';}
 set();setInterval(set,3e5);
})();</script>"""

CUSTOM = {
    # Minimal: black, white and gray only. Everything colored (chips, photos, drawings) is turned to grayscale,
    # and the YouTube / Spotify / SoundCloud icons are hidden.
    "minimal": dict(stops=["#ffffff", "#f5f5f5", "#e2e2e2", "#cccccc", "#8c8c8c", "#6b6b6b", "#4d4d4d", "#111111"],
                    extra={"#fff": "#111", "#ccc": "#444", "#bbb": "#4d4d4d", "#aaa": "#5c5c5c", "#e6fafa": "#111"},
                    light_chips=True,
                    css="<style>:root{color-scheme:light}html{background:#fff}"
                        "body{background:#fff!important;color:#111;"
                        "font-family:'Helvetica Neue',Helvetica,ui-sans-serif,-apple-system,'Segoe UI',Arial,sans-serif!important}"
                        ".ml,.mlinks{display:none!important}"
                        "body>*:not(#pf):not(#lb),#pf img,#lb img{filter:grayscale(1)}"
                        ".evrow,details.sec,.spot,.hlcard{border-radius:2px!important;box-shadow:none!important;font-family:inherit!important}"
                        ".evrow{border-width:0 0 1px 0!important;background:#fff!important;padding-left:0!important;padding-right:0!important}"
                        ".tix,.hlcard a[style*='background:#111111']{background:#111!important;color:#fff!important}"
                        ".fchip[aria-pressed=true]{background:#111!important;color:#fff!important}"
                        "div[style*='letter-spacing:2px'],details.sec>summary{letter-spacing:1.5px!important;font-weight:500!important;font-family:inherit!important}"
                        # after LA sunset everything flips to white on black (photos flip back so they look normal)
                        "html.mnight,html.mnight body{background:#000!important}"
                        "html.mnight body>*:not(#pf):not(#lb){filter:grayscale(1) invert(1)}"
                        "html.mnight body>*:not(#pf):not(#lb) img{filter:invert(1)}"
                        "</style>" + MINIMAL_SUN_JS),
    # You Look Amazing (Burning Man camp): sand and cream, Tulum turquoise, sunset gold. A light, boho style.
    "yla": dict(stops=["#f4eadb", "#fbf6ee", "#e9dcc5", "#d8c3a0", "#9b8467", "#8b7357", "#7a6248", "#127f7c"],
                extra={"#fff": "#3a2c20", "#ccc": "#5c4a39", "#bbb": "#5c4a39", "#aaa": "#6b5845", "#e6fafa": "#3a2c20"},
                light_chips=True,
                css="<style>:root{color-scheme:light}html{background:#f4eadb}"
                    "body{background:linear-gradient(180deg,#f7efe2 0%,#f1e3cc 100%) fixed!important;"
                    "font-family:ui-sans-serif,-apple-system,'Segoe UI',Roboto,sans-serif!important}"
                    "div[style*='letter-spacing:2px'],details.sec>summary,.dl,#highlight div[style*='font-size:22px']"
                    "{font-family:Georgia,'Times New Roman',serif!important;letter-spacing:.5px}"
                    ".evrow,details.sec,.spot{box-shadow:0 1px 0 #fff inset,0 6px 18px rgba(120,90,50,.08);border-radius:14px!important;font-family:inherit!important}"
                    ".tix,.hlcard a[style*='background:#127f7c']{background:linear-gradient(90deg,#127f7c,#1aa39f)!important;color:#fffaf2!important}"
                    ".hlcard{background:linear-gradient(135deg,#fffaf2,#f6e7cf)!important;border-color:#c9962e!important}"
                    ".fchip[aria-pressed=true]{background:#127f7c!important;color:#fffaf2!important}</style>"),
    # 2026 futuristic: glass panels, iridescent edges, ice-cyan accents, clean sans type.
    "holo": dict(stops=["#05070d", "#0b1120", "#111a30", "#22304f", "#3f5680", "#7f93bd", "#a9bbe0", "#7cf5ff"],
                 extra={"#e6fafa": "#eaf6ff"},
                 css="<style>body{background:radial-gradient(90% 60% at 50% 0%,#101a33 0%,#05070d 70%) fixed!important;"
                     "font-family:ui-sans-serif,-apple-system,'SF Pro Text','Segoe UI',Inter,Roboto,sans-serif!important}"
                     ".evrow,details.sec{background:rgba(255,255,255,.035)!important;backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);"
                     "border-color:rgba(124,245,255,.16)!important;font-family:inherit!important;border-radius:14px!important}"
                     "details.sec>summary{font-family:inherit!important;letter-spacing:.4px}"
                     "#highlight,#highlight-next{border:1px solid transparent!important;background:linear-gradient(#0b1120,#0b1120) padding-box,"
                     "conic-gradient(from 200deg,#7cf5ff,#b58cff,#ff8ad8,#ffd27a,#7cf5ff) border-box!important;font-family:inherit!important}"
                     ".tix,.hlcard a[style*='background:#7cf5ff']{background:linear-gradient(90deg,#7cf5ff,#b58cff)!important;color:#05070d!important;font-weight:600}"
                     ".fchip[aria-pressed=true]{background:linear-gradient(90deg,#7cf5ff,#b58cff)!important;border-color:transparent!important}"
                     ".sc{font-variant-numeric:tabular-nums}"
                     # Tron glow: the teal letters get the same pink neon halo as Outrun
                     "h1,h2,details.sec>summary,div[style*='letter-spacing:2px'],.sc"
                     "{text-shadow:0 0 6px rgba(255,113,206,.75),0 0 16px rgba(181,140,255,.45)}</style>"),
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
        if c.get("light_chips"):
            from digest.colors import to_light_chips
            page = to_light_chips(page)
        if c.get("body"):
            page = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + c["body"], page, count=1)
        return page.replace("</head>", c["css"] + "</head>", 1) if c["css"] else page
    if name == "turquoise":
        return page
    for b in BASE:
        page = re.sub(re.escape(b), _recolor(b, hue), page, flags=re.I)
    return page
