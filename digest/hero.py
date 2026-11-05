"""hero.py - the picture at the top of the page: an LA sunset, skyline, palms and an equalizer (inline SVG)."""
import random


def hero_svg(seed=0):
    rnd = random.Random(seed)
    W, H = 680, 170
    bars = "".join(
        f'<rect x="{8 + i * 14}" y="{H - 8 - h}" width="9" height="{h}" rx="2" fill="#00b9bc" opacity="{0.4 + (h / 60)}">'
        f'<animate attributeName="height" values="{h};{max(5, h - 9)};{h}" dur="{0.8 + (i % 5) * 0.17:.2f}s" repeatCount="indefinite"/>'
        f'<animate attributeName="y" values="{H - 8 - h};{H - 8 - max(5, h - 9)};{H - 8 - h}" dur="{0.8 + (i % 5) * 0.17:.2f}s" repeatCount="indefinite"/></rect>'
        for i, h in enumerate(rnd.randint(10, 30) for _ in range(48)))
    skyline = "".join(
        f'<rect x="{x}" y="{H - 40 - h}" width="{w}" height="{h + 40}" fill="#001515"/>'
        for x, w, h in [(250, 22, 38), (276, 16, 62), (296, 26, 30), (326, 18, 78), (348, 24, 44), (376, 20, 54), (400, 28, 26)])
    palm = lambda x, s: (f'<g transform="translate({x} {H - 40}) scale({s})" fill="#001515">'
                         '<path d="M0 0 C2 -30 3 -50 1 -76 L5 -76 C4 -50 5 -30 8 0Z"/>'
                         '<path d="M3 -76 C-14 -88 -30 -80 -38 -66 C-24 -78 -12 -78 3 -72Z"/>'
                         '<path d="M3 -76 C20 -92 38 -84 44 -68 C30 -80 16 -80 3 -72Z"/>'
                         '<path d="M3 -76 C-4 -96 6 -108 16 -112 C8 -100 6 -90 5 -76Z"/></g>')
    stripes = "".join(f'<rect x="130" y="{70 + k * 11}" width="140" height="{2 + k}" fill="#003e3f"/>' for k in range(5))
    return f'''<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Los Angeles sunset skyline with an equalizer"
 style="display:block;border-radius:10px;border:1px solid #005254;background:linear-gradient(#001515,#00292a 70%,#003e3f)">
<circle cx="200" cy="78" r="58" fill="#00b9bc" opacity=".9"/>{stripes}
<rect x="0" y="{H - 40}" width="{W}" height="40" fill="#001515"/>
{skyline}{palm(70, 1.0)}{palm(112, .75)}{palm(560, 1.1)}{palm(606, .8)}
{bars}</svg>'''


