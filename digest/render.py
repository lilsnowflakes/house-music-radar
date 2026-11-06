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
from digest.venue_links import venue_html
from config.config import HEARD_HOME
from datetime import datetime
from zoneinfo import ZoneInfo

from collections import Counter, OrderedDict
import os
from digest.dates import bucket, sort_key, day_label, to_date, now_pt, show_time
from digest import theme as _theme
from digest.artist_links import links_html
from digest import highlight as _hl
from digest.share import buttons_html, SHARE_JS, sprite
from digest.hero import hero_svg, vapor_svg, console_svg, night_svg, deck_svg, radar_svg, holo_svg
from config.config import CODE_VERSION
from digest.colors import legend_html, chips_for

PACIFIC = ZoneInfo("America/Los_Angeles")
ORANGE = "#00b9bc"


def esc(x) -> str:
    return _html.escape(str(x or ""))


def announced_card(r: dict) -> str:
    link = (f'<a href="{esc(r["ticket_url"])}" style="color:{ORANGE};">Event page</a>'
            if r.get("ticket_url") else "")
    return f"""
    <div style="background:#00292a;border:1px solid #005254;border-radius:8px;
                padding:14px;margin-bottom:10px;font-family:monospace;">
      <div style="font-size:16px;font-weight:bold;color:#fff;">{esc(r['artist'])}</div>
      <div style="color:#ccc;font-size:13px;margin:6px 0;">
        📅 {esc(r['date_str'])} &nbsp;|&nbsp; 📍 {venue_html(r['venue'], r.get('address',''))}
      </div>
      <div style="color:{ORANGE};font-size:13px;">⏳ {esc(r['on_sale_text'])}</div>
      <div style="margin-top:6px;">{links_html(r)}</div>
      <div style="font-size:12px;margin-top:6px;">{link}</div>
    </div>"""


def section(title: str, body: str, note: str = "") -> str:
    note_html = (f'<div style="color:#009092;font-size:12px;margin-bottom:10px;">{note}</div>'
                 if note else "")
    return f"""
    <div style="margin-bottom:32px;">
      <h2 style="color:{ORANGE};border-bottom:1px solid #005254;padding-bottom:8px;
                 font-family:monospace;">{title}</h2>
      {note_html}{body}
    </div>"""


def health_table(rows) -> str:
    colors = {"ok": "#5ec269", "empty": "#e0b341", "error": "#e5534b",
              "skipped": "#00a5a7"}
    trs = ""
    for label, status, detail in rows:
        c = colors.get(status, "#00a5a7")
        trs += (f'<tr><td style="padding:4px 10px;color:#ccc;">{esc(label)}</td>'
                f'<td style="padding:4px 10px;color:{c};">{esc(status)}</td>'
                f'<td style="padding:4px 10px;color:#00a5a7;">{esc(detail)}</td></tr>')
    return ('<table style="font-family:monospace;font-size:12px;border-collapse:collapse;">'
            f"{trs}</table>")



FONT = "font-family:monospace;"


def _initials(name):
    w = [x for x in (name or "?").replace("&", " ").split() if x[:1].isalnum()]
    return ("".join(x[0] for x in w[:2]) or "?").upper()


def stale_js(now):
    """If someone opens the page after the night it was built for, say so instead of showing an old 'Tonight'."""
    night = (now - __import__("datetime").timedelta(hours=6)).strftime("%Y-%m-%d")
    label = (now - __import__("datetime").timedelta(hours=6)).strftime("%a %b %-d")
    tomorrow_iso = (now - __import__("datetime").timedelta(hours=6) + __import__("datetime").timedelta(days=1)).strftime("%Y-%m-%d")
    return f"""<script>
(function(){{var n=new Date(Date.now()-6*3600e3),
 here=n.toLocaleDateString('en-CA',{{timeZone:'America/Los_Angeles'}});
 if(here<='{night}')return;
 var s=document.querySelector('#tonight>summary');
 if(s){{s.firstChild.textContent='🌙 Last night ({label}) ';document.getElementById('tonight').open=false;}}
 var t=document.getElementById('tomorrow');
 if(t&&here==='{tomorrow_iso}'){{t.querySelector('summary').firstChild.textContent='🔥 Tonight ';t.open=true;}}
 var b=document.createElement('div');
 b.style.cssText='background:#3a2a00;color:#ffd27a;border:1px solid #7a5b00;border-radius:8px;padding:8px 12px;margin:0 0 12px;font:13px monospace;text-align:center';
 b.textContent='Built for {label}. The next refresh is on its way; "This week" below is still current.';
 var h=document.getElementById('highlight')||document.getElementById('tonight');h.parentNode.insertBefore(b,h);}})();
</script>"""


