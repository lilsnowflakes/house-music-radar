"""
moments.py - "From the floor" photos, fed from a shared Google Drive folder.

You drop photos into the Drive folder from your phone. Each run:
  1. lists the folder (Drive API, read-only, API key),
  2. downloads only photos it hasn't processed before (kept in data/photos/ by the workflow cache),
  3. makes two small WebP copies (thumbnail and full view) with ALL hidden data removed (GPS, phone),
  4. the main page rotates through photos from the last 7 days (the section is hidden if there are none),
  5. moments.html shows every photo as a timeline, newest first.
Caption = the photo's Drive description, or its file name. Write "caption | photo @you ft @friend".
"""
import html
import json
import os
import re
from datetime import datetime, timedelta, timezone

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(ROOT, "data", "photos")          # processed copies, carried between runs
OUT = os.path.join(ROOT, "docs", "moments")           # what the website serves
INDEX = os.path.join(STORE, "index.json")
WEEK_DAYS = 7
THUMB, FULL = 480, 1400
LAST = {}
e = html.escape


def _env(k):
    return (os.environ.get(k) or "").strip()


def _load_index():
    try:
        return json.load(open(INDEX, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _caption(name, desc):
    """Caption and credit from the Drive description, or else from the file name.
    'Clinic at Jungle | photo @mo'  or  'Clinic at Jungle - photo @mo'  -> ("Clinic at Jungle", "photo @mo").
    Camera names like IMG_4821 or PXL_2026... are not used as captions."""
    text = (desc or "").strip()
    if not text:
        text = re.sub(r"\.[a-z0-9]{3,4}$", "", name or "", flags=re.I).replace("_", " ").strip()
        if re.match(r"(?i)^(img|pxl|dsc|dscn|dji|gopr|photo|image|screenshot|signal|whatsapp image)[\s-]*[\d\s:.-]*$", text) \
                or re.match(r"^[\d\s:.-]+$", text):
            text = ""
    if "|" in text:
        cap, _, credit = text.partition("|")
    else:
        m = re.search(r"\s[-–—~·]\s*((?:photo|pic|📸|ft\.?|feat\.?)\b.*)$", text, re.I)
        cap, credit = (text[:m.start()], m.group(1)) if m else (text, "")
    return cap.strip(), credit.strip()


def _taken(f):
    t = (f.get("imageMediaMetadata") or {}).get("time")       # "2026:11:04 22:13:01" from the camera
    for s, fmt in ((t, "%Y:%m:%d %H:%M:%S"), ((f.get("createdTime") or "")[:19], "%Y-%m-%dT%H:%M:%S")):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc).isoformat()
        except (TypeError, ValueError):
            continue
    return datetime.now(timezone.utc).isoformat()


def _process(raw_bytes, pid):
    from io import BytesIO
    from PIL import Image, ImageOps
    try:                                   # iPhone photos (HEIC/HEIF)
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    im = ImageOps.exif_transpose(Image.open(BytesIO(raw_bytes))).convert("RGB")   # upright, then metadata is dropped
    os.makedirs(STORE, exist_ok=True)
    full = im.copy()
    full.thumbnail((FULL, FULL))
    full.save(os.path.join(STORE, f"{pid}.webp"), "WEBP", quality=78, method=5)
    th = ImageOps.fit(im, (THUMB, THUMB), centering=(0.5, 0.38))   # square, biased up toward faces
    th.save(os.path.join(STORE, f"{pid}-t.webp"), "WEBP", quality=72, method=5)
    return full.size


def sync():
    """Bring the Drive folder into data/photos. Returns the full photo list, newest first."""
    idx = _load_index()
    key, folder = _env("GOOGLE_API_KEY"), _env("DRIVE_FOLDER_ID")
    if not key or not folder:
        LAST["Photos (Drive)"] = ("skipped", "add GOOGLE_API_KEY and DRIVE_FOLDER_ID secrets to use the Drive photo folder")
    else:
        try:
            files, token = [], None
            while True:
                r = requests.get("https://www.googleapis.com/drive/v3/files", timeout=20, params={
                    "q": f"'{folder}' in parents and mimeType contains 'image/' and trashed=false",
                    "orderBy": "createdTime desc", "pageSize": 200, "key": key, **({"pageToken": token} if token else {}),
                    "fields": "nextPageToken,files(id,name,description,createdTime,md5Checksum,imageMediaMetadata(time))"})
                if r.status_code != 200:
                    raise RuntimeError(f"{r.status_code}: {r.text[:120]}")
                j = r.json()
                files += j.get("files", [])
                token = j.get("nextPageToken")
                if not token:
                    break
            new = 0
            live = set()
            for f in files:
                pid = f["id"] + "-" + (f.get("md5Checksum") or "x")[:8]
                live.add(pid)
                cap, credit = _caption(f.get("name"), f.get("description"))
                rec = idx.get(pid) or {}
                if not rec or not os.path.exists(os.path.join(STORE, f"{pid}-t.webp")):
                    raw = requests.get(f"https://www.googleapis.com/drive/v3/files/{f['id']}",
                                       params={"alt": "media", "key": key}, timeout=60)
                    if raw.status_code != 200:
                        continue
                    w, h = _process(raw.content, pid)
                    rec = {"w": w, "h": h}
                    new += 1
                rec.update(caption=cap, credit=credit, taken=_taken(f))   # captions can be edited in Drive later
                idx[pid] = rec
            for pid in [p for p in idx if p not in live and not p.startswith("local-")]:   # removed from Drive -> removed here
                idx.pop(pid, None)
            LAST["Photos (Drive)"] = ("ok", f"{len(files)} photos in the folder, {new} new this run")
        except Exception as ex:
            LAST["Photos (Drive)"] = ("error", f"{str(ex)[:120]} (kept the photos from earlier runs)")
    _add_local(idx)
    os.makedirs(STORE, exist_ok=True)
    json.dump(idx, open(INDEX, "w", encoding="utf-8"), indent=0)
    return publish(idx)


def _add_local(idx):
    """The repo's community/spotlight.txt still works as a second way to post one photo."""
    from digest.community import read_spotlight, SRC
    info = read_spotlight()
    for p in [p for p in idx if p.startswith("local-")]:
        idx.pop(p)
    if not info:
        return
    path = os.path.join(SRC, info["photo"])
    pid = "local-" + re.sub(r"[^a-z0-9]", "", info["photo"].lower())[:20] + f"-{int(os.path.getmtime(path))}"
    w, h = _process(open(path, "rb").read(), pid)
    idx[pid] = {"w": w, "h": h, "caption": info.get("caption", ""), "credit": info.get("credit", ""),
                "taken": datetime.now(timezone.utc).isoformat()}


def publish(idx):
    """Copy the processed photos into docs/moments for the website. Returns the list, newest first."""
    import shutil
    os.makedirs(OUT, exist_ok=True)
    items = []
    for pid, rec in idx.items():
        for suf in ("", "-t"):
            src = os.path.join(STORE, f"{pid}{suf}.webp")
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(OUT, f"{pid}{suf}.webp"))
        items.append(dict(rec, id=pid))
    items.sort(key=lambda r: r.get("taken", ""), reverse=True)
    return items


