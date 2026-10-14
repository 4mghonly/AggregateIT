"""Persist bounded host cooldowns after HTTP 429, without sleeping workers."""
import json
import time
import threading
from pathlib import Path
from urllib.parse import urlsplit

STATE=Path(__file__).resolve().parent/'data'/'http_cooldowns.json'
_LOCK=threading.Lock()

def _load():
    try: return json.loads(STATE.read_text())
    except (OSError,ValueError): return {}

def blocked(url):
    return float(_load().get(urlsplit(url).netloc,0))>time.time()

def observe(url,status,headers=None):
    if status!=429: return
    try: wait=float((headers or {}).get('Retry-After',900))
    except (TypeError,ValueError): wait=900
    with _LOCK:
        data=_load();data[urlsplit(url).netloc]=time.time()+min(86400,max(900,wait))
        STATE.parent.mkdir(exist_ok=True)
        tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(data));tmp.replace(STATE)
