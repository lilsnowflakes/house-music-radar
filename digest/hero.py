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


def night_svg(counts=None):
    """Low-light 'Night' hero: gradient planet with a ring, stars, and a bar chart of shows per day for the next 7 days."""
    import datetime
    counts = counts or [0] * 7
    rnd = random.Random(7)
    W, H = 680, 190
    stars = "".join(f'<circle cx="{rnd.randint(6, W - 6)}" cy="{rnd.randint(6, H - 6)}" r="{rnd.choice([.7, 1, 1.3])}" fill="#cfe0ff" opacity="{rnd.choice([.3, .55, .9])}"/>' for _ in range(46))
    mx = max(counts + [1])
    today = datetime.date.today()
    bars = ""
    for i, n in enumerate(counts):
        h = 10 + 78 * n / mx
        x = 330 + i * 48
        lab = (today + datetime.timedelta(days=i)).strftime("%a")
        bars += (f'<rect x="{x}" y="{150 - h:.1f}" width="26" height="{h:.1f}" rx="6" fill="url(#nbar)"/>'
                 f'<text x="{x + 13}" y="170" text-anchor="middle" font-family="monospace" font-size="11" fill="#8fa6d6">{lab}</text>'
                 f'<text x="{x + 13}" y="{143 - h:.1f}" text-anchor="middle" font-family="monospace" font-size="11" fill="#cfe0ff">{n}</text>')
    return f'''<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Shows per day for the next seven days"
 style="display:block;border-radius:18px;border:1px solid #25407a;background:linear-gradient(160deg,#0b1630,#142a55)">
<defs><linearGradient id="nbar" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#9a3cff"/><stop offset="1" stop-color="#29b6ff"/></linearGradient>
<radialGradient id="nplanet" cx=".3" cy=".3" r=".9"><stop offset="0" stop-color="#29b6ff"/><stop offset=".6" stop-color="#7b3cff"/><stop offset="1" stop-color="#c026ff"/></radialGradient></defs>
{stars}
<ellipse cx="130" cy="96" rx="92" ry="22" fill="none" stroke="#29b6ff" stroke-width="2" transform="rotate(-18 130 96)" opacity=".85"/>
<circle cx="130" cy="96" r="52" fill="url(#nplanet)"/>
<ellipse cx="130" cy="96" rx="92" ry="22" fill="none" stroke="#e9f3ff" stroke-width="2" stroke-dasharray="120 400" stroke-dashoffset="-150" transform="rotate(-18 130 96)"/>
<text x="330" y="30" font-family="monospace" font-size="12" fill="#8fa6d6" letter-spacing="2">SHOWS · NEXT 7 NIGHTS</text>{bars}</svg>'''