def recent(items, days=WEEK_DAYS):
    cut = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    return [i for i in items if i.get("taken", "") >= cut]


def spotlight_html(items, base=""):
    """Main page: rotates through last week's photos. Empty string (section hidden) if there are none."""
    week = recent(items)[:8]
    if not week:
        return ""
    slides = ""
    for n, p in enumerate(week):
        when = datetime.fromisoformat(p["taken"]).strftime("%a %b %-d")
        meta = " · ".join(x for x in (when, p.get("credit")) if x)
        slides += (f'<a class="mslide{" on" if n == 0 else ""}" href="{base}moments.html#{p["id"]}" '
                   f'data-full="{base}moments/{p["id"]}.webp" data-cap="{e(p.get("caption", ""))}" data-meta="{e(meta)}">'
                   f'<img src="{base}moments/{p["id"]}-t.webp" alt="{e(p.get("caption") or "Photo from a recent night")}" '
                   f'width="96" height="96" {"loading=lazy " if n else ""}decoding="async">'
                   f'<span><span class="spotk">📸 FROM THE FLOOR</span><span class="spotc">{e(p.get("caption", ""))}</span>'
                   f'<span class="spotm">{e(meta)}</span></span></a>')
    dots = "".join(f'<i class="{"on" if n == 0 else ""}"></i>' for n in range(len(week))) if len(week) > 1 else ""
    return (f'<div class="spot mrot" data-n="{len(week)}">{slides}<div class="mdots">{dots}</div>'
            f'<a class="mall" href="{base}moments.html">All moments →</a></div>')


