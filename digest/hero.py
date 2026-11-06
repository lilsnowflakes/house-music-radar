"""hero.py - the picture at the top of the page: an LA sunset, skyline, palms and an equalizer (inline SVG)."""
import random


def hero_svg(seed=0):
    """Classic: LA at dusk. A lighter sky so the skyline reads, two layers of towers with windows that
    twinkle on and off, red rooftop beacons, the striped sun, palms and the equalizer."""
    rnd = random.Random(seed)
    W, H, G = 680, 170, 130          # G = ground line
    bars = "".join(
        f'<rect x="{8 + i * 14}" y="{H - 8 - h}" width="9" height="{h}" rx="2" fill="#00b9bc" opacity="{0.4 + (h / 60)}">'
        f'<animate attributeName="height" values="{h};{max(5, h - 9)};{h}" dur="{0.8 + (i % 5) * 0.17:.2f}s" repeatCount="indefinite"/>'
        f'<animate attributeName="y" values="{H - 8 - h};{H - 8 - max(5, h - 9)};{H - 8 - h}" dur="{0.8 + (i % 5) * 0.17:.2f}s" repeatCount="indefinite"/></rect>'
        for i, h in enumerate(rnd.randint(10, 30) for _ in range(48)))
    stars = "".join(f'<circle cx="{rnd.randint(5, W - 5)}" cy="{rnd.randint(4, 60)}" r="{rnd.choice([.6, .8, 1])}" fill="#e6c79a" '
                    f'opacity="{rnd.choice([.25, .4, .6])}"><animate attributeName="opacity" values=".15;.7;.15" '
                    f'dur="{rnd.uniform(2.5, 6):.1f}s" begin="-{rnd.uniform(0, 5):.1f}s" repeatCount="indefinite"/></circle>'
                    for _ in range(26))
    back = [(232, 18, 46), (252, 14, 58), (268, 20, 40), (300, 12, 70), (318, 22, 52), (352, 16, 64), (372, 26, 36),
            (420, 18, 50), (440, 14, 42), (458, 22, 30)]
    front = [(250, 22, 38), (276, 16, 62), (296, 26, 30), (326, 18, 82), (348, 24, 44), (376, 20, 56), (400, 28, 26), (432, 16, 34)]
    sky_back = "".join(f'<rect x="{x}" y="{G - h}" width="{w}" height="{h}" fill="#003e3f"/>' for x, w, h in back)
    sky_front = "".join(f'<rect x="{x}" y="{G - h}" width="{w}" height="{h}" fill="#001515"/>' for x, w, h in front)
    win = ""
    for x, w, h in front:
        for wx in range(x + 3, x + w - 3, 5):
            for wy in range(G - h + 5, G - 4, 6):
                if rnd.random() < .30:
                    on, d = rnd.choice([1, 1, .2]), rnd.uniform(3, 11)
                    win += (f'<rect x="{wx}" y="{wy}" width="2" height="2.4" fill="#ffd9a0" opacity="{on}">'
                            f'<animate attributeName="opacity" values="{on};{on};.08;{on}" keyTimes="0;.7;.8;1" dur="{d:.1f}s" '
                            f'begin="-{rnd.uniform(0, d):.1f}s" repeatCount="indefinite"/></rect>')
    beacons = "".join(f'<circle cx="{x + w / 2}" cy="{G - h - 2}" r="1.6" fill="#ff4a3d"><animate attributeName="opacity" '
                      f'values="1;.1;1" dur="1.6s" begin="-{i * .5:.1f}s" repeatCount="indefinite"/></circle>'
                      for i, (x, w, h) in enumerate(sorted(front, key=lambda t: -t[2])[:3]))
    palm = lambda x, s: (f'<g transform="translate({x} {G}) scale({s})" fill="#001515">'
                         '<path d="M0 0 C2 -30 3 -50 1 -76 L5 -76 C4 -50 5 -30 8 0Z"/>'
                         '<path d="M3 -76 C-14 -88 -30 -80 -38 -66 C-24 -78 -12 -78 3 -72Z"/>'
                         '<path d="M3 -76 C20 -92 38 -84 44 -68 C30 -80 16 -80 3 -72Z"/>'
                         '<path d="M3 -76 C-4 -96 6 -108 16 -112 C8 -100 6 -90 5 -76Z"/></g>')
    cuts = "".join(f'<rect x="130" y="{78 + k * 9}" width="140" height="{1.6 + k * .9:.1f}" fill="#000"/>' for k in range(5))
    return f'''<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Los Angeles at dusk: skyline with twinkling windows, sun and equalizer"
 style="display:block;border-radius:10px;border:1px solid #005254;background:linear-gradient(#00292a 0%,#005254 62%,#007c7d 78%,#005254 100%)">
<defs><mask id="sunm"><rect width="{W}" height="{H}" fill="#fff"/>{cuts}</mask></defs>
<g data-d="1">{stars}</g>
<g data-d="6"><circle cx="200" cy="80" r="56" fill="#00b9bc" mask="url(#sunm)"/></g>
<g data-d="3">{sky_back}</g>
<rect x="-20" y="{G}" width="{W + 40}" height="{H - G}" fill="#001515"/>
<g data-d="2">{sky_front}{win}{beacons}</g>
<g data-d="10">{palm(70, 1.0)}{palm(112, .75)}{palm(560, 1.1)}{palm(606, .8)}</g>
<g data-d="1">{bars}</g></svg>'''


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
<rect x="-20" width="{W + 40}" height="{HZ}" fill="url(#vsky)"/><g data-d="2">{stars}</g>
<g data-d="6"><circle cx="340" cy="{HZ - 4}" r="70" fill="url(#vsun)" filter="url(#vglow)"/>{slits}</g>
<rect y="{HZ}" width="{W}" height="{H - HZ}" fill="#0b0220"/>
<g stroke="#01cdfe" stroke-width="1.3" opacity=".9" filter="url(#vglow)" clip-path="url(#vclip)">{vlines}{hlines}</g>
<clipPath id="vclip"><rect y="{HZ}" width="{W}" height="{H - HZ}"/></clipPath>
<line x1="0" y1="{HZ}" x2="{W}" y2="{HZ}" stroke="#ff71ce" stroke-width="2" filter="url(#vglow)"/>
<g data-d="10">{palm(60, 1.05)}{palm(104, .72)}{palm(590, 1.1)}{palm(636, .78)}</g>
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