LAZY_JS = """<script>
document.addEventListener('toggle',function(e){var d=e.target;if(d.tagName!=='DETAILS'||!d.open)return;
 var b=d.querySelector(':scope>.secb'),t=b&&b.querySelector(':scope>template');if(t)t.replaceWith(t.content);},true);
</script>"""

MOTION_CSS = """
.hero{position:relative}
#tilt[hidden]{display:none}
#tilt{position:absolute;right:10px;bottom:10px;font:12px monospace;color:#00b9bc;background:#001515cc;
 border:1px solid #005254;border-radius:999px;padding:4px 10px;cursor:pointer}
.hero [data-d],.hero .xf{transition:transform .25s ease-out}
@media (orientation:landscape) and (max-height:520px){.hero svg{max-height:46vh;width:auto;margin:0 auto}}
@media (prefers-reduced-motion:reduce){.hero [data-d],.hero .xf{transition:none}}
"""

MOTION_JS = r"""<script>
(function(){
 if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
 var hero=document.querySelector('.hero');if(!hero)return;
 var els=[].slice.call(hero.querySelectorAll('[data-d]')),xf=hero.querySelector('.xf'),btn=document.getElementById('tilt');
 function move(x,y){ /* x,y in -1..1 */
  x=Math.max(-1,Math.min(1,x));y=Math.max(-1,Math.min(1,y));
  els.forEach(function(e){var d=+e.getAttribute('data-d');e.setAttribute('transform','translate('+(x*d).toFixed(1)+' '+(y*d*.5).toFixed(1)+')');});
  if(xf)xf.setAttribute('transform','translate('+(x*36).toFixed(1)+' 0)');
 }
 function onTilt(e){
  if(e.gamma==null)return;
  var a=(screen.orientation&&screen.orientation.angle)||window.orientation||0,x,y;
  if(a==90){x=e.beta/25;y=(-e.gamma-45)/25;}            /* phone on its side, top to the left */
  else if(a==-90||a==270){x=-e.beta/25;y=(e.gamma-45)/25;} /* on its side, top to the right */
  else{x=e.gamma/25;y=(e.beta-45)/25;}                   /* upright: left/right tilt moves the scene */
  move(x,y);
 }
 var touch=matchMedia('(pointer:coarse)').matches||('ontouchstart' in window);
 function start(){addEventListener('deviceorientation',onTilt);if(btn)btn.hidden=true;}
 if(touch&&window.DeviceOrientationEvent){
  if(typeof DeviceOrientationEvent.requestPermission==='function'){
   /* iPhone (and some browsers): motion needs one tap to allow */
   btn.hidden=false;btn.onclick=function(){DeviceOrientationEvent.requestPermission().then(function(s){if(s==='granted')start();}).catch(function(){});};
  }else{start();}  /* Android: works straight away */
 }
 hero.addEventListener('mousemove',function(e){var r=hero.getBoundingClientRect();
  move((e.clientX-r.left)/r.width*2-1,(e.clientY-r.top)/r.height*2-1);});
 hero.addEventListener('mouseleave',function(){move(0,0);});
})();
</script>"""

