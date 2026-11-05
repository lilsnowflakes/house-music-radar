import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers import la_sources as s

def nd(obj):
    return '<script id="__NEXT_DATA__" type="application/json">' + json.dumps(obj) + '</script>'

ra = nd({"props": {"apolloState": {
    "Event:1": {"title": "Lights Down Low feat. yaego", "date": "2026-11-07T00:00:00.000", "contentUrl": "/events/1",
                "venue": {"__ref": "Venue:9"}, "artists": [{"__ref": "Artist:7"}]},
    "Venue:9": {"name": "Exchange LA"}, "Artist:7": {"name": "Yaego"}}}})
e = s.parse_ra(ra)
assert len(e) == 1 and e[0]["artist"] == "Yaego" and e[0]["venue"] == "Exchange LA" and e[0]["ticket_url"] == "https://ra.co/events/1"

dice = nd({"props": {"pageProps": {"events": [
    {"id": "a1", "name": "Adriatique", "status": "on-sale", "price": {"amount": 7043},
     "dates": {"event_start_date": "2026-11-07T18:00:00-08:00", "sale_start_date": "2026-01-01T09:00:00-08:00"},
     "venues": [{"name": "Reframe Studios Outdoors"}]},
    {"id": "b2", "name": "Future Show", "status": "off-sale", "price": {},
     "dates": {"event_start_date": "2027-05-07T18:00:00-08:00", "sale_start_date": "2099-01-01T09:00:00-08:00"},
     "venues": [{"name": "The Wiltern"}]}]}}})
ev, ann = s.parse_dice(dice)
assert [x["artist"] for x in ev] == ["Adriatique"] and ev[0]["price"] == "$70.43"
assert [x["artist"] for x in ann] == ["Future Show"] and "On sale" in ann[0]["on_sale_text"]

sg = '''<div class="grid"><h2>Fri 6 Nov</h2>
<a href="https://shotgun.live/en/events/x"><div>Nightshift After Hours</div><div>Los Angeles</div><div>Nov 6</div><div>11:00 PM</div><div>$28.38</div><div>House</div><div>Tech House</div><div>+</div><div>2</div></a>
<a href="https://shotgun.live/en/events/y"><div>Metal Night</div><div>Tango</div><div>Nov 6</div><div>9:00 PM</div><div>$10.00</div><div>Metal</div></a></div>'''
r = s.parse_shotgun(sg)
assert len(r) == 1 and r[0]["genres"] == ["house", "tech house"] and r[0]["price"] == "$28.38"

ss = "<main>11.04.26\nTom Jones\nat the Greek Theatre (8:00pm)\n11.06.26\nSome DJ w/ Friend\nat Sound Nightclub (10:00pm)\n</main>"
r = s.parse_scenestar(ss)
assert [x["venue"] for x in r] == ["Sound Nightclub"] and r[0]["artist"] == "Some DJ"
print("LA sources OK")