def deck_svg(lines=None, seed=0):
    """DJ-controller hero: two spinning jog wheels, a mixer with level meters, and a track-list screen (original art)."""
    rnd = random.Random(seed)
    lines = (lines or ["NO SHOWS LOGGED TONIGHT"])[:5]
    W, H = 680, 250
    rows = ""
    for i, l in enumerate(lines):
        sel = i == 0
        rows += (f'<rect x="238" y="{34 + i * 11}" width="204" height="11" fill="{"#e8edf5" if sel else "none"}"/>'
                 f'<text x="242" y="{43 + i * 11}" font-family="monospace" font-size="8.5" fill="{"#000" if sel else "#cfd6e2"}">{l[:38].replace("&", "&amp;")}</text>')

    def wheel(cx, cy):
        ticks = "".join(f'<line x1="{cx}" y1="{cy - 55}" x2="{cx}" y2="{cy - 50}" stroke="#7b808a" stroke-width="1.2" transform="rotate({a} {cx} {cy})"/>' for a in range(0, 360, 12))
        return f'''<circle cx="{cx}" cy="{cy}" r="66" fill="#15161a" stroke="#2c2e34" stroke-width="2"/>
<circle cx="{cx}" cy="{cy}" r="62" fill="none" stroke="#ff9d1a" stroke-width="2.5" stroke-dasharray="70 320" opacity=".9"><animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="6s" repeatCount="indefinite"/></circle>
<circle cx="{cx}" cy="{cy}" r="56" fill="url(#plat)"/>{ticks}
<circle cx="{cx}" cy="{cy}" r="30" fill="#101114" stroke="#5a5e66" stroke-width="1.5"/>
<circle cx="{cx}" cy="{cy}" r="9" fill="#2a2c31"/>
<g><circle cx="{cx}" cy="{cy - 42}" r="3.2" fill="#ff9d1a"/><animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="6s" repeatCount="indefinite"/></g>'''

    def pads(x):
        return "".join(f'<rect x="{x + i * 34}" y="216" width="28" height="22" rx="3" fill="#0c1220" stroke="#2a7bff" stroke-width="1.6"/>' for i in range(4))

    def meter(x):
        seg = ""
        for k in range(9):
            col = "#2ee06a" if k < 6 else ("#ffb020" if k < 8 else "#ff3b30")
            seg += (f'<rect x="{x}" y="{166 - k * 8}" width="7" height="5" fill="{col}">'
                    f'<animate attributeName="opacity" values="1;{0.25 if k > 3 else 1};1" dur="{0.5 + rnd.random():.2f}s" repeatCount="indefinite"/></rect>')
        return seg

    knobs = "".join(f'<circle cx="{x}" cy="{y}" r="7" fill="#1d1e22" stroke="#6b6f78"/><line x1="{x}" y1="{y}" x2="{x + 3}" y2="{y - 5}" stroke="#e8edf5" stroke-width="1.4"/>'
                    for x in (270, 410) for y in (112, 138, 164))
    faders = "".join(f'<rect x="{x}" y="176" width="3" height="40" fill="#050506"/><rect x="{x - 6}" y="{rnd.randint(180, 204)}" width="15" height="8" rx="2" fill="#cfd3da"/>' for x in (298, 380))
    return f'''<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="DJ controller with two jog wheels and a mixer"
 style="display:block;border-radius:10px;border:1px solid #3a3d44;background:linear-gradient(#1b1c20,#0f1012)">
<defs><radialGradient id="plat" cx=".5" cy=".5" r=".5"><stop offset=".55" stop-color="#2b2d33"/><stop offset="1" stop-color="#4a4d54"/></radialGradient></defs>
<rect x="232" y="10" width="216" height="74" rx="3" fill="#000" stroke="#3a3d44"/>
<rect x="238" y="16" width="204" height="12" fill="#101a2e"/><text x="242" y="25" font-family="monospace" font-size="8" fill="#6fa8ff">[TRACK]  TONIGHT</text>{rows}
<text x="340" y="96" text-anchor="middle" font-family="monospace" font-size="7" fill="#8a8f99" letter-spacing="1.5">BROWSE · TAG LIST · INFO</text>
<circle cx="40" cy="40" r="9" fill="#ff9d1a"/><circle cx="76" cy="40" r="9" fill="#ff9d1a"/><circle cx="604" cy="40" r="9" fill="#ff9d1a"/><circle cx="640" cy="40" r="9" fill="#ff9d1a"/>
<text x="40" y="62" text-anchor="middle" font-family="monospace" font-size="7" fill="#8a8f99">IN</text><text x="76" y="62" text-anchor="middle" font-family="monospace" font-size="7" fill="#8a8f99">OUT</text>
<text x="604" y="62" text-anchor="middle" font-family="monospace" font-size="7" fill="#8a8f99">IN</text><text x="640" y="62" text-anchor="middle" font-family="monospace" font-size="7" fill="#8a8f99">OUT</text>
{wheel(118, 140)}{wheel(562, 140)}{pads(52)}{pads(496)}
<rect x="250" y="104" width="180" height="116" rx="4" fill="none" stroke="#2c2e34"/>{knobs}{faders}{meter(325)}{meter(348)}

<text x="322" y="231" text-anchor="middle" font-family="monospace" font-size="8" fill="#8a8f99">CH1</text><text x="358" y="231" text-anchor="middle" font-family="monospace" font-size="8" fill="#8a8f99">CH2</text></svg>'''


def radar_svg(n=0):
    """Redline hero: a radar sweep over LA with blips (one per show tonight)."""
    rnd = random.Random(n)
    W, H = 680, 200
    cx, cy = 340, 100
    rings = "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#005254" stroke-width="1"/>' for r in (30, 60, 90))
    blips = "".join(f'<circle cx="{cx + rnd.randint(-230, 230)}" cy="{cy + rnd.randint(-70, 70)}" r="3.5" fill="#00b9bc">'
                    f'<animate attributeName="opacity" values="1;.2;1" dur="{1.2 + i * .23:.2f}s" repeatCount="indefinite"/></circle>' for i in range(max(n, 5)))
    return f'''<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Radar sweep"
 style="display:block;border-radius:10px;border:1px solid #005254;background:#001515">
<defs><linearGradient id="sw" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#00b9bc" stop-opacity="0"/><stop offset="1" stop-color="#00b9bc" stop-opacity=".55"/></linearGradient></defs>
<line x1="0" y1="{cy}" x2="{W}" y2="{cy}" stroke="#003e3f"/><line x1="{cx}" y1="0" x2="{cx}" y2="{H}" stroke="#003e3f"/>{rings}
<g><path d="M{cx} {cy} L{cx + 100} {cy - 24} A103 103 0 0 1 {cx + 100} {cy + 24} Z" fill="url(#sw)"/>
<line x1="{cx}" y1="{cy}" x2="{cx + 103}" y2="{cy}" stroke="#00b9bc" stroke-width="2"/>
<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="5s" repeatCount="indefinite"/></g>{blips}
<text x="16" y="24" font-family="monospace" font-size="12" fill="#00a5a7" letter-spacing="3">SCANNING LOS ANGELES</text>
<text x="664" y="24" text-anchor="end" font-family="monospace" font-size="12" fill="#00a5a7" letter-spacing="2">{n} TONIGHT</text></svg>'''