PAGE_CSS = """
.ic{vertical-align:middle}
.ml{text-decoration:none;display:inline-block;margin-right:6px;padding:6px 8px 4px 0}
.sb{color:#00b9bc;text-decoration:none;font-size:12px;border:1px solid #005254;border-radius:999px;padding:3px 10px;
 margin:3px 0 3px 6px;display:inline-block;background:none;cursor:pointer;font-family:inherit}
.evrow{display:flex;gap:12px;align-items:center;background:#00292a;border:1px solid #005254;border-radius:8px;
 padding:10px 12px;margin-bottom:6px;font-family:monospace}
.evmain{min-width:0;flex:1}
.evside{text-align:right;flex:none}
.evside>div{margin-top:6px}
.nm{font-size:15px}.nm a,.nm span{color:#fff;text-decoration:none;font-weight:bold}
.vn{color:#ccc;font-size:12px;margin-top:2px}
.chips{margin-top:6px}
.mrow{display:flex;align-items:center;flex-wrap:wrap;gap:4px;margin-top:6px}
.sharebar{margin-left:auto;text-align:right}
.via{color:#009092;font-size:11px}.via a{color:#00b9bc}
.av{width:44px;height:44px;border-radius:50%;flex:none}
img.av{object-fit:cover;border:1px solid #005254}
div.av{background:#003e3f;color:#00b9bc;display:flex;align-items:center;justify-content:center;font-weight:bold}
.tix{background:#00b9bc;color:#001515;padding:3px 10px;border-radius:4px;text-decoration:none;font-size:11px;white-space:nowrap}
.sc{color:#00b9bc;font-weight:bold;font-size:18px;line-height:1}.sc span{color:#009092;font-size:10px;font-weight:normal}
.sc0{color:#009092;font-size:13px;line-height:1}.sc0 span{font-size:10px}
.dl{color:#00a5a7;font-size:12px;letter-spacing:1px;text-transform:uppercase;margin:14px 0 6px;font-family:monospace}
details.sec{margin-bottom:10px;background:#001515;border:1px solid #005254;border-radius:10px;padding:0 12px}
details.sec>summary{cursor:pointer;padding:12px 0;color:#00b9bc;font-weight:bold;font-family:monospace}
details.sec>summary span{color:#00a5a7;font-weight:normal}
.secb{padding-bottom:10px}
.none{color:#00a5a7;font-size:13px;padding:6px 0;font-family:monospace}
.tba{color:#009092}.st{color:#00b9bc;white-space:nowrap}
.fchip{font:12px monospace;color:#00a5a7;background:#001515;border:1px solid #005254;border-radius:999px;padding:5px 11px;margin:0 6px 8px 0;cursor:pointer}
.fchip[aria-pressed="true"]{background:#00b9bc;color:#001515;border-color:#00b9bc;font-weight:bold}
@media (max-width:560px){
 .evrow{flex-wrap:wrap}
 .evmain{flex-basis:calc(100% - 60px)}
 .evside{flex-basis:100%;display:flex;justify-content:space-between;align-items:center;text-align:left}
 .evside>div{margin-top:0}
 .hlpic{width:60px!important;height:60px!important;font-size:20px!important}
 .sb{font-size:11px;padding:3px 8px}
}
"""


def _price_num(p):
    import re as _r
    m = _r.search(r"\$\s*(\d+)", p or "")
    return int(m.group(1)) if m else (0 if "free" in (p or "").lower() else None)


def filter_tokens(ev):
    """Words the filter bar checks: pm, spot, conf, ok18, cheap, big, tix, sold, late."""
    t = []
    g = (" ".join(ev.get("genres") or []) + " " + ev.get("title", "")).lower()
    if "progressive" in g or "melodic" in g:
        t.append("pm")
    if ev.get("watched"):
        t.append("spot")
    if (ev.get("house_check") or {}).get("verdict") == "house":
        t.append("conf")
    if ev.get("age") != "21+":
        t.append("ok18")
    n = _price_num(ev.get("price"))
    if n is not None and n < 30:
        t.append("cheap")
    if ev.get("score", 0) >= 50:
        t.append("big")
    sold = ev.get("ticket_status") == "sold out" or "sold out" in (ev.get("price", "") + ev.get("title", "")).lower()
    if sold:
        t.append("sold")
    elif ev.get("ticket_url"):
        t.append("tix")
    start = show_time(ev)[1]
    if start and (start >= "21:00" or start < "06:00"):
        t.append("late")
    return " ".join(t)


