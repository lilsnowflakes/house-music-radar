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
    """'past', 'tonight', 'week' (rest of this Mon-Sun week), 'next' (next week), 'later', 'unknown'."""
    today = today or now_pt()
    t = today.date()
    d = to_date(date_str, today)
    if d is None or d.year == 9999:
        return "unknown"
    if d < t:
        return "past"
    if d == t:
        return "tonight"
    week_end = t + timedelta(days=6 - t.weekday())          # this Sunday
    if d <= week_end:
        return "week"
    if d <= week_end + timedelta(days=7):
        return "next"
    return "later"
