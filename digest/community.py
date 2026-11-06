"""
community.py - the "From the floor" photo: one small picture from a recent night.

Reads community/spotlight.txt, makes a web-sized copy and a thumbnail in docs/community/,
and strips all hidden photo data (GPS location, phone model, time) on the way.
"""
import html
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "community")
OUT = os.path.join(ROOT, "docs", "community")
e = html.escape


def read_spotlight():
    try:
        lines = open(os.path.join(SRC, "spotlight.txt"), encoding="utf-8").read().splitlines()
    except OSError:
        return None
    info = {}
    for l in lines:
        l = l.strip()
        if l and not l.startswith("#") and ":" in l:
            k, v = l.split(":", 1)
            info[k.strip().lower()] = v.strip()
    if not info.get("photo") or not os.path.exists(os.path.join(SRC, info["photo"])):
        return None
    return info


def build_images(info):
    """Returns (thumb_path, large_path) relative to docs/, or None if the photo can't be read."""
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return None
    try:
        im = Image.open(os.path.join(SRC, info["photo"]))
        im = ImageOps.exif_transpose(im).convert("RGB")     # keep it upright, then drop all metadata
    except Exception:
        return None
    os.makedirs(OUT, exist_ok=True)
    big = im.copy()
    big.thumbnail((1200, 1200))
    big.save(os.path.join(OUT, "spotlight.jpg"), "JPEG", quality=82, optimize=True)   # no exif= -> no GPS
    th = ImageOps.fit(im, (240, 240))
    th.save(os.path.join(OUT, "spotlight-thumb.jpg"), "JPEG", quality=80, optimize=True)
    return "community/spotlight-thumb.jpg", "community/spotlight.jpg"


def spotlight_html(base=""):
    info = read_spotlight()
    if not info:
        return ""
    paths = build_images(info)
    if not paths:
        return ""
    th, big = paths
    meta = " · ".join(x for x in (info.get("date"), info.get("credit")) if x)
    return (f'<div class="spot"><a href="{base}{big}" target="_blank" rel="noopener">'
            f'<img src="{base}{th}" alt="{e(info.get("caption", "Photo from a recent night"))}" width="96" height="96" loading="lazy"></a>'
            f'<div><div class="spotk">📸 FROM THE FLOOR</div><div class="spotc">{e(info.get("caption", ""))}</div>'
            f'<div class="spotm">{e(meta)}</div></div></div>')