FILTERS = [("pm", "Progressive / melodic"), ("spot", "★ Your spots"), ("conf", "✓ Confirmed house"),
           ("tix", "Tickets available"), ("nosold", "Hide sold out"), ("ok18", "18+ / all ages"),
           ("cheap", "Under $30"), ("big", "Big names 50+"), ("late", "Late (9pm+)")]


def filter_bar():
    chips = "".join(f'<button type="button" class="fchip" data-k="{k}" aria-pressed="false">{esc(lab)}</button>'
                    for k, lab in FILTERS)
    return (f'<details class="sec" id="filters"><summary style="font-size:14px">⚙ Filters <span id="fcount"></span></summary>'
            f'<div class="secb">{chips}<button type="button" class="fchip" id="fclear">Clear</button>'
            f'<div class="none" style="font-size:11px">Filters stack (show only shows that match all of them) and are remembered on this device.</div>'
            f'</div></details>')


FILTER_JS = r"""<script>
(function(){
 var K='radarFilters',on={};try{on=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){}
 function apply(){
  var act=Object.keys(on).filter(function(k){return on[k]});
  document.querySelectorAll('.evrow[data-f]').forEach(function(r){
   var f=' '+r.dataset.f+' ',show=act.every(function(k){return k==='nosold'?f.indexOf(' sold ')<0:f.indexOf(' '+k+' ')>=0});
   r.style.display=show?'':'none';});
  document.querySelectorAll('.dl').forEach(function(d){var n=d.nextElementSibling,any=false;
   while(n&&!n.classList.contains('dl')){if(n.classList.contains('evrow')&&n.style.display!=='none')any=true;n=n.nextElementSibling;}
   d.style.display=any?'':'none';});
  document.querySelectorAll('.fchip[data-k]').forEach(function(b){b.setAttribute('aria-pressed',!!on[b.dataset.k])});
  document.querySelectorAll('details.sec>.secb').forEach(function(b){
   var rows=[].filter.call(b.children,function(x){return x.classList.contains('evrow')||x.classList.contains('dl')}),
       ev=b.querySelectorAll(':scope>.evrow'),shown=[].filter.call(ev,function(x){return x.style.display!=='none'}).length,
       n=b.querySelector(':scope>.fnote');
   if(ev.length&&!shown){if(!n){n=document.createElement('div');n.className='none fnote';b.prepend(n);}
    n.textContent='All '+ev.length+' hidden by your filters.';n.style.display='';}
   else if(n)n.style.display='none';});
  var c=document.getElementById('fcount');if(c)c.textContent=act.length?'('+act.length+' on)':'';
  try{localStorage.setItem(K,JSON.stringify(on))}catch(e){}
 }
 document.addEventListener('click',function(e){var b=e.target.closest('.fchip');if(!b)return;
  if(b.id==='fclear')on={};else on[b.dataset.k]=!on[b.dataset.k];apply();});
 document.addEventListener('toggle',function(){setTimeout(apply,0)},true);  /* sections built on open get filtered too */
 apply();
})();
</script>"""


def score_badge(score):
    """Always shown. A dash means no popularity data came back for this artist (yet)."""
    if score:
        return (f'<div class="sc" title="Popularity score (0-100): Spotify 50%, RA 30%, SoundCloud 20%">'
                f'{score:.0f}<span>/100</span></div>')
    return '<div class="sc0" title="No popularity data for this artist yet">–<span>/100</span></div>'


def media_row(ev):
    """Media icons on the left, invite/calendar buttons pushed to the right: fewer mis-taps."""
    return f'<div class="mrow"><div>{links_html(ev)}</div><div class="sharebar">{buttons_html(ev)}</div></div>'


