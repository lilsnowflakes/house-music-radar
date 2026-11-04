# House Music Radar (runs on GitHub, not your computer)

Every Monday GitHub runs the script, builds a web page, and emails you the same page.

What you get: announced-but-not-on-sale shows at your Ticketmaster rooms, shows at your
watched venues/promoters (starred), all other LA + Phoenix house shows scored by
Spotify / RA / SoundCloud, and a "Source health" table showing which sources worked.

## Setup (about 20 minutes, once)

1. **GitHub account + repo.** Create a free account, then a new repo (for example
   `house-music-radar`). Upload everything in this folder, including the hidden
   `.github` folder. Free GitHub Pages needs a **public** repo, so the page will be
   public. It contains only show listings, but do not put anything personal in the repo.

2. **Get three free keys.**
   - Spotify: developer.spotify.com/dashboard → Create app → Client ID and Secret.
   - Ticketmaster: developer.ticketmaster.com → get a Discovery API key.
   - Gmail app password (for sending): Google Account → Security → 2-Step Verification
     on → App passwords. Use a Gmail you are fine sending from.

3. **Add secrets.** Repo → Settings → Secrets and variables → Actions → New repository secret.
   Add these names exactly:
   `EMAIL_TO` (where the digest goes: mauricio.escobar80@gmail.com), `EMAIL_FROM`, `EMAIL_PASSWORD`,
   `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `TICKETMASTER_API_KEY`.
   (`SONGKICK_API_KEY` is optional. Without it Songkick is skipped.)

4. **Turn on the website.** Repo → Settings → Pages → Source: **GitHub Actions**.

5. **First run.** Repo → Actions → House Music Radar → Run workflow. When it finishes,
   open the Pages link and read the **Source health** table at the bottom.

## Reading the first run

The scrapers were written without being able to reach the real sites, so expect some
yellow or red rows in Source health on run one. Send the table (or the Actions log) back
and each broken source gets fixed one at a time. Some sites block cloud servers; if one
does, it stays empty and the table will say so.

## Things to know

- Schedule is 16:30 UTC Monday: 8:30am Pacific in winter, 9:30am in summer.
- GitHub pauses scheduled jobs after 60 days with no activity in a public repo. Re-enable
  it from the Actions tab, or push any small change.
- Venue calendars (Sound, Reframe/Framework, Origin, The Spotlight) are read directly. Every act on them
  is genre-checked (Spotify, then MusicBrainz). Not-house acts are dropped and named in Source health;
  acts that cannot be matched are kept with a "?" for you to judge.
- AXS is not covered. Its site blocks automated checks.
- 1001Tracklists is not a source (it has no city listings).
- Edit `config/config.py` to change watched venues, promoters, Ticketmaster rooms, or cities.

## Test on your own machine (optional)

    pip install -r requirements.txt
    python main.py --demo         # fake data, no network
    python main.py --no-email     # real run, no email
