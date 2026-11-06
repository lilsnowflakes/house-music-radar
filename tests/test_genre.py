import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scoring import genre_check as g

assert g.split_acts("Framework Afterparty ft. Pete Tong") == ["Pete Tong"], g.split_acts("Framework Afterparty ft. Pete Tong")
assert g.split_acts("Kyle Starkey & Paige Tomlinson") == ["Kyle Starkey", "Paige Tomlinson"]
assert g.split_acts("Drumcode LA") == ["Drumcode LA"]

fake = {"Pete Tong": (["house", "uk dance"], "Spotify"), "Emancipator": (["downtempo", "trip hop"], "Spotify"),
        "Mystery Act": ([], ""), "Locky": (["afro house"], "MusicBrainz")}
g.genres_for = lambda n: fake.get(n, ([], ""))
evs = [dict(artist="Framework Afterparty ft. Pete Tong", source="Discotech", genres=["house"]),
       dict(artist="Emancipator", source="Discotech", genres=["house"]),
       dict(artist="Mystery Act", source="DICE venue", genres=["house"]),
       dict(artist="Locky", source="DICE venue", genres=["house"]),
       dict(artist="Whoever", source="19hz", genres=["house"])]
kept, dropped = g.filter_venue_events(evs)
assert [e["artist"] for e in dropped] == ["Emancipator"]
v = {e["artist"]: e.get("house_check", {}).get("verdict") for e in kept}
assert v["Mystery Act"] == "unverified" and v["Locky"] == "house" and v["Whoever"] is None, v
assert g.is_house_genre("melodic house and techno") and g.is_house_genre("melodic techno") and not g.is_house_genre("indie rock")
assert g.split_acts("Clinic Wednesdays: Clinic") == [], "a party/promoter name must not be looked up as a band"
assert g.split_acts("Bedouin Presents: Saga") == ["Bedouin"], "'X Presents: Y' -> the act is X"
assert g.split_acts("Only Fire & Friends - Los Angeles") == ["Only Fire"]
g.genres_for = lambda n: {"nimino": (["electronic", "lidarr"], "MusicBrainz"), "Raw Brigade": (["hardcore punk"], "MusicBrainz")}.get(n, ([], ""))
assert g.verify(dict(artist="nimino"))["verdict"] == "unverified", "vague tags like 'electronic' must not drop a show"
assert g.verify(dict(artist="Raw Brigade"))["verdict"] == "not_house"
print("genre check OK")
