"""dates.py - date helpers shared by the pages and the de-duplicator."""
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")
MON = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}


def now_pt():
    return datetime.now(PACIFIC)


def day_key(date_str):
    """'Fri: Nov 6 (9pm-2am)' and 'Fri Nov 6' both become 'nov6'."""
    m = re.search(r"([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2})", re.sub(r"^[A-Za-z]{3,9}:?\s", "", date_str or ""))
    return (m.group(1).lower() + m.group(2)) if m else (date_str or "")


def sort_key(date_str, today=None):
    """(year, month, day) for a listing; (9999,12,31) when the date can't be read."""
    today = today or now_pt()
    m = re.search(r"([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2})(?:,\s*(\d{4}))?",
                  re.sub(r"^[A-Za-z]{3,9}:?\s", "", date_str or ""))
    if not m or m.group(1).lower() not in MON:
        return (9999, 12, 31)
    mo, d = MON[m.group(1).lower()], int(m.group(2))
    y = int(m.group(3)) if m.group(3) else today.year + (1 if mo < today.month - 1 else 0)
    return (y, mo, d)


def day_label(date_str):
    return re.sub(r"\s*\(.*$", "", (date_str or "").replace(": ", " ")).strip()


def to_date(date_str, today=None):
    y, m, d = sort_key(date_str, today)
    try:
        return date(y, m, d)
    except ValueError:
        return None


def bucket(date_str, today=None):
    """'past', 'tonight', 'tomorrow', 'week' (rest of this Mon-Sun week), 'next' (next week), 'later', 'unknown'."""
    today = today or now_pt()
    # Nightlife day: until 6am it's still "last night". At 2am Friday, Thursday's party is still Tonight.
    t = (today - timedelta(hours=6)).date()
    d = to_date(date_str, today)
    if d is None or d.year == 9999:
        return "unknown"
    if d < t:
        return "past"
    if d == t:
        return "tonight"
    if d == t + timedelta(days=1):
        return "tomorrow"
    week_end = t + timedelta(days=6 - t.weekday())          # this Sunday
    if d <= week_end:
        return "week"
    if d <= week_end + timedelta(days=7):
        return "next"
    return "later"


_T = re.compile(r"(?i)\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b")


def _hm(m):
    h, mi, ap = int(m.group(1)), int(m.group(2) or 0), m.group(3).lower()
    if h == 12:
        h = 0
    return h + (12 if ap == "pm" else 0), mi


def show_time(ev):
    """Best start/end time we can find: a DICE timestamp, '(9pm-2am)' in a 19hz date, '(10PM)' in a Heard title.
    Returns (label, 'HH:MM' start, 'HH:MM' end) or ("", "", "")."""
    iso = ev.get("start_iso") or ""
    m = re.search(r"T(\d{2}):(\d{2})", iso)
    if m and m.group(1) + m.group(2) != "0000":
        h, mi = int(m.group(1)), int(m.group(2))
        lab = datetime(2000, 1, 1, h, mi).strftime("%-I:%M%p").replace(":00", "").lower()
        return lab, f"{h:02d}:{mi:02d}", ""
    for text in (ev.get("date_str", ""), ev.get("title", ""), ev.get("time_text", "")):
        paren = re.findall(r"\(([^)]*)\)", text or "") or ([text] if text is ev.get("time_text") else [])
        for p in paren:
            ts = list(_T.finditer(p))
            if ts:
                s = _hm(ts[0])
                e = _hm(ts[1]) if len(ts) > 1 else None
                lab = ts[0].group(0).lower().replace(" ", "") + (f"–{ts[1].group(0).lower().replace(' ', '')}" if e else "")
                return lab, f"{s[0]:02d}:{s[1]:02d}", (f"{e[0]:02d}:{e[1]:02d}" if e else "")
    return "", "", ""
