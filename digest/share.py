"""
share.py - "Invite" and "Add to calendar" for each show.
Nothing is stored or sent automatically: every button opens the person's own app
(share sheet, WhatsApp, calendar) with a ready-made message they can edit or cancel.
"""
import html
from datetime import timedelta
from urllib.parse import quote, urlencode

from digest.dates import day_label, to_date, show_time

e = html.escape
SITE = "https://lilsnowflakes.github.io/house-music-radar/"

WA_ICON = ('<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" style="vertical-align:-3px">'
           '<circle cx="8" cy="8" r="8" fill="#25d366"/><path d="M4.2 12.2l.6-2.1A4 4 0 1 1 6.3 11.6z" fill="none" '
           'stroke="#fff" stroke-width="1.2" stroke-linejoin="round"/></svg>')
CAL_ICON = ('<svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true" style="vertical-align:-3px">'
            '<rect x="1.5" y="2.5" width="13" height="12" rx="2" fill="#fff" stroke="#8a8a8a"/>'
            '<rect x="1.5" y="2.5" width="13" height="4" rx="2" fill="#e8453c"/>'
            '<rect x="4" y="1" width="1.6" height="3" fill="#555"/><rect x="10.4" y="1" width="1.6" height="3" fill="#555"/></svg>')


def sprite():
    """Every icon drawn once, as CSS backgrounds; each row only carries a tiny <i class="ico i-name">."""
    from urllib.parse import quote as _q
    from digest.artist_links import ICONS, _size
    icons = dict(ICONS, wa=WA_ICON, cal=CAL_ICON)
    css = ".ico{display:inline-block;vertical-align:middle;background:no-repeat center/contain}"
    for k, svg in icons.items():
        w, h = _size(svg)
        svg = svg.replace('aria-hidden="true"', 'xmlns="http://www.w3.org/2000/svg"')
        svg = __import__("re").sub(r'style="[^"]*"', "", svg)
        css += f'.i-{k}{{width:{w}px;height:{h}px;background-image:url("data:image/svg+xml,{_q(svg)}")}}'
    return f"<style>{css}</style>"


def _ic(key, w=16, h=16):
    return f'<i class="ico i-{key}"></i>'


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
    _lab, st, en = show_time(ev)
    if st:
        from datetime import datetime as _dt
        s_ = _dt(d.year, d.month, d.day, int(st[:2]), int(st[3:]))
        e_ = _dt(d.year, d.month, d.day, int(en[:2]), int(en[3:])) if en else s_ + timedelta(hours=4)
        if e_ <= s_:
            e_ += timedelta(days=1)
        dates = f"{s_:%Y%m%dT%H%M%S}/{e_:%Y%m%dT%H%M%S}"
    else:
        dates = f"{d:%Y%m%d}/{d + timedelta(days=1):%Y%m%d}"
    q = {"action": "TEMPLATE", "text": f"{who} @ {ev.get('venue', '')}".strip(" @"), "dates": dates,
         **({"ctz": "America/Los_Angeles"} if st else {}),
         "location": ", ".join(x for x in (ev.get("venue", ""), ev.get("address") or "Los Angeles, CA") if x),
         "details": details}
    return "https://calendar.google.com/calendar/render?" + urlencode(q)


def buttons_html(ev, color="#00b9bc", site=SITE):
    """Website version. The show's details sit once on the wrapper; the page script builds the
    WhatsApp / Google links when tapped, so 400 rows don't each carry four long links."""
    d = to_date(ev.get("date_str", ""))
    loc = ", ".join(x for x in (ev.get("venue", ""), ev.get("address") or "Los Angeles, CA") if x)
    data = (f'data-text="{e(invite_text(ev, site))}" '
            f'data-title="{e((ev.get("artist") or ev.get("title") or "Show") + " @ " + ev.get("venue", ""))}" '
            f'data-loc="{e(loc)}" data-url="{e(ev.get("ticket_url", ""))}"' + (f' data-date="{d:%Y%m%d}"' if d else ""))
    _lab, st, en = show_time(ev)
    if st:
        data += f' data-start="{st}"' + (f' data-end="{en}"' if en else "")
    out = (f'<span class="sbw" {data}><button type="button" class="sb inv">📣 Invite</button>'
           f'<button type="button" class="sb wa" title="Send on WhatsApp">{_ic("wa")}</button>')
    if d:
        out += (f'<button type="button" class="sb cal" title="Add to calendar">{_ic("cal")} iCal</button>'
                f'<button type="button" class="sb gcal" title="Add to Google Calendar">{_ic("cal")} Google Cal</button>')
    return out + "</span>"