def event_row(ev: dict) -> str:
    """One compact card per show. All styling is in PAGE_CSS so 400+ rows stay light."""
    artist = ev.get("artist") or ev.get("title") or "Unknown"
    star = "★ " if ev.get("watched") else ""
    link = ev.get("ticket_url", "")
    name = f'<a href="{esc(link)}">{esc(artist)}</a>' if link else f'<span>{esc(artist)}</span>'
    pic = (f'<img class="av" src="{esc(ev["image"])}" alt="" width="44" height="44" loading="lazy">'
           if ev.get("image") else f'<div class="av">{esc(_initials(artist))}</div>')
    title = ev.get("title", "")
    sub = esc(title) if title and title != artist and len(title) < 90 else ""
    via = " + ".join(esc(s) for s in (ev.get("sources") or [ev.get("source", "")]) if s)
    edm = f' · <a href="{esc(ev["edmtrain_url"])}">on Edmtrain</a>' if ev.get("edmtrain_url") else ""
    edm += f' · <a href="{esc(ev["reddit_url"])}">on Reddit</a>' if ev.get("reddit_url") else ""
    edm += f' · ⚠ moved from {esc(ev["moved_from"])}' if ev.get("moved_from") else ""
    price = " " + esc(ev.get("price")) if ev.get("price") else ""
    btn = f'<a class="tix" href="{esc(link)}">Tickets{price}</a>' if link else ""
    venue = (f'📍 {venue_html(ev.get("venue"), ev.get("address", ""))}' if ev.get("venue")
             else '<span class="tba">📍 Venue TBA</span>')
    tlab = show_time(ev)[0]
    when = f' · <span class="st">🕘 {esc(tlab)}</span>' if tlab else ""
    return (f'<div class="evrow" data-f="{filter_tokens(ev)}">{pic}<div class="evmain"><div class="nm">{star}{name}</div>'
            f'<div class="vn">{venue}{when}{" · " + sub if sub else ""}</div>'
            f'<div class="chips">{chips_for(ev)}</div>{media_row(ev)}<div class="via">via {via}{edm}</div></div>'
            f'<div class="evside">{score_badge(ev.get("score", 0))}<div>{btn}</div></div></div>')


def highlight_html(events, now):
    ev, note, how = _hl.pick(events, now)
    if not ev:
        return ""
    artist = ev.get("artist") or ev.get("title") or ""
    link = ev.get("ticket_url", "")
    pic = (f'<img class="hlpic" src="{esc(ev["image"])}" alt="" width="96" height="96" style="border-radius:50%;object-fit:cover;'
           f'border:2px solid #00b9bc;flex:none;">' if ev.get("image") else
           f'<div class="hlpic" style="width:96px;height:96px;border-radius:50%;background:#003e3f;color:#00b9bc;display:flex;'
           f'align-items:center;justify-content:center;font-size:30px;font-weight:bold;flex:none;border:2px solid #00b9bc;">'
           f'{esc(_initials(artist))}</div>')
    btn = (f'<a href="{esc(link)}" style="background:#00b9bc;color:#001515;padding:8px 16px;border-radius:6px;'
           f'text-decoration:none;font-weight:bold;font-size:13px;display:inline-block;margin-top:10px;">'
           f'Tickets{" · " + esc(ev.get("price")) if ev.get("price") else ""}</a>') if link else ""
    return (f'<div id="highlight" style="background:linear-gradient(135deg,#00292a,#003e3f);border:2px solid #00b9bc;'
            f'border-radius:14px;padding:16px;margin:0 0 16px;{FONT}">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;"><div style="color:#00b9bc;font-size:11px;'
            f'letter-spacing:2px;font-weight:bold;">★ HIGHLIGHT · {esc(how.upper())}</div>{score_badge(ev.get("score", 0))}</div>'
            f'<div style="display:flex;gap:16px;align-items:center;margin-top:10px;">{pic}<div style="min-width:0;">'
            f'<div style="color:#fff;font-size:22px;font-weight:bold;line-height:1.2;">{esc(artist)}</div>'
            f'<div style="color:#00a5a7;font-size:13px;margin-top:4px;">{esc(day_label(ev.get("date_str", "")))} · '
            f'📍 {venue_html(ev.get("venue", ""), ev.get("address", ""))}</div>'
            f'{f"<div style=\"color:#ccc;font-size:13px;margin-top:6px;\">{esc(note)}</div>" if note else ""}'
            f'<div style="margin-top:8px;">{chips_for(ev)}</div>{media_row(ev)}{btn}</div></div></div>')


