"""analytics.py - optional visitor counting with GoatCounter (free, no cookies, no personal data).
Only added when GOATCOUNTER_CODE is set. Never added to the email."""
import html

from config.config import GOATCOUNTER_CODE


def tag():
    if not GOATCOUNTER_CODE:
        return ""
    code = html.escape(GOATCOUNTER_CODE)
    return (f'<script data-goatcounter="https://{code}.goatcounter.com/count" '
            f'async src="https://gc.zgo.at/count.js"></script>')
