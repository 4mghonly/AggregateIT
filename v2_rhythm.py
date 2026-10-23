"""Planning-only UAE publishing slots; this does NOT configure a scheduler."""
from __future__ import annotations
from datetime import datetime,date,time,timedelta,timezone
UAE=timezone(timedelta(hours=4))

def _day(s):
    if not isinstance(s,str) or len(s)!=10 or s.count('-')!=2:
        raise ValueError('invalid_uae_date')
    try:return date.fromisoformat(s)
    except ValueError as exc:raise ValueError('invalid_uae_date') from exc

def daily_slots(uae_day):
    day=_day(uae_day)
    rows=[]
    for hour in (0,6,12,18):
        dt=datetime.combine(day,time(hour),tzinfo=UAE)
        rows.append({'cadence':'daily','slot_id':dt.isoformat(),'local_hour':hour,
                     'full_morning':hour==6,'schedule_enabled':False,
                     'english_destination':'discord_webhook',
                     'arabic_destination':'discord_webhook_arabic'})
    return rows

def weekly_slot(uae_day):
    day=_day(uae_day)
    if day.weekday()!=6:raise ValueError('not_provisional_weekly_day')
    dt=datetime.combine(day,time(6),tzinfo=UAE)
    return {'cadence':'weekly','slot_id':dt.isoformat(),
            'local_hour':6,'schedule_enabled':False,
            'day_choice':'provisional_sunday',
            'english_destination':'discord_webhook',
            'arabic_destination':'discord_webhook_arabic'}