def _by_day(evs, today):
    """Chronological, A-Z by artist inside each day."""
    evs = sorted(evs, key=lambda e: (sort_key(e.get("date_str", ""), today),
                                     (e.get("artist") or e.get("title") or "").casefold()))
    days = OrderedDict()
    for e in evs:
        days.setdefault(day_label(e.get("date_str", "")) or "Date unclear", []).append(e)
    return days


def _days_html(evs, today):
    out = ""
    for label, items in _by_day(evs, today).items():
        out += f'<div class="dl">{esc(label)}</div>' + "".join(event_row(e) for e in items)
    return out


def _details(id_, title, count, body, open_=False, level=2, lazy=True):
    """Collapsible section. Closed sections keep their rows in a <template> that is only turned into
    real page elements when opened: the phone builds Tonight first, everything else on demand."""
    size = "17px" if level == 2 else "14px"
    inner = body or '<div class="none">Nothing listed.</div>'
    if lazy and not open_:
        inner = f"<template>{inner}</template>"
    return (f'<details class="sec" id="{id_}" {"open" if open_ else ""}><summary style="font-size:{size}">'
            f'{title} <span>({count})</span></summary><div class="secb">{inner}</div></details>')


def source_map(events, health):
    """Which source supplied how many of the final rows, then the per-source health table."""
    c = Counter(s for e in events for s in (e.get("sources") or [e.get("source", "")]) if s)
    if c:
        rows = "".join(f'<span style="display:inline-block;background:#003e3f;color:#ccc;border-radius:4px;'
                       f'padding:2px 8px;margin:0 6px 6px 0;font-size:12px;">{esc(k)} <b style="color:#00b9bc;">{v}</b></span>'
                       for k, v in c.most_common())
        counts = (f'<div style="{FONT}color:#00a5a7;font-size:12px;margin-bottom:8px;">Shows on this page by source '
                  f'(a show carried by two sources counts for both):</div><div>{rows}</div>')
    else:
        counts = ""
    return counts + health_table(health)


STRIPES = ('<div style="height:8px;border-radius:4px;margin:2px 0 10px;background:linear-gradient(90deg,#b8451f 0 22%,#d9772b 22% 44%,#7d7a2c 44% 66%,#e8d2a6 66% 84%,#6a3418 84%);"></div>')

STYLES = [("classic", "Classic", "index.html", "list.html"), ("outrun", "Outrun", "index-outrun.html", "list-outrun.html"),
          ("console", "Console", "index-console.html", "list-console.html"),
          ("night", "Night", "index-night.html", "list-night.html"), ("deck", "Deck", "index-deck.html", "list-deck.html"),
          ("holo", "Holo", "index-holo.html", "list-holo.html")]


def style_switcher(active, base, page="index"):
    """Three check-box style links at the top. The choice is remembered in the browser."""
    idx = 2 if page == "index" else 3
    items = "".join(
        f'<a href="{base}{s[idx]}" data-style="{s[0]}" style="color:#00b9bc;text-decoration:none;padding:5px 12px;'
        f'border:1px solid #005254;border-radius:6px;{"background:#003e3f;font-weight:bold;" if s[0] == active else ""}">'
        f'{"☑" if s[0] == active else "☐"} {s[1]}</a>' for s in STYLES)
    return (f'<div id="styles" style="display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin:0 0 12px;'
            f'font-family:monospace;font-size:12px;"><span style="color:#00a5a7;padding:5px 0;">Style:</span>{items}</div>')


STYLE_JS = ("<script>try{var k='radarStyle',cur=document.body.dataset.style;"
            "document.querySelectorAll('#styles a').forEach(function(a){a.addEventListener('click',function(){localStorage.setItem(k,a.dataset.style)})});"
            "var want=localStorage.getItem(k);if(want&&want!==cur&&!location.search){var l=document.querySelector('#styles a[data-style='+want+']');"
            "if(l)location.replace(l.getAttribute('href'))}}catch(e){}</script>")


