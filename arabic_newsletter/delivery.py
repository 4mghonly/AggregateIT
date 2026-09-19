"""Dedicated Arabic-slide Discord delivery. No fallback channel; uncertain sends require reconciliation."""
import os
import json
import re
import time
from contextlib import ExitStack
from urllib.parse import urlsplit, urlunsplit
import requests
from pathlib import Path

class DeliveryError(RuntimeError): pass

def webhook_url():
    raw=os.getenv('DISCORD_WEBHOOK_ARABIC','').strip()
    p=urlsplit(raw)
    if p.scheme!='https' or p.hostname not in ('discord.com','discordapp.com') or not re.fullmatch(r'/api(?:/v\d+)?/webhooks/\d+/[A-Za-z0-9_-]+',p.path):
        raise DeliveryError('DISCORD_WEBHOOK_ARABIC is missing or invalid')
    return urlunsplit((p.scheme,p.netloc,p.path,'wait=true',''))

def send(state,edition,paths):
    # Hard isolation boundary: the Arabic webhook accepts rendered slide PNGs only.
    # Sources, reports, JSON, text files, and any other artifact must never be attached.
    if not paths or any(Path(p).suffix.lower()!='.png' for p in paths):
        raise DeliveryError('DISCORD_WEBHOOK_ARABIC accepts Arabic slide PNGs only')
    paths=[Path(p) for p in paths]
    url=webhook_url()
    prior=state.delivery(edition)
    if prior:
        if prior[0]=='sent': return prior[1]
        # Never blindly repeat an ambiguous POST after a network timeout or crash.
        raise DeliveryError('Edition already reserved; reconcile Discord delivery before retrying')
    if sum(p.stat().st_size for p in paths)>8_000_000: raise DeliveryError('Attachments exceed conservative 8 MB limit')
    state.reserve(edition)
    for attempt in range(2):
        try:
            with ExitStack() as stack:
                files={f'files[{i}]':(p.name,stack.enter_context(p.open('rb')),'image/png') for i,p in enumerate(paths)}
                r=requests.post(url,data={'payload_json':json.dumps({'content':'النشرة الجيوسياسية والعسكرية والأمنية | '+edition+' | بتوقيت الإمارات',
                  'allowed_mentions':{'parse':[]}},ensure_ascii=False)},files=files,timeout=(10,60))
        except requests.RequestException:
            state.mark(edition,'uncertain')
            raise DeliveryError('Discord response uncertain; automatic duplicate retry blocked') from None
        if r.status_code==429 and attempt==0:
            try: delay=min(max(float(r.json().get('retry_after',2)),1),30)
            except (ValueError,TypeError): delay=2
            time.sleep(delay); continue
        if r.status_code!=200:
            state.mark(edition,'uncertain' if r.status_code>=500 else 'failed')
            raise DeliveryError(f'Discord HTTP {r.status_code}; delivery not confirmed')
        try: message_id=str(r.json()['id'])
        except (ValueError,KeyError,TypeError):
            state.mark(edition,'uncertain'); raise DeliveryError('Discord message ID missing') from None
        state.mark(edition,'sent',message_id); return message_id
    raise DeliveryError('Discord rate limited')