def searchlights(W=680, H=190):
    """Hollywood premiere searchlights: soft beams swinging across the sky from below the skyline."""
    out = ""
    for i, (x, a0, a1, dur) in enumerate([(250, -32, 18, 11), (300, 24, -20, 13), (640, -12, 28, 9.5)]):
        out += (f'<g><polygon points="{x - 5},{H} {x + 5},{H} {x + 38},-20 {x - 38},-20" fill="url(#beam)"/>'
                f'<animateTransform attributeName="transform" type="rotate" values="{a0} {x} {H};{a1} {x} {H};{a0} {x} {H}" '
                f'dur="{dur}s" begin="-{i * 3}s" repeatCount="indefinite" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/></g>')
    return out


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
<linearGradient id="beam" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#e9f3ff" stop-opacity=".55"/>
<stop offset=".55" stop-color="#cfe0ff" stop-opacity=".16"/><stop offset="1" stop-color="#cfe0ff" stop-opacity="0"/></linearGradient>
<radialGradient id="nplanet" cx=".3" cy=".3" r=".9"><stop offset="0" stop-color="#29b6ff"/><stop offset=".6" stop-color="#7b3cff"/><stop offset="1" stop-color="#c026ff"/></radialGradient></defs>
<g data-d="2">{stars}</g><g data-d="4">{searchlights(W, H)}</g><g data-d="9">
<ellipse cx="130" cy="96" rx="92" ry="22" fill="none" stroke="#29b6ff" stroke-width="2" transform="rotate(-18 130 96)" opacity=".85"/>
<circle cx="130" cy="96" r="52" fill="url(#nplanet)"/>
<ellipse cx="130" cy="96" rx="92" ry="22" fill="none" stroke="#e9f3ff" stroke-width="2" stroke-dasharray="120 400" stroke-dashoffset="-150" transform="rotate(-18 130 96)"/></g>
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
<rect x="296" y="240" width="88" height="4" rx="2" fill="#050506"/>
<g class="xf"><rect x="334" y="234" width="12" height="15" rx="2" fill="#cfd3da"/><line x1="340" y1="236" x2="340" y2="247" stroke="#555"/></g>

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
<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="5s" repeatCount="indefinite"/></g><g data-d="5">{blips}</g>
<text x="16" y="24" font-family="monospace" font-size="12" fill="#00a5a7" letter-spacing="3">SCANNING LOS ANGELES</text>
<text x="664" y="24" text-anchor="end" font-family="monospace" font-size="12" fill="#00a5a7" letter-spacing="2">{n} TONIGHT</text></svg>'''


def holo_svg(tonight=0, total=0, seed=0):
    """'Holo' hero (2026 futuristic): a rotating wireframe globe in an iridescent gradient, an orbiting
    satellite, a live waveform and HUD readouts."""
    rnd = random.Random(seed)
    W, H, cx, cy, R = 680, 210, 520, 108, 78
    mer = ""
    for i in range(6):   # meridians: ellipses whose width sweeps, which reads as rotation
        ph = i / 6
        mer += (f'<ellipse cx="{cx}" cy="{cy}" rx="{R}" ry="{R}" fill="none" stroke="url(#hg)" stroke-width="1" opacity=".75">'
                f'<animate attributeName="rx" values="{R};0;{R}" keyTimes="0;.5;1" dur="9s" begin="-{ph * 9:.2f}s" repeatCount="indefinite"/></ellipse>')
    lat = "".join(f'<ellipse cx="{cx}" cy="{cy + y}" rx="{(R * R - y * y) ** .5:.1f}" ry="{max(2, ((R * R - y * y) ** .5) * .18):.1f}" '
                  f'fill="none" stroke="url(#hg)" stroke-width=".8" opacity=".55"/>' for y in (-52, -26, 0, 26, 52))
    pts = []
    for k in range(3):
        pts.append(" ".join(f"{x},{150 + 18 * __import__('math').sin(x / (18 + k * 6) + k) * rnd.uniform(.5, 1):.1f}" for x in range(20, 380, 8)))
    wave = (f'<polyline fill="none" stroke="url(#hg)" stroke-width="2" points="{pts[0]}">'
            f'<animate attributeName="points" values="{pts[0]};{pts[1]};{pts[2]};{pts[0]}" dur="4s" repeatCount="indefinite"/></polyline>')
    dots = "".join(f'<circle cx="{rnd.randint(10, 670)}" cy="{rnd.randint(8, 200)}" r=".9" fill="#cfe9ff" opacity="{rnd.choice([.25, .5, .8])}"/>' for _ in range(40))
    hud = 'font-family="ui-monospace,monospace" font-size="10" fill="#a9bbe0" letter-spacing="1.5"'
    return f'''<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Wireframe globe and live waveform"
 style="display:block;border-radius:16px;border:1px solid #22304f;background:radial-gradient(120% 140% at 80% 40%,#111a30 0%,#05070d 60%)">
