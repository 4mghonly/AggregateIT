"""Dedicated Arabic-slide Discord delivery with explicit routing and receipts."""
import os, json, re, time
from contextlib import ExitStack
from urllib.parse import urlsplit, urlunsplit
from pathlib import Path
import requests

class DeliveryError(RuntimeError): pass

def webhook_url(wait=True):
    raw=os.getenv('DISCORD_WEBHOOK_ARABIC','').strip()
    p=urlsplit(raw)
    if p.scheme!='https' or p.hostname not in ('discord.com','discordapp.com') or not re.fullmatch(r'/api(?:/v\d+)?/webhooks/\d+/[A-Za-z0-9_-]+',p.path):
        raise DeliveryError('DISCORD_WEBHOOK_ARABIC is missing or invalid')
    return urlunsplit((p.scheme,p.netloc,p.path,'wait=true' if wait else '',''))

def webhook_info():
    try:
        r=requests.get(webhook_url(wait=False),timeout=(10,20))
    except requests.RequestException:
        raise DeliveryError('Arabic Discord webhook probe failed') from None
    if r.status_code!=200:
        raise DeliveryError(f'Arabic Discord webhook probe HTTP {r.status_code}')
    try: info=r.json()
    except ValueError: raise DeliveryError('Arabic Discord webhook probe returned invalid JSON') from None
    channel=str(info.get('channel_id') or 'unknown')
    webhook_id=str(info.get('id') or 'unknown')
    name=str(info.get('name') or 'unnamed').replace('\n',' ')[:80]
    print(f'Arabic Discord route confirmed: channel_id={channel} webhook_id={webhook_id} name={name}',flush=True)
    return info

def send(state,edition,paths):
    if not paths or any(Path(p).suffix.lower()!='.png' for p in paths):
        raise DeliveryError('DISCORD_WEBHOOK_ARABIC accepts Arabic slide PNGs only')
    paths=[Path(p) for p in paths]
    if any(not p.is_file() for p in paths): raise DeliveryError('One or more Arabic slide files are missing')
    url=webhook_url()
    prior=state.delivery(edition)
    if prior:
        if prior[0]=='sent': return prior[1]
        if prior[0]=='failed': state.clear_delivery(edition)
        else: raise DeliveryError('Edition already reserved; reconcile Discord delivery before retrying')
    if sum(p.stat().st_size for p in paths)>8_000_000: raise DeliveryError('Attachments exceed conservative 8 MB limit')
    state.reserve(edition)
    for attempt in range(2):
        try:
            with ExitStack() as stack:
                files={f'files[{i}]':(p.name,stack.enter_context(p.open('rb')),'image/png') for i,p in enumerate(paths)}
                r=requests.post(url,data={'payload_json':json.dumps({'content':'النشرة الجيوسياسية والعسكرية والأمنية | '+edition+' | بتوقيت الإمارات','allowed_mentions':{'parse':[]}},ensure_ascii=False)},files=files,timeout=(10,60))
        except requests.RequestException:
            state.mark(edition,'uncertain')
            raise DeliveryError('Discord response uncertain; automatic duplicate retry blocked') from None
        if r.status_code==429 and attempt==0:
            try: delay=min(max(float(r.json().get('retry_after',2)),1),30)
            except (ValueError,TypeError): delay=2
            time.sleep(delay); continue
        if r.status_code==429:
            state.mark(edition,'failed'); raise DeliveryError('Discord rate limit persisted after retry')
        if r.status_code!=200:
            state.mark(edition,'uncertain' if r.status_code>=500 else 'failed')
            raise DeliveryError(f'Discord HTTP {r.status_code}; delivery not confirmed')
        try:
            body=r.json(); message_id=str(body['id']); channel_id=str(body.get('channel_id') or 'unknown')
        except (ValueError,KeyError,TypeError):
            state.mark(edition,'uncertain'); raise DeliveryError('Discord message ID missing') from None
        state.mark(edition,'sent',message_id)
        print(f'Arabic Discord delivery confirmed: message_id={message_id} channel_id={channel_id}',flush=True)
        return message_id
    state.mark(edition,'failed')
    raise DeliveryError('Discord delivery retry budget exhausted')
