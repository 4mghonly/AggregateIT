"""policy.py — Send gating, quiet hours, and volume control.
GST = UTC+4.

General Quiet Hours:
- Mon-Fri 02:00-08:00 GST (22:00-04:00 UTC previous day)
- Weekend: Fri 22:00 GST to Sun 12:00 GST (quiet except limited window)

Slide-Specific Rules (independent from general quiet):
- Mon-Fri: Allowed, EXCEPT 02:00-06:00 GST (4-hour maintenance window)
- Saturday: Completely disabled
- Sunday: Allowed from 13:00 GST (pre-futures open preparation)

Critical alerts always break quiet."""
import time
from datetime import datetime, timezone, timedelta

GST = timezone(timedelta(hours=4))

def is_quiet(ts=None):
    """General quiet hours for briefings/digests/alerts."""
    dt = datetime.fromtimestamp(ts or time.time(), tz=GST)
    wd = dt.weekday()  # 0=Mon, 4=Fri, 5=Sat, 6=Sun
    h = dt.hour

    # Weekend mode: Fri 22:00 GST to Sun 12:00 GST
    if wd == 4 and h >= 22: return True
    if wd == 5:  # Saturday: all quiet
        return True
    if wd == 6:  # Sunday: quiet until 12:00 GST
        return h < 12

    # Weekday quiet: 02:00-08:00 GST
    if 2 <= h < 8: return True
    return False

def is_slide_quiet(ts=None):
    """Slide-specific quiet hours (more permissive)."""
    dt = datetime.fromtimestamp(ts or time.time(), tz=GST)
    wd = dt.weekday()
    h = dt.hour

    # Saturday: completely disabled
    if wd == 5: return True
    
    # Sunday: only allowed from 13:00 GST
    if wd == 6 and h < 13: return True
    
    # Mon-Fri: quiet only 02:00-06:00 GST (4-hour window)
    if wd <= 4 and 2 <= h < 6: return True
    
    return False

def can_send(kind, importance=None):
    """kind: pulse, briefing, digest, slide, daily, alert."""
    if importance == 'Critical': return True
    
    if kind == 'slide':
        return not is_slide_quiet()
    
    # All other content types follow general quiet hours
    return not is_quiet()

def can_send_digest(item):
    """Digest gating: only High/Critical or CONFIRMED."""
    imp = item.get('analysis', {}).get('importance', 'Low')
    status = item.get('status', 'NEW')
    if imp in ('High', 'Critical'): return True
    if status == 'CONFIRMED': return True
    return False

def can_send_alert(item):
    """Alert gating: High/Critical only."""
    imp = item.get('analysis', {}).get('importance', 'Low')
    return imp in ('High', 'Critical')
