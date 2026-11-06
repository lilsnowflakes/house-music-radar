"""
House Music Radar — configuration.

Secrets come from environment variables (GitHub "Secrets" when it runs
on GitHub). Nothing private is stored in this file.
"""

import os


def env(name, default=""):
    return os.environ.get(name, default).strip()


# --- DELIVERY ---------------------------------------------------------
EMAIL_TO = env("EMAIL_TO")                 # where the digest is sent
EMAIL_FROM = env("EMAIL_FROM")             # Gmail account that sends it
EMAIL_PASSWORD = env("EMAIL_PASSWORD")     # Gmail app password
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SITE_URL = env("SITE_URL")                 # set by the workflow

# --- API KEYS (all free) ---------------------------------------------
SPOTIFY_CLIENT_ID = env("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = env("SPOTIFY_CLIENT_SECRET")
TICKETMASTER_API_KEY = env("TICKETMASTER_API_KEY")
SEATGEEK_CLIENT_ID = env("SEATGEEK_CLIENT_ID")      # free: seatgeek.com/account/develop
EDMTRAIN_CLIENT_KEY = env("EDMTRAIN_CLIENT_KEY")    # free on request: edmtrain.com/developer-api
SONGKICK_API_KEY = env("SONGKICK_API_KEY")  # optional

# --- WINDOWS ----------------------------------------------------------
DAYS_AHEAD = 30              # house shows: next 30 days
TM_LOOKAHEAD_DAYS = 180      # announced-not-on-sale: look further out
YOUTUBE_SET_LOOKBACK_DAYS = 60

# --- CITIES AND SOURCES ----------------------------------------------
CITIES = ["los_angeles"]

SOURCES = {
    "los_angeles": ["19hz", "resident_advisor", "dice", "shotgun", "scenestar",
                    "venue_calendars", "heard", "seatgeek", "edmtrain", "calendars"],
}
# Note: 1001Tracklists has no city listings, so it is not a source here.

HOUSE_GENRES = [
    "house", "deep house", "tech house", "afro house", "progressive house",
    "melodic house", "organic house", "funky house", "soulful house",
    "nu-disco", "disco", "garage", "uk garage", "minimal", "mushroom jazz",
    "latin house",
]

SCORE_WEIGHTS = {
    "spotify_listeners": 0.50,
    "ra_followers": 0.30,
    "soundcloud_followers": 0.20,
}

# --- WATCH LIST (built from your DICE / Eventbrite / Ticketmaster history)
# A show gets a star if its venue, title or lineup text contains any of these.
WATCH_VENUES = {
    "los_angeles": [
        "Sound Nightclub", "The Spotlight", "Jungle Hollywood",
        "Reframe Studios", "Union Station", "Dream Rooftop", "The Rose Room",
        "Golden Hour", "Level 8", "ORIGIN", "Kiss Kiss Bang Bang",
        "Hotel Ziggy", "Pershing Square", "Grand Park", "City Market",
        "Optimist Studios", "6th St Bridge", "Gin Ling Way",
        "Santa Monica Pier", "Moroccan Lounge", "The Wiltern", "The Novo",
        "Pacific Electric", "Hollywood Palladium",
        "El Rey Theatre", "Fonda Theatre", "Greek Theatre", "Peacock Theater",
        "Santa Barbara Bowl",
    ],
}

# Pop-up nights move around, so promoters are watched too.
WATCH_PROMOTERS = [
    "Framework", "Stranger Than", "Sound Presents", "Clinic",
    "All Day I Dream", "Blind Tiger", "Boiler Room", "SBCLTR",
    "Techno Night Market", "Venice Gets Deep", "Knee Deep", "Mayan Warrior",
    "Sun Sequence",
]

# Artists you have bought AXS tickets for (house / melodic). Shows with these names get a star.
WATCH_ARTISTS = ["Le Youth", "Lane 8", "Disclosure", "Christian Löffler",
                 "Christian Loffler", "New Constellations", "Full Crate"]

# --- TICKETMASTER ROOMS (announced-but-not-on-sale check) -------------
# (venue name as Ticketmaster lists it, state code)
TICKETMASTER_VENUES = {
    "los_angeles": [
        ("The Moroccan Lounge", "CA"), ("The Wiltern", "CA"),
        ("The Novo", "CA"), ("Pacific Electric", "CA"),
        ("Hollywood Palladium", "CA"), ("Hollywood Bowl", "CA"),
        ("Kia Forum", "CA"), ("The Torch", "CA"),
    ],
}


# --- VENUE CALENDARS (read directly, one venue at a time) -------------
# kind: discotech | dice_venue | framework. Only rooms that host house music.
VENUE_CALENDARS = {
    "los_angeles": [
        {"venue": "Sound Nightclub", "kind": "dice_venue",
         "url": "https://dice.fm/venue/sound-nightclub-kxeo"},
        {"venue": "Reframe Studios / Framework", "kind": "framework",
         "url": "https://thisisframework.com/events"},
        {"venue": "Origin", "kind": "discotech",
         "url": "https://app.discotech.me/los-angeles/origin"},
        {"venue": "The Spotlight", "kind": "discotech",
         "url": "https://app.discotech.me/los-angeles/the-spotlight"},
    ],
}
# Calendar entries containing these words are dropped (jazz nights, comedy, passes).
VENUE_SKIP_WORDS = ["jazz", "comedy", "season 2 passes", "two-day pass"]


# --- VENUE ADDRESSES AND LINKS ---------------------------------------
# Only addresses seen on the venues' own listings (DICE, Discotech) are filled in.
# Any other venue still gets a Google Maps link, searched by name + "Los Angeles, CA".
VENUE_ADDRESSES = {
    "sound nightclub": "1642 N Las Palmas Ave, Los Angeles, CA 90028",
    "the spotlight": "1601 N Cahuenga Blvd, Los Angeles, CA",
    "origin": "613 Imperial St, Los Angeles, CA",
}

# Venues that have a page on getheard.live (names as Heard writes them, lowercased).
HEARD_VENUES = {
    "el cid": "el-cid", "club tee gee": "club-tee-gee", "slipper clutch": "slipper-clutch",
    "jungle hollywood": "jungle-hollywood", "la cita": "la-cita", "silverlake lounge": "silverlake-lounge",
    "the association": "the-association", "johnny's cocktails & hi-fi": "johnny-s-cocktails-and-hi-fi",
    "the short stop": "the-short-stop", "the room hollywood": "the-room-hollywood",
    "general lee's": "general-lee-s", "boardner's": "boardner-s", "loulou": "loulou",
    "the grayson": "the-grayson", "gold line": "gold-line", "palomino": "palomino",
    "juju social club": "juju-social-club", "animal la": "animal-la", "good housekeeping": "good-housekeeping",
    "footsie's": "footsie-s", "the little joy": "the-little-joy",
}
HEARD_HOME = "https://getheard.live/"


# --- VERSION AND THEME -------------------------------------------------
CODE_VERSION = "2026.11.05"   # bump when the code changes; shown on the page and in the email
# Color theme: edit config/theme.txt (one word). "auto" rotates to a new color every run.
