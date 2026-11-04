import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers import venues
from main import day_key
F = os.path.join(os.path.dirname(__file__), "fixtures")
rd = lambda n: open(os.path.join(F, n), encoding="utf-8").read()

d = venues.parse_dice_venue(rd("dice_sound.txt"), "Sound Nightclub", "u", "los_angeles",
                            ["https://dice.fm/event/a", "https://dice.fm/event/b", "https://dice.fm/event/c"])
assert [e["artist"] for e in d] == ["Indo Warehouse", "Locky", "Patrick Topping"], d
assert d[1]["price"] == "$24.93" and d[1]["ticket_url"].endswith("/b")
assert "2027" in d[2]["date_str"]

f = venues.parse_framework(rd("framework.txt"), "u")
assert [e["artist"] for e in f] == ["Adriatique", "Solomun", "Nora En Pure"], [e["artist"] for e in f]
assert "SOLD OUT" in f[1]["title"] and f[0]["venue"] == "Reframe Studios Outdoors"

s = venues.parse_discotech(rd("discotech_spotlight.txt"), "The Spotlight", "u", "los_angeles")
assert [e["artist"] for e in s] == ["Shermanology", "Framework Afterparty ft. Pete Tong"], s  # jazz dropped

assert day_key("Fri: Nov 6 (9pm-2am)") == day_key("Fri Nov 6") == "nov6"
print("venue parsers OK:", len(d), len(f), len(s))
