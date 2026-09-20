"""policy.py — Send gating, quiet hours, and volume control.
GST = UTC+4.

General Quiet Hours for legacy digest/briefing/alert senders:
- Mon-Fri 02:00-08:00 GST (22:00-04:00 UTC previous day)
- Weekend: Fri 22:00 GST to Sun 12:00 GST.

The production Gazette has its own explicit workflow schedule and does not use this
legacy quiet-hours gate. Critical alerts always break quiet."""
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

def can_send(kind, importance=None):
    """kind: pulse, briefing, digest, slide, daily, alert."""
    if importance == 'Critical': return True
    
    # The production Gazette is scheduled independently by slide.yml.
    if kind == 'slide': return True
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
