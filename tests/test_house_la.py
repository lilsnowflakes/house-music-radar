import os, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.calendars import parse_house_la, _fix_time
from digest.dates import show_time

html = open(os.path.join(os.path.dirname(__file__), "fixtures", "house_la.html"), errors="ignore").read()
evs = parse_house_la(html, today=datetime(2026, 11, 6))
by = {(e["artist"], e["date_str"]): e for e in evs}
a = by[("Adriatique", "Sat Nov 7")]
assert a["venue"] == "Reframe Studios" and a["price"] == "$79+" and show_time(a)[0] == "6pm–12am"
assert by[("Prospa", "Thu Oct 15")]["ticket_status"] == "sold out"
assert ("Clinic", "Wed Nov 11") in by and ("Clinic", "Wed Nov 18") in by, "weeklies become the next two dates"
assert not any("Pomona" in e.get("neighborhood", "") or e["venue"] == "Petco Park" for e in evs), "geo-off rows are outside LA"
assert any(e["artist"] == "Green Velvet" and e["date_str"] == "Sat Jan 2, 2027" for e in evs), "year comes from the link"
assert _fix_time("3 to 9 PM") == "3 PM to 9 PM"
print("HOUSE·LA OK:", len(evs))