def email_links(ev, color="#08524f", site=SITE):
    """Email version: plain links (email apps don't run scripts)."""
    st = f"color:{color};font-size:12px;text-decoration:underline;margin-right:12px;"
    g = gcal_url(ev, site)
    return (f'<a href="{e(whatsapp_url(ev, site))}" style="{st}">Invite on WhatsApp</a>'
            + (f'<a href="{e(g)}" style="{st}">Add to Google Calendar</a>' if g else ""))


SHARE_JS = r"""<script>
document.addEventListener('click',function(ev){
 var b=ev.target.closest('button.inv,button.wa,button.cal,button.gcal'); if(!b)return;
 var d=b.closest('.sbw').dataset, open=function(u){window.open(u,'_blank','noopener');};
 var wa='https://wa.me/?text='+encodeURIComponent(d.text);
 if(b.classList.contains('inv')){ if(navigator.share){navigator.share({text:d.text}).catch(function(){});} else open(wa); return; }
 if(b.classList.contains('wa')){ open(wa); return; }
 if(!d.date)return;
 var y=+d.date.slice(0,4),m=+d.date.slice(4,6)-1,day=+d.date.slice(6,8);
 var end=new Date(Date.UTC(y,m,day+1)).toISOString().slice(0,10).replace(/-/g,'');
 var s0=d.date,e0=end,timed=!!d.start;
 if(timed){ /* local LA wall-clock times; ends next day if the end is "earlier" (e.g. 9pm-2am); 4 hours if unknown */
  var sh=+d.start.slice(0,2),sm=+d.start.slice(3,5),sd=new Date(Date.UTC(y,m,day,sh,sm)),ed;
  if(d.end){var eh=+d.end.slice(0,2),em=+d.end.slice(3,5);ed=new Date(Date.UTC(y,m,day,eh,em));if(ed<=sd)ed=new Date(ed.getTime()+864e5);}
  else ed=new Date(sd.getTime()+4*36e5);
  var f=function(t){return t.toISOString().slice(0,16).replace(/[-:]/g,'')+'00'};s0=f(sd);e0=f(ed);}
 if(b.classList.contains('gcal')){
  open('https://calendar.google.com/calendar/render?action=TEMPLATE&text='+encodeURIComponent(d.title)+'&dates='+s0+'/'+e0+(timed?'&ctz=America/Los_Angeles':'')+
   '&location='+encodeURIComponent(d.loc)+'&details='+encodeURIComponent('Tickets: '+d.url+'\nFrom Mo\'s House Music Radar: '+location.href.split('#')[0]));
  return; }
 var esc=function(s){return (s||'').replace(/[\;,]/g,function(c){return '\\'+c}).replace(/\n/g,'\\n')};
 var ics=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Mo House Music Radar//EN','BEGIN:VEVENT',
  'UID:'+d.date+'-'+Math.random().toString(36).slice(2)+'@house-music-radar',
  'DTSTAMP:'+new Date().toISOString().replace(/[-:]/g,'').slice(0,15)+'Z',
  timed?'DTSTART;TZID=America/Los_Angeles:'+s0:'DTSTART;VALUE=DATE:'+d.date,
  timed?'DTEND;TZID=America/Los_Angeles:'+e0:'DTEND;VALUE=DATE:'+end,'SUMMARY:'+esc(d.title),'LOCATION:'+esc(d.loc),
  'DESCRIPTION:'+esc('Tickets: '+d.url),'END:VEVENT','END:VCALENDAR'].join('\r\n');
 var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([ics],{type:'text/calendar'}));
 a.download='show.ics';document.body.appendChild(a);a.click();a.remove();
});
</script>"""