<defs><linearGradient id="hg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7cf5ff"/><stop offset=".35" stop-color="#b58cff"/>
<stop offset=".7" stop-color="#ff8ad8"/><stop offset="1" stop-color="#ffd27a"/></linearGradient>
<filter id="hglow"><feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<g data-d="2">{dots}</g>
<g data-d="8" filter="url(#hglow)">{mer}{lat}
<ellipse cx="{cx}" cy="{cy}" rx="{R + 30}" ry="20" fill="none" stroke="#7cf5ff" stroke-width=".8" opacity=".5" transform="rotate(-14 {cx} {cy})"/>
<circle r="4" fill="#ffffff"><animateMotion dur="6s" repeatCount="indefinite" path="M{cx - R - 30},{cy} a{R + 30},20 0 1,0 {2 * (R + 30)},0 a{R + 30},20 0 1,0 -{2 * (R + 30)},0" rotate="auto"/></circle></g>
<g data-d="3" filter="url(#hglow)">{wave}</g>
<g data-d="1"><text x="20" y="28" {hud}>LOS ANGELES · 34.05°N 118.24°W</text>
<text x="20" y="46" {hud} fill="#7cf5ff">● LIVE · {tonight} TONIGHT · {total} UPCOMING</text>
<text x="20" y="196" {hud}>MO'S HOUSE MUSIC RADAR · 2026</text></g></svg>'''