def postcard(p, base=""):
    """One photo between sections: a small picture with its caption, opening the Moments page at that photo."""
    when = datetime.fromisoformat(p["taken"]).strftime("%a %b %-d")
    meta = " · ".join(x for x in (when, p.get("credit")) if x)
    return (f'<a class="spot pcard" href="{base}moments.html#{p["id"]}" data-full="{base}moments/{p["id"]}.webp" '
            f'data-cap="{e(p.get("caption", ""))}" data-meta="{e(meta)}">'
            f'<img src="{base}moments/{p["id"]}-t.webp" alt="{e(p.get("caption") or "Photo from a recent night")}" '
            f'width="96" height="96" loading="lazy" decoding="async">'
            f'<span><span class="spotk">📸 FROM THE FLOOR</span><span class="spotc">{e(p.get("caption", ""))}</span>'
            f'<span class="spotm">{e(meta)}</span></span></a>')


def page_slots(items, base="", n=6):
    """Photos placed down the page, newest first: the first break rotates through the last 7 days,
    the next breaks show the following photos one each. Empty breaks stay empty (nothing shown)."""
    slots = [""] * n
    if not items:
        return slots
    slots[0] = spotlight_html(items, base)
    used = {p["id"] for p in recent(items)[:8]} if slots[0] else set()
    rest = [p for p in items if p["id"] not in used]
    for i, p in enumerate(rest[: n - 1], start=1):
        slots[i] = postcard(p, base)
    return slots


FLOAT_CSS = """
#pf{position:fixed;inset:0;z-index:50;display:flex;align-items:center;justify-content:center;flex-direction:column;
 padding:18px;background:rgba(0,0,0,.72);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);
 opacity:0;pointer-events:none;transition:opacity .22s ease}
#pf.on{opacity:1;pointer-events:auto}
#pf figure{margin:0;max-width:min(92vw,900px);transform:translateY(14px) scale(.92);transition:transform .32s cubic-bezier(.2,.9,.25,1.15)}
#pf.on figure{transform:none}
#pf img{display:block;max-width:100%;max-height:74vh;border-radius:14px;box-shadow:0 24px 70px rgba(0,0,0,.65),0 0 0 1px rgba(255,255,255,.08);
 background:#003e3f}
#pf figcaption{color:#fff;font:15px system-ui,sans-serif;margin-top:12px;text-align:center}
#pf figcaption small{display:block;color:#bbb;font-size:12px;margin-top:4px}
#pf figcaption a{color:#00b9bc;font-size:12px;text-decoration:none;display:inline-block;margin-top:8px}
#pf button{position:absolute;top:14px;right:14px;width:42px;height:42px;border-radius:50%;border:1px solid #fff4;
 background:#0008;color:#fff;font-size:22px;cursor:pointer}
@media (prefers-reduced-motion:reduce){#pf,#pf figure{transition:none}}
"""

FLOAT_JS = r"""<script>
(function(){
 var pf=null,y0=null;
 function close(){if(pf){pf.classList.remove('on');document.documentElement.style.overflow='';}}
 function open(a){
  if(!pf){pf=document.createElement('div');pf.id='pf';pf.setAttribute('role','dialog');pf.setAttribute('aria-modal','true');
   pf.innerHTML='<button type="button" aria-label="Close">×</button><figure><img alt=""><figcaption></figcaption></figure>';
   document.body.appendChild(pf);
   pf.addEventListener('click',function(e){if(e.target===pf||e.target.tagName==='BUTTON')close();});
   pf.addEventListener('touchstart',function(e){y0=e.touches[0].clientY},{passive:true});
   pf.addEventListener('touchend',function(e){if(y0!==null&&e.changedTouches[0].clientY-y0>70)close();y0=null;});
   addEventListener('keydown',function(e){if(e.key==='Escape')close();});}
  var im=pf.querySelector('img'),fc=pf.querySelector('figcaption'),th=a.querySelector('img');
  im.src=th?th.src:'';                       /* show the thumbnail at once, swap to the sharp one when it arrives */
  var big=new Image();big.onload=function(){im.src=big.src};big.src=a.dataset.full;
  im.alt=th?th.alt:'';
  fc.innerHTML='';var t=document.createElement('div');t.textContent=a.dataset.cap||'';fc.appendChild(t);
  if(a.dataset.meta){var m=document.createElement('small');m.textContent=a.dataset.meta;fc.appendChild(m);}
  var l=document.createElement('a');l.href=a.getAttribute('href');l.textContent='All moments →';fc.appendChild(l);
  document.documentElement.style.overflow='hidden';
  requestAnimationFrame(function(){pf.classList.add('on')});
 }
 document.addEventListener('click',function(e){var a=e.target.closest('a[data-full]');if(!a)return;e.preventDefault();open(a);});
})();
</script>"""

