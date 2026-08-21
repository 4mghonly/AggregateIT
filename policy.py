"""policy.py — Send gating, quiet hours, and volume control.
GST = UTC+4.
Quiet: Mon-Fri 02:00-08:00 GST (22:00-04:00 UTC).
Weekend: Fri 22:00 GST to Sun 00:00 GST, EXCEPT Sat/Sun 08:00-12:00 GST (04:00-08:00 UTC).
Critical always breaks quiet."""
import time
from datetime import datetime, timezone, timedelta

GST = timezone(timedelta(hours=4))

def is_quiet(ts=None):
    dt = datetime.fromtimestamp(ts or time.time(), tz=GST)
    wd = dt.weekday()  # 0=Mon, 4=Fri, 5=Sat, 6=Sun
    h = dt.hour

    # Weekend mode: Fri 22:00 GST to Sun 00:00 GST
    if wd == 4 and h >= 22: return True
    if wd == 5:  # Saturday: quiet except 08:00-12:00 GST
        return not (8 <= h < 12)
    if wd == 6:  # Sunday: quiet except 08:00-12:00 GST
        return not (8 <= h < 12)

    # Weekday quiet: 02:00-08:00 GST
    if 2 <= h < 8: return True
    return False

def can_send(kind, importance=None):
    """kind: pulse, briefing, digest, slide, daily, alert.
    importance: Low, Medium, High, Critical."""
    if importance == 'Critical': return True
    if is_quiet(): return False
    return True

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