def build_page(events, announced, health, site_url="", demo=False, dupes_removed=0, style="classic") -> str:
    now = now_pt()
    stamp = now.strftime("%A, %B %-d, %Y")
    th = _theme.choose() if style == "classic" else (style, 0, "set")
    base = site_url if (site_url and site_url.endswith("/")) else (site_url + "/" if site_url else "")
    run_no = _theme.run_number()
    run_txt = f"Run #{run_no}" if run_no else "Local build"
    ran = now.strftime("%b %-d, %Y %-I:%M %p PT")

    banner = ""
    if demo:
        banner = (f'<div style="background:#5a1a1a;color:#fff;padding:10px;text-align:center;{FONT}'
                  f'margin-bottom:16px;">DEMO DATA. These are made-up shows, not real listings.</div>')
    elif site_url:
        banner = (f'<div style="text-align:center;margin-bottom:12px;{FONT}font-size:12px;">'
                  f'<a href="{esc(site_url)}" style="color:{ORANGE};">Open the live page</a></div>')
    banner += (f'<div style="background:#00292a;border:1px solid #005254;border-radius:6px;padding:10px;'
               f'text-align:center;{FONT}font-size:12px;color:#bbb;margin-bottom:16px;">'
               f'🎧 <a href="{base}{dict((s[0], s[3]) for s in STYLES)[style]}" style="color:{ORANGE};">Full list by night</a> · tap a venue for Google Maps · '
               f'Smaller rooms and tonight\'s live music: <a href="{HEARD_HOME}" style="color:{ORANGE};">Heard (getheard.live)</a></div>')

    # bucket the shows
    groups = {k: [] for k in ("tonight", "tomorrow", "week", "next", "later", "unknown")}
    for e in events:
        b = bucket(e.get("date_str", ""), now)
        if b != "past":
            groups[b].append(e)
    from datetime import timedelta as _td
    tmr = (now - _td(hours=6) + _td(days=1)).strftime("%a %b %-d")

    s_tonight = _details("tonight", "🔥 Tonight", len(groups["tonight"]),
                         _days_html(groups["tonight"], now), open_=bool(groups["tonight"]))
    s_tomorrow = _details("tomorrow", f"🌅 Tomorrow · {tmr}", len(groups["tomorrow"]), _days_html(groups["tomorrow"], now))
    s_week = _details("week", "This week", len(groups["week"]), _days_html(groups["week"], now))
    s_next = _details("next", "Next week", len(groups["next"]), _days_html(groups["next"], now))

    months = OrderedDict()
    for e in sorted(groups["later"] + groups["unknown"], key=lambda e: sort_key(e.get("date_str", ""), now)):
        y, m, _ = sort_key(e.get("date_str", ""), now)
        key = "Date unclear" if y == 9999 else datetime(y, m, 1).strftime("%B %Y")
        months.setdefault(key, []).append(e)
    later_body = "".join(_details("m-" + k.replace(" ", "-").lower(), k, len(v), _days_html(v, now), level=3)
                         for k, v in months.items())
    s_later = _details("later", "Later", sum(len(v) for v in months.values()), later_body)

    ann_body = "".join(announced_card(r) for r in announced) or \
        f'<div style="color:#00a5a7;{FONT}font-size:13px;">Nothing announced-but-unsold found this run.</div>'
    s_ann = _details("announced", "⏳ Announced, not on sale yet", len(announced),
                     f'<div style="color:#009092;font-size:12px;margin-bottom:8px;{FONT}">Ticketmaster and DICE rooms only. '
                     f'AXS is not covered (its site blocks automated checks).</div>' + ann_body)

    spots = [e for e in events if e.get("watched") and bucket(e.get("date_str", ""), now) != "past"]
    s_spots = _details("spots", "★ Your spots", len(spots), _days_html(spots, now))

    nav_link = f"color:{ORANGE};text-decoration:none;padding:6px 12px;border:1px solid #005254;border-radius:999px;"
    nav = (f'<div style="position:sticky;top:0;background:#001515;padding:8px 0;margin:0 0 12px;z-index:5;{FONT}'
           f'font-size:13px;display:flex;gap:8px;flex-wrap:wrap;justify-content:center;border-bottom:1px solid #003e3f;">'
           f'<a href="#tonight" style="{nav_link}">Tonight</a><a href="#tomorrow" style="{nav_link}">Tomorrow</a>'
           f'<a href="#week" style="{nav_link}">This week</a>'
           f'<a href="#next" style="{nav_link}">Next week</a><a href="#later" style="{nav_link}">Later</a></div>')

    dup_note = f" · {dupes_removed} duplicate listings merged" if dupes_removed else ""
    s_health = (f'<div id="health" style="margin-top:28px;"><h2 style="color:{ORANGE};border-bottom:1px solid #005254;'
                f'padding-bottom:8px;{FONT}">Source health</h2>'
                f'<div style="color:#009092;font-size:12px;margin-bottom:10px;{FONT}">What each source returned on this run{dup_note}. '
                f'Yellow or red means that source returned nothing. Check it before trusting the lists above.</div>'
                f'{source_map(events, health)}</div>')

    how = {"rotate": "rotates every run", "auto": "default for Classic"}.get(th[2], "set by config/theme.txt")
    foot = (f'{run_txt} · last ran {ran} · code v{CODE_VERSION} · color: {th[0]} ({how}). '
            f'To pick one, edit config/theme.txt (auto, mahogany, rotate, turquoise, violet, magenta, amber, green, blue, red).<br>'
            f'Updated every Monday morning. Within each day shows are A to Z by artist. '
            f'Scores: Spotify 50% · RA 30% · SoundCloud 20%.')

    from datetime import timedelta
    day0 = now.date()
    counts = [sum(1 for x in events if to_date(x.get("date_str", ""), now) == day0 + timedelta(days=i)) for i in range(7)]
    tl = [f"{(x.get('artist') or x.get('title') or '').upper()} @ {(x.get('venue') or '').upper()}" for x in groups["tonight"]]
    n_all = sum(len(v) for v in groups.values())
    hero = {"outrun": lambda: vapor_svg(run_no),
            "console": lambda: console_svg(run_no, len(groups["tonight"]), n_all),
            "night": lambda: night_svg(counts),
            "deck": lambda: deck_svg(tl, run_no),
            "redline": lambda: radar_svg(len(groups["tonight"])),
            "holo": lambda: holo_svg(len(groups["tonight"]), n_all, run_no)}.get(th[0], lambda: hero_svg(run_no))()

    page = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mo's House Music Radar</title>