def yla_svg(seed=0):
    """You Look Amazing: a gold starburst setting into the desert under a soft boho sky with drifting clouds."""
    import math
    rnd = random.Random(seed)
    W, H, cx, cy = 680, 200, 340, 150
    rays = ""
    for i in range(23):
        a = math.pi * (i / 22)
        long_ = 118 if i % 2 == 0 else 92
        x1, y1 = cx + 46 * math.cos(a), cy - 46 * math.sin(a)
        x2, y2 = cx + long_ * math.cos(a), cy - long_ * math.sin(a)
        rays += (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#d9a441" stroke-width="{2.2 if i % 2 == 0 else 1.4}" '
                 f'stroke-linecap="round"><animate attributeName="opacity" values=".55;1;.55" dur="{3 + (i % 5) * .6:.1f}s" '
                 f'begin="-{i * .3:.1f}s" repeatCount="indefinite"/></line>')

    def cloud(x, y, s, dur, d0):
        return (f'<g opacity=".85"><g transform="translate({x} {y}) scale({s})">'
                f'<ellipse cx="0" cy="0" rx="34" ry="10" fill="#fffaf2"/><ellipse cx="-14" cy="-7" rx="16" ry="11" fill="#fffaf2"/>'
                f'<ellipse cx="10" cy="-10" rx="18" ry="13" fill="#fffaf2"/><ellipse cx="26" cy="-3" rx="13" ry="8" fill="#fbeee0"/></g>'
                f'<animateTransform attributeName="transform" type="translate" values="0 0;{d0} 0;0 0" dur="{dur}s" repeatCount="indefinite"/></g>')
    sparkles = "".join(f'<circle cx="{rnd.randint(20, 660)}" cy="{rnd.randint(10, 90)}" r="1" fill="#fffaf2">'
                       f'<animate attributeName="opacity" values="0;.9;0" dur="{rnd.uniform(2, 5):.1f}s" begin="-{rnd.uniform(0, 4):.1f}s" '
                       f'repeatCount="indefinite"/></circle>' for _ in range(14))
    return f'''<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="A gold starburst sun setting over the desert under soft clouds"
 style="display:block;border-radius:16px;border:1px solid #d8c3a0;background:linear-gradient(180deg,#8fcfcb 0%,#cfe3d6 34%,#f6d2b4 62%,#f2b878 82%,#e9a25c 100%)">
<defs><radialGradient id="ysun" cx=".5" cy=".9" r=".8"><stop offset="0" stop-color="#fff1c9"/><stop offset=".6" stop-color="#f6c66a"/><stop offset="1" stop-color="#e3a03c"/></radialGradient></defs>
<g data-d="2">{sparkles}</g>
<g data-d="3">{cloud(110, 44, 1.1, 38, 40)}{cloud(540, 30, .9, 46, -50)}{cloud(430, 72, .65, 30, 30)}{cloud(220, 82, .55, 52, -30)}</g>
<g data-d="6">{rays}<path d="M{cx - 44},{cy} A44,44 0 0 1 {cx + 44},{cy} Z" fill="url(#ysun)"/>
<path d="M{cx - 44},{cy} A44,44 0 0 1 {cx + 44},{cy}" fill="none" stroke="#c9962e" stroke-width="2"/></g>
<g data-d="8"><path d="M0,{cy} C120,{cy - 10} 220,{cy + 6} 340,{cy} S560,{cy - 12} 680,{cy - 2} L680,{H} L0,{H} Z" fill="#e9d6b6"/>
<path d="M0,{cy + 22} C150,{cy + 10} 300,{cy + 30} 450,{cy + 18} S620,{cy + 12} 680,{cy + 20} L680,{H} L0,{H} Z" fill="#dcc29a"/>
<line x1="0" y1="{cy}" x2="{W}" y2="{cy}" stroke="#127f7c" stroke-width="1.4" opacity=".55"/></g>
<text x="{cx}" y="{H - 14}" text-anchor="middle" font-family="Georgia,serif" font-size="13" letter-spacing="6" fill="#6b4f33">YOU LOOK AMAZING</text>
</svg>'''