def vapor_svg(seed=0):
    """Vaporwave / outrun hero: striped gradient sun, neon perspective grid, palms, katakana."""
    rnd = random.Random(seed)
    W, H, HZ = 680, 200, 128
    stars = "".join(f'<circle cx="{rnd.randint(8, W - 8)}" cy="{rnd.randint(6, 80)}" r="{rnd.choice([.8, 1, 1.4])}" '
                    f'fill="#fffb96" opacity="{rnd.choice([.4, .7, 1])}"/>' for _ in range(34))
    slits = "".join(f'<rect x="250" y="{HZ - 40 + k * 9}" width="180" height="{2 + k * 1.2:.1f}" fill="#241046"/>' for k in range(5))
    vlines = "".join(f'<line x1="340" y1="{HZ}" x2="{340 + dx}" y2="{H}" />' for dx in range(-900, 901, 90))
    hlines = "".join(f'<line x1="0" y1="{y:.1f}" x2="{W}" y2="{y:.1f}"/>'
                     for y in [HZ + 4 * (1.55 ** k) for k in range(1, 9) if HZ + 4 * (1.55 ** k) < H])
    palm = lambda x, s: (f'<g transform="translate({x} {HZ}) scale({s})" fill="#0b0220">'
                         '<path d="M0 0 C2 -30 3 -50 1 -76 L5 -76 C4 -50 5 -30 8 0Z"/>'
                         '<path d="M3 -76 C-14 -88 -30 -80 -38 -66 C-24 -78 -12 -78 3 -72Z"/>'
                         '<path d="M3 -76 C20 -92 38 -84 44 -68 C30 -80 16 -80 3 -72Z"/>'
                         '<path d="M3 -76 C-4 -96 6 -108 16 -112 C8 -100 6 -90 5 -76Z"/></g>')
    return f'''<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Vaporwave sunset over a neon grid"
 style="display:block;border-radius:10px;border:1px solid #b967ff">
<defs>
<linearGradient id="vsky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#12032e"/><stop offset=".6" stop-color="#5a189a"/><stop offset="1" stop-color="#ff71ce"/></linearGradient>
<linearGradient id="vsun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fffb96"/><stop offset=".55" stop-color="#ff9ee5"/><stop offset="1" stop-color="#ff2a9d"/></linearGradient>
<filter id="vglow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<rect width="{W}" height="{HZ}" fill="url(#vsky)"/>{stars}
<circle cx="340" cy="{HZ - 4}" r="70" fill="url(#vsun)" filter="url(#vglow)"/>{slits}
<rect y="{HZ}" width="{W}" height="{H - HZ}" fill="#0b0220"/>
<g stroke="#01cdfe" stroke-width="1.3" opacity=".9" filter="url(#vglow)" clip-path="url(#vclip)">{vlines}{hlines}</g>
<clipPath id="vclip"><rect y="{HZ}" width="{W}" height="{H - HZ}"/></clipPath>
<line x1="0" y1="{HZ}" x2="{W}" y2="{HZ}" stroke="#ff71ce" stroke-width="2" filter="url(#vglow)"/>
{palm(60, 1.05)}{palm(104, .72)}{palm(590, 1.1)}{palm(636, .78)}
<text x="18" y="26" font-family="monospace" font-size="15" fill="#01cdfe" filter="url(#vglow)" letter-spacing="3">ハウス ミュージック</text>
<text x="662" y="26" text-anchor="end" font-family="monospace" font-size="12" fill="#ff71ce" filter="url(#vglow)" letter-spacing="4">L . A .  1 9 8 6</text>
</svg>'''


def console_svg(seed=0, tonight=0, total=0):
    """80s computer console hero: green phosphor screen, boot text, blinking cursor."""
    lines = [
        "MO'S HOUSE MUSIC RADAR  V" + __import__("config.config", fromlist=["x"]).CODE_VERSION,
        "COPYRIGHT 1986 BIG DOG SYSTEMS",
        "",
        '> LOAD "19HZ",8,1 ............ OK',
        '> LOAD "VENUES",8,1 .......... OK',
        "> RUN HOUSE.SCAN",
        f"> {total} SHOWS FOUND  {tonight} TONIGHT",
        "> READY.",
    ]
    ys = [38 + i * 19 for i in range(len(lines))]
    txt = "".join(
        f'<text x="26" y="{y}" fill="#39ff6a" font-family="monospace" font-size="14" opacity="0">'
        f'{l.replace("&", "&amp;")}<animate attributeName="opacity" from="0" to="1" begin="{0.35 * i:.2f}s" dur="0.01s" fill="freeze"/></text>'
        for i, (l, y) in enumerate(zip(lines, ys)) if l)
    cur_y = ys[-1] - 12
    return f'''<svg viewBox="0 0 680 200" width="100%" role="img" aria-label="Retro green terminal boot screen"
 style="display:block;border-radius:14px;border:3px solid #1d3b24;background:#000500">
<defs><filter id="cglow"><feGaussianBlur stdDeviation="1.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1.4" fill="#000" opacity=".35"/></pattern>
<radialGradient id="vig" cx=".5" cy=".5" r=".75"><stop offset=".6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".7"/></radialGradient></defs>
<g filter="url(#cglow)">{txt}
<rect x="{26 + 7.9 * 8}" y="{cur_y}" width="9" height="15" fill="#39ff6a"><animate attributeName="opacity" values="1;1;0;0" dur="1s" repeatCount="indefinite"/></rect></g>
<rect width="680" height="200" fill="url(#scan)"/><rect width="680" height="200" fill="url(#vig)"/></svg>'''