<style>{PAGE_CSS}{MOTION_CSS}</style></head>
<body data-style="{style}" style="background:#001515;color:#fff;font-family:monospace;max-width:680px;margin:0 auto;padding:20px;">
{sprite()}
  {banner}
  {style_switcher(style, base)}
  <div class="hero">{hero}<button type="button" id="tilt" hidden>✨ Tilt</button></div>
  <div style="text-align:center;padding:14px 0 6px;">
    <div style="font-size:28px;font-weight:bold;color:{ORANGE};letter-spacing:2px;">🎛 MO'S HOUSE MUSIC RADAR</div>
    <div style="color:#00a5a7;font-size:13px;margin-top:4px;">{stamp} · Los Angeles · {run_txt} · last ran {ran}</div>
  </div>
  {STRIPES if th[0] == 'mahogany' else ''}
  {nav}
  {legend_html()}
  {highlight_html(events, now)}
  {filter_bar()}
  {s_tonight}{s_tomorrow}{s_week}{s_next}{s_later}{s_ann}{s_spots}
  {s_health}
  <div style="text-align:center;color:#009092;font-size:11px;padding:24px 0;border-top:1px solid #003e3f;margin-top:24px;">
    {foot}
  </div>
<script>
function openFor(id){{var el=id&&document.getElementById(id);if(!el)return;
 for(var p=el;p;p=p.parentElement){{if(p.tagName==='DETAILS')p.open=true;}}
 el.scrollIntoView();}}
addEventListener('hashchange',function(){{openFor(location.hash.slice(1));}});
document.addEventListener('click',function(e){{var a=e.target.closest('a[href^="#"]');
 if(a){{e.preventDefault();history.replaceState(null,'',a.getAttribute('href'));openFor(a.getAttribute('href').slice(1));}}}});
</script>
{STYLE_JS if site_url else ''}
{SHARE_JS}
{LAZY_JS}
{FILTER_JS}
{stale_js(now)}
{MOTION_JS}
</body></html>"""
    return _theme.apply(page, th)
