"""
share.py - "Invite" and "Add to calendar" for each show.
Nothing is stored or sent automatically: every button opens the person's own app
(share sheet, WhatsApp, calendar) with a ready-made message they can edit or cancel.
"""
import html
from datetime import timedelta
from urllib.parse import quote, urlencode

from digest.dates import day_label, to_date

e = html.escape
SITE = "https://lilsnowflakes.github.io/house-music-radar/"

WA_ICON = ('<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" style="vertical-align:-3px">'
           '<circle cx="8" cy="8" r="8" fill="#25d366"/><path d="M4.2 12.2l.6-2.1A4 4 0 1 1 6.3 11.6z" fill="none" '
           'stroke="#fff" stroke-width="1.2" stroke-linejoin="round"/></svg>')
CAL_ICON = ('<svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true" style="vertical-align:-3px">'
            '<rect x="1.5" y="2.5" width="13" height="12" rx="2" fill="#fff" stroke="#8a8a8a"/>'
            '<rect x="1.5" y="2.5" width="13" height="4" rx="2" fill="#e8453c"/>'
            '<rect x="4" y="1" width="1.6" height="3" fill="#555"/><rect x="10.4" y="1" width="1.6" height="3" fill="#555"/></svg>')


def invite_text(ev, site=SITE):
    who = ev.get("artist") or ev.get("title") or "this show"
    where = ev.get("venue", "")
    when = day_label(ev.get("date_str", ""))
    link = ev.get("ticket_url") or site
    return f"I'm going to {who}{' @ ' + where if where else ''}, {when}. You in? 🎟 {link}"


def whatsapp_url(ev, site=SITE):
    # wa.me with no phone number: WhatsApp opens and YOU pick who gets it. Nothing is sent until you hit send.
    return "https://wa.me/?text=" + quote(invite_text(ev, site))


def gcal_url(ev, site=SITE):
    d = to_date(ev.get("date_str", ""))
    if not d:
        return ""
    who = ev.get("artist") or ev.get("title") or "Show"
    details = f"{ev.get('title', '')}\nTickets: {ev.get('ticket_url', '')}\nFrom Mo's House Music Radar: {site}"
    q = {"action": "TEMPLATE", "text": f"{who} @ {ev.get('venue', '')}".strip(" @"),
         "dates": f"{d:%Y%m%d}/{d + timedelta(days=1):%Y%m%d}",
         "location": ", ".join(x for x in (ev.get("venue", ""), ev.get("address") or "Los Angeles, CA") if x),
         "details": details}
    return "https://calendar.google.com/calendar/render?" + urlencode(q)


def buttons_html(ev, color="#00b9bc", site=SITE):
    """Website version: Invite (phone share sheet, falls back to WhatsApp), WhatsApp, and Calendar (Apple .ics or Google)."""
    d = to_date(ev.get("date_str", ""))
    st = (f"color:{color};text-decoration:none;font-size:12px;border:1px solid #005254;border-radius:999px;"
          f"padding:3px 10px;margin:3px 0 3px 6px;display:inline-block;background:none;cursor:pointer;font-family:inherit;")
    data = (f'data-text="{e(invite_text(ev, site))}" data-title="{e((ev.get("artist") or ev.get("title") or "Show") + " @ " + ev.get("venue", ""))}" '
            f'data-date="{d:%Y%m%d}" data-loc="{e(ev.get("venue", ""))}" data-url="{e(ev.get("ticket_url", ""))}"' if d else "")
    out = f'<button type="button" class="inv" {data} style="{st}">📣 Invite</button>'
    out += f'<a href="{e(whatsapp_url(ev, site))}" target="_blank" rel="noopener" title="Send on WhatsApp" style="{st}">{WA_ICON}</a>'
    if d:
        out += (f'<button type="button" class="cal" {data} title="Add to calendar" style="{st}">{CAL_ICON} iCal</button>'
                f'<a href="{e(gcal_url(ev, site))}" target="_blank" rel="noopener" title="Add to Google Calendar" style="{st}">{CAL_ICON} Google Cal</a>')
    return out


def email_links(ev, color="#08524f", site=SITE):
    """Email version: plain links (email apps don't run scripts)."""
    st = f"color:{color};font-size:12px;text-decoration:underline;margin-right:12px;"
    g = gcal_url(ev, site)
    return (f'<a href="{e(whatsapp_url(ev, site))}" style="{st}">Invite on WhatsApp</a>'
            + (f'<a href="{e(g)}" style="{st}">Add to Google Calendar</a>' if g else ""))


SHARE_JS = """<script>
document.addEventListener('click',function(ev){
 var b=ev.target.closest('button.inv,button.cal'); if(!b)return;
 var d=b.dataset;
 if(b.classList.contains('inv')){
  if(navigator.share){navigator.share({text:d.text}).catch(function(){});}
  else{window.open('https://wa.me/?text='+encodeURIComponent(d.text),'_blank','noopener');}
  return;}
 if(!d.date)return;
 var y=d.date.slice(0,4),m=+d.date.slice(4,6)-1,day=+d.date.slice(6,8);
 var n=new Date(Date.UTC(y,m,day+1)),end=n.toISOString().slice(0,10).replace(/-/g,'');
 var esc=function(s){return (s||'').replace(/[\\\;,]/g,function(c){return '\\\\'+c}).replace(/\\n/g,'\\\\n')};
 var ics=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Mo House Music Radar//EN','BEGIN:VEVENT',
  'UID:'+d.date+'-'+Math.random().toString(36).slice(2)+'@house-music-radar',
  'DTSTAMP:'+new Date().toISOString().replace(/[-:]/g,'').slice(0,15)+'Z',
  'DTSTART;VALUE=DATE:'+d.date,'DTEND;VALUE=DATE:'+end,'SUMMARY:'+esc(d.title),'LOCATION:'+esc(d.loc),
  'DESCRIPTION:'+esc('Tickets: '+d.url),'END:VEVENT','END:VCALENDAR'].join('\\r\\n');
 var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([ics],{type:'text/calendar'}));
 a.download='show.ics';document.body.appendChild(a);a.click();a.remove();
});
</script>"""