ROTATE_JS = r"""<script>
(function(){var box=document.querySelector('.mrot');if(!box)return;
 var s=box.querySelectorAll('.mslide'),d=box.querySelectorAll('.mdots i'),i=0;if(s.length<2)return;
 if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
 setInterval(function(){if(document.hidden)return;s[i].classList.remove('on');if(d[i])d[i].classList.remove('on');
  i=(i+1)%s.length;s[i].classList.add('on');if(d[i])d[i].classList.add('on');},6000);})();
</script>"""

SPOT_CSS = """
.spot{position:relative;background:#00292a;border:1px solid #005254;border-radius:12px;padding:10px;margin:0 0 12px;min-height:116px}
.mslide{display:flex;gap:14px;align-items:center;text-decoration:none;position:absolute;inset:10px 10px 22px 10px;
 opacity:0;transition:opacity .8s ease;pointer-events:none}
.mslide.on{opacity:1;pointer-events:auto;position:relative;inset:auto}
.mslide img{width:96px;height:96px;border-radius:10px;object-fit:cover;display:block;border:1px solid #005254;flex:none}
.mslide>span{display:flex;flex-direction:column;min-width:0}
.spotk{color:#00b9bc;font-size:11px;letter-spacing:2px;font-weight:bold}
.spotc{color:#fff;font-size:15px;margin-top:4px}.spotm{color:#009092;font-size:12px;margin-top:4px}
.mdots{display:flex;gap:5px;justify-content:center;margin-top:6px;min-height:6px}
.mdots i{width:6px;height:6px;border-radius:50%;background:#005254}.mdots i.on{background:#00b9bc}
.mall{position:absolute;right:12px;bottom:6px;font-size:11px;color:#00b9bc;text-decoration:none}
.pcard{display:flex;gap:14px;align-items:center;text-decoration:none;min-height:0}
.pcard img{width:96px;height:96px;border-radius:10px;object-fit:cover;display:block;border:1px solid #005254;flex:none}
.pcard>span{display:flex;flex-direction:column;min-width:0}
"""


