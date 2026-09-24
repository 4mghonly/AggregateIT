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
    expected=(os.getenv('DISCORD_ARABIC_EXPECTED_CHANNEL_ID') or '').strip()
    if expected and channel!=expected:
        raise DeliveryError(f'Arabic Discord webhook points to channel {channel}, expected {expected}')
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
        if prior[0]=='failed':
            state.clear_delivery(edition)
            prior=None
        else:
            raise DeliveryError('Edition already reserved; reconcile Discord delivery before retrying')
    # Discord documents a 20 MB free upload limit per file as of Aug 2026.
    # Keep a 1 MB safety margin and upload each slide independently so a valid
    # 4K deck is never rejected by an obsolete aggregate-size cap.
    max_file_bytes=int(os.getenv('ARABIC_DISCORD_MAX_FILE_BYTES','19000000') or 19000000)
    oversized=[p.name for p in paths if p.stat().st_size>max_file_bytes]
    if oversized:
        raise DeliveryError('Arabic slide exceeds Discord per-file safety limit: '+','.join(oversized))

    # Deliver the complete three-slide deck as ONE Discord message.
    # Discord supports multiple attachments in one webhook message; the safety
    # ceiling remains per file rather than aggregate.
    state.reserve(edition)
    expected=(os.getenv('DISCORD_ARABIC_EXPECTED_CHANNEL_ID') or '').strip()
    response=None
    last_error=None

    for attempt in range(3):
        try:
            with ExitStack() as stack:
                files={
                  f'files[{i}]':(p.name,stack.enter_context(p.open('rb')),'image/png')
                  for i,p in enumerate(paths)
                }
                payload={
                  'content':f'النشرة الجيوسياسية والأمنية | {edition} | بتوقيت الإمارات',
                  'allowed_mentions':{'parse':[]}
                }
                response=requests.post(
                  url,
                  data={'payload_json':json.dumps(payload,ensure_ascii=False)},
                  files=files,
                  timeout=(10,90)
                )
        except requests.RequestException as exc:
            # A network exception after upload begins is ambiguous. Do not retry
            # automatically and risk duplicate publication.
            state.mark(edition,'uncertain')
            raise DeliveryError('Discord response uncertain after deck upload; duplicate retry blocked') from None

        if response.status_code==429:
            try: delay=min(max(float(response.json().get('retry_after',2)),1),30)
            except (ValueError,TypeError): delay=2
            last_error='http_429'
            time.sleep(delay)
            continue
        if response.status_code>=500:
            last_error=f'http_{response.status_code}'
            time.sleep(min(2**attempt,8))
            continue
        if response.status_code!=200:
            state.mark(edition,'failed')
            raise DeliveryError(f'Discord HTTP {response.status_code} during deck upload')

        try:
            body=response.json()
            message_id=str(body['id'])
            channel_id=str(body.get('channel_id') or 'unknown')
        except (ValueError,KeyError,TypeError):
            state.mark(edition,'uncertain')
            raise DeliveryError('Discord deck receipt missing message ID') from None

        if expected and channel_id!=expected:
            state.mark(edition,'failed')
            raise DeliveryError(f'Arabic Discord receipt channel mismatch: {channel_id} != {expected}')

        state.mark(edition,'sent',message_id)
        print(f'Arabic Discord deck confirmed in one message: message_id={message_id} channel_id={channel_id}',flush=True)
        return message_id

    state.mark(edition,'failed')
    raise DeliveryError(f'Discord deck upload failed after retries: {last_error or "unknown"}')