def timeline_page(items, home="index.html", style="classic", site_url=""):
    """moments.html: every photo, newest first, grouped by month, with a swipeable full-screen viewer."""
    from collections import OrderedDict
    from digest import theme as _theme
    groups = OrderedDict()
    for p in items:
        t = datetime.fromisoformat(p["taken"])
        groups.setdefault(t.strftime("%B %Y"), []).append((p, t))
    body = ""
    n = 0
    for month, ps in groups.items():
        body += f'<h2 class="mo">{e(month)}</h2><div class="grid">'
        for p, t in ps:
            body += (f'<figure id="{p["id"]}" data-i="{n}" data-full="moments/{p["id"]}.webp">'
                     f'<img src="moments/{p["id"]}-t.webp" alt="{e(p.get("caption") or "")}" width="{THUMB}" height="{THUMB}" '
                     f'{"" if n < 6 else "loading=lazy "}decoding="async">'
                     f'<figcaption><b>{e(p.get("caption", ""))}</b><span>{t:%a %b %-d}{(" · " + e(p["credit"])) if p.get("credit") else ""}</span></figcaption></figure>')
            n += 1
        body += "</div>"
    if not items:
        body = '<p class="empty">No photos yet. Drop one into the shared Drive folder and it shows up after the next run.</p>'
    page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Moments · Mo's House Music Radar</title>
{__import__('digest.ogimage', fromlist=['x']).meta_tags(site_url, "Moments · Mo's House Music Radar", "Photos from the floor at LA house nights.", "moments.html", datetime.now().strftime("%Y%m%d%H"))}
<style>
:root{{color-scheme:dark}}
*{{box-sizing:border-box}}body{{margin:0;background:#001515;color:#fff;font-family:system-ui,-apple-system,sans-serif}}
.wrap{{max-width:980px;margin:0 auto;padding:20px 16px 60px}}
header a{{color:#00b9bc;font:13px monospace;text-decoration:none}}
h1{{font-size:clamp(28px,6vw,44px);margin:10px 0 2px}}.sub{{color:#00a5a7;margin:0 0 10px}}
.mo{{position:sticky;top:0;z-index:2;background:#001515ee;backdrop-filter:blur(6px);margin:22px 0 10px;padding:8px 0;
 font:600 13px monospace;letter-spacing:2px;text-transform:uppercase;color:#00b9bc;border-bottom:1px solid #005254}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}}
figure{{margin:0;background:#00292a;border:1px solid #005254;border-radius:12px;overflow:hidden;cursor:zoom-in;
 transition:transform .2s ease,border-color .2s ease}}
figure:hover{{transform:translateY(-2px);border-color:#00b9bc}}
figure img{{display:block;width:100%;height:auto;aspect-ratio:1/1;object-fit:cover;background:#003e3f}}
figcaption{{padding:10px 12px;display:flex;flex-direction:column;gap:4px}}figcaption b{{font-weight:600}}
figcaption span{{color:#009092;font-size:12px}}.empty{{color:#00a5a7}}
#lb{{position:fixed;inset:0;background:rgba(0,0,0,.78);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);display:flex;opacity:0;pointer-events:none;
 transition:opacity .22s ease;align-items:center;justify-content:center;z-index:9;flex-direction:column;padding:16px}}
#lb.on{{opacity:1;pointer-events:auto}}
#lb img{{max-width:100%;max-height:78vh;border-radius:14px;transition:opacity .25s,transform .32s cubic-bezier(.2,.9,.25,1.15);
 transform:translateY(14px) scale(.92);box-shadow:0 24px 70px rgba(0,0,0,.65),0 0 0 1px rgba(255,255,255,.08)}}
#lb.on img{{transform:none}}
#lb p{{color:#ddd;text-align:center;max-width:680px;margin:12px 0 0}}#lb small{{color:#999}}
#lb button{{position:absolute;top:50%;background:#0008;color:#fff;border:1px solid #fff3;border-radius:999px;width:44px;height:44px;font-size:22px;cursor:pointer}}
#lb .p{{left:12px}}#lb .n{{right:12px}}#lb .x{{top:14px;right:14px}}
@media (prefers-reduced-motion:reduce){{figure,#lb img{{transition:none}}}}
</style></head><body><div class="wrap">
<header><a href="{home}">← Back to the radar</a></header>
<h1>Moments</h1><p class="sub">Photos from the floor, newest first. Tap one to view it full size.</p>
{body}</div>
<div id="lb" role="dialog" aria-modal="true"><button class="x" aria-label="Close">×</button><button class="p" aria-label="Previous">‹</button>
<img alt=""><p></p><button class="n" aria-label="Next">›</button></div>
<script>
(function(){{var f=[].slice.call(document.querySelectorAll('figure')),lb=document.getElementById('lb'),im=lb.querySelector('img'),
 cap=lb.querySelector('p'),i=0,x0=null;
 function show(n){{i=(n+f.length)%f.length;var g=f[i];im.style.opacity=0;im.onload=function(){{im.style.opacity=1}};
  im.src=g.dataset.full;im.alt=g.querySelector('img').alt;cap.innerHTML=g.querySelector('figcaption').innerHTML;
  lb.classList.add('on');history.replaceState(null,'','#'+g.id);
  var nx=f[(i+1)%f.length];if(nx){{(new Image()).src=nx.dataset.full}}}}  /* preload the next one */
 function close(){{lb.classList.remove('on');history.replaceState(null,'',location.pathname)}}
 f.forEach(function(g,n){{g.addEventListener('click',function(){{show(n)}})}});
 lb.querySelector('.n').onclick=function(e){{e.stopPropagation();show(i+1)}};
 lb.querySelector('.p').onclick=function(e){{e.stopPropagation();show(i-1)}};
 lb.querySelector('.x').onclick=close;lb.addEventListener('click',function(e){{if(e.target===lb)close()}});
 addEventListener('keydown',function(e){{if(!lb.classList.contains('on'))return;
  if(e.key==='ArrowRight')show(i+1);else if(e.key==='ArrowLeft')show(i-1);else if(e.key==='Escape')close();}});
 lb.addEventListener('touchstart',function(e){{x0=e.touches[0].clientX}},{{passive:true}});
 lb.addEventListener('touchend',function(e){{if(x0===null)return;var dx=e.changedTouches[0].clientX-x0;
  if(Math.abs(dx)>40)show(i+(dx<0?1:-1));x0=null;}});
 var h=location.hash.slice(1),t=h&&document.getElementById(h);if(t)show(f.indexOf(t));}})();
</script></body></html>"""
    return _theme.apply(page, _theme.choose() if style == "classic" else (style, 0, "set"))
