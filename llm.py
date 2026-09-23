"""Provider-agnostic LLM gateway for AggregateIT.
Provider/model selection comes from environment variables mapped from GitHub
Actions Secrets. Primary and fallback routes are independent: either complete
route can operate alone. The API is OpenAI-compatible, but no provider,
endpoint, or model is hard-coded.
"""
import os, json, time, hashlib, requests
from datetime import datetime, timezone
BASE=os.path.dirname(os.path.abspath(__file__))
def _env(name,default=""): return (os.environ.get(name,default) or "").strip()
def _json_env(name):
    raw=_env(name)
    if not raw: return {}
    value=json.loads(raw)
    if not isinstance(value,dict): raise ValueError("%s must contain a JSON object" % name)
    return value
API_KEY=_env("LLM_API_KEY")
BASE_URL=_env("LLM_BASE_URL").rstrip("/")
MODEL=_env("LLM_MODEL")
FALLBACK_API_KEY=_env("LLM_FALLBACK_API_KEY")
FALLBACK_BASE_URL=_env("LLM_FALLBACK_BASE_URL").rstrip("/")
FALLBACK_MODEL=_env("LLM_FALLBACK_MODEL")
AUTH_HEADER=_env("LLM_AUTH_HEADER","Authorization")
AUTH_SCHEME=_env("LLM_AUTH_SCHEME","Bearer")
CHAT_PATH="/"+_env("LLM_CHAT_PATH","chat/completions").lstrip("/")
FALLBACK_AUTH_HEADER=_env("LLM_FALLBACK_AUTH_HEADER","Authorization")
FALLBACK_AUTH_SCHEME=_env("LLM_FALLBACK_AUTH_SCHEME","Bearer")
FALLBACK_CHAT_PATH="/"+_env("LLM_FALLBACK_CHAT_PATH","chat/completions").lstrip("/")
try:
    EXTRA_HEADERS=_json_env("LLM_EXTRA_HEADERS_JSON")
    REQUEST_OPTIONS=_json_env("LLM_REQUEST_OPTIONS_JSON")
    FALLBACK_EXTRA_HEADERS=_json_env("LLM_FALLBACK_EXTRA_HEADERS_JSON")
    FALLBACK_REQUEST_OPTIONS=_json_env("LLM_FALLBACK_REQUEST_OPTIONS_JSON")
    _CONFIG_ERROR=""
except Exception as exc:
    EXTRA_HEADERS={}; REQUEST_OPTIONS={}; FALLBACK_EXTRA_HEADERS={}; FALLBACK_REQUEST_OPTIONS={}
    _CONFIG_ERROR=str(exc)
MAX_CALLS=int(_env("LLM_MAX_CALLS","40") or 40)
PROMPT_VERSION=1
USAGE_FILE=os.path.join(BASE,"reports","token_usage.json")
LEDGER_FILE=os.path.join(BASE,"data","qwen_ledger.json")
class BudgetExceeded(RuntimeError): pass
class LLMPermanent(RuntimeError): pass
class LLMTransient(RuntimeError): pass
_calls=0
_force_fallback=False
print("LLM MODEL:",MODEL or "<not configured>","| budget:",MAX_CALLS)
def _route_complete(fallback=False):
    return bool((FALLBACK_API_KEY and FALLBACK_BASE_URL and FALLBACK_MODEL) if fallback else (API_KEY and BASE_URL and MODEL))
def _headers(key,fallback=False):
    header=FALLBACK_AUTH_HEADER if fallback else AUTH_HEADER
    scheme=FALLBACK_AUTH_SCHEME if fallback else AUTH_SCHEME
    out={"Content-Type":"application/json"}
    out.update(FALLBACK_EXTRA_HEADERS if fallback else EXTRA_HEADERS)
    if header: out[header]=(("%s %s"%(scheme,key)).strip() if scheme else key)
    return out
def _request(base,key,model,messages,temperature,max_tokens,timeout,fallback=False):
    body={"model":model,"messages":messages,"temperature":temperature,"max_tokens":max_tokens}
    body.update(FALLBACK_REQUEST_OPTIONS if fallback else REQUEST_OPTIONS)
    path=FALLBACK_CHAT_PATH if fallback else CHAT_PATH
    return requests.post(base+path,headers=_headers(key,fallback),json=body,timeout=timeout)
def _content_text(message):
    if not isinstance(message,dict): raise ValueError("LLM message must be an object")
    content=message.get("content")
    if isinstance(content,str): return content
    if isinstance(content,dict): return json.dumps(content,ensure_ascii=False)
    if isinstance(content,list):
        parts=[]
        for item in content:
            if isinstance(item,str): parts.append(item)
            elif isinstance(item,dict):
                value=item.get("text") or item.get("content")
                if isinstance(value,str): parts.append(value)
        if parts: return "".join(parts)
    raise ValueError("LLM response content is not usable text")
def _load_json(path,fallback):
    try:
        with open(path,encoding="utf-8") as fh: return json.load(fh)
    except Exception: return fallback
def _save_json(path,obj):
    try:
        os.makedirs(os.path.dirname(path),exist_ok=True)
        with open(path,"w",encoding="utf-8") as fh: json.dump(obj,fh)
    except Exception: pass
def _save_ledger(led):
    if len(led)>600: led=dict(sorted(led.items(),key=lambda kv:kv[1].get("ts",0),reverse=True)[:400])
    _save_json(LEDGER_FILE,led)
def _ledger_key(model,messages):
    blob=json.dumps(messages,ensure_ascii=False,sort_keys=True)
    return hashlib.md5(("%s|v%d|%s"%(model,PROMPT_VERSION,blob)).encode("utf-8")).hexdigest()
def _log_usage(model,inp,outp,cached=False):
    try:
        today=datetime.now(timezone.utc).strftime("%Y-%m-%d"); data=_load_json(USAGE_FILE,{}); e=data.get(today,{})
        e["in"]=e.get("in",0)+int(inp or 0); e["out"]=e.get("out",0)+int(outp or 0)
        e["calls"]=e.get("calls",0)+(0 if cached else 1); e["cached"]=e.get("cached",0)+(1 if cached else 0); e["model"]=model
        data[today]=e; _save_json(USAGE_FILE,data)
    except Exception: pass
def preflight():
    global _force_fallback
    if _CONFIG_ERROR: return False,_CONFIG_ERROR
    if not _route_complete() and not _route_complete(True): return False,"No complete LLM route configured"
    messages=[{"role":"user","content":"ping"}]; last=None
    if _route_complete():
        try:
            r=_request(BASE_URL,API_KEY,MODEL,messages,0,1,20,False)
            if r.status_code==200: return True,"primary-ok"
            last="primary HTTP %d %s"%(r.status_code,(r.text or "")[:120])
        except Exception as exc: last="primary %s"%str(exc)[:120]
    if _route_complete(True):
        try:
            r=_request(FALLBACK_BASE_URL,FALLBACK_API_KEY,FALLBACK_MODEL,messages,0,1,20,True)
            if r.status_code==200: _force_fallback=True; return True,"fallback-ok"
            last="fallback HTTP %d %s"%(r.status_code,(r.text or "")[:120])
        except Exception as exc: last="fallback %s"%str(exc)[:120]
    return False,last or "No configured LLM route returned HTTP 200"
def _decode_or_raise(r):
    if r.status_code in (408,409,425,429,500,502,503,504): raise LLMTransient("HTTP %d"%r.status_code)
    if 400<=r.status_code<500: raise LLMPermanent("HTTP %d %s"%(r.status_code,(r.text or "")[:200]))
    r.raise_for_status(); return r.json()
def _post(messages,temperature,max_tokens,timeout):
    global _force_fallback
    if _CONFIG_ERROR: raise LLMPermanent(_CONFIG_ERROR)
    primary_ready=_route_complete(); fallback_ready=_route_complete(True)
    if not primary_ready and not fallback_ready: raise LLMPermanent("No complete LLM route configured")
    if primary_ready and not _force_fallback:
        try:
            r=_request(BASE_URL,API_KEY,MODEL,messages,temperature,max_tokens,timeout,False)
            if r.status_code==200: return r.json(),MODEL
        except requests.RequestException as exc:
            if not fallback_ready: raise LLMTransient("Primary network %s"%str(exc)[:160]) from None
        if fallback_ready: print("PRIMARY LLM ROUTE FAILED; switching to configured fallback",flush=True)
        else: return _decode_or_raise(r),MODEL
    if fallback_ready:
        try: r=_request(FALLBACK_BASE_URL,FALLBACK_API_KEY,FALLBACK_MODEL,messages,temperature,max_tokens,timeout,True)
        except requests.RequestException as exc: raise LLMTransient("Fallback network %s"%str(exc)[:160]) from None
        obj=_decode_or_raise(r); _force_fallback=True; return obj,FALLBACK_MODEL
    r=_request(BASE_URL,API_KEY,MODEL,messages,temperature,max_tokens,timeout,False)
    return _decode_or_raise(r),MODEL
def chat(messages,temperature=0.3,timeout=90,max_tokens=2000):
    global _calls
    model=FALLBACK_MODEL if _force_fallback and _route_complete(True) else MODEL
    if not model: model=FALLBACK_MODEL
    key=_ledger_key(model or "<unconfigured>",messages); led=_load_json(LEDGER_FILE,{})
    hit=led.get(key)
    if hit and hit.get("status")=="success":
        print("LLM LEDGER HIT (no API call)"); _log_usage(model,0,0,cached=True); return hit["response"]
    if _calls>=MAX_CALLS: raise BudgetExceeded("LLM_MAX_CALLS=%d reached"%MAX_CALLS)
    _calls+=1; print("LLM CALL %d/%d configured_model=%s"%(_calls,MAX_CALLS,model or "<none>")); last=None
    for attempt in (1,2):
        try:
            obj,used_model=_post(messages,temperature,max_tokens,timeout); content=_content_text(obj["choices"][0]["message"]); u=obj.get("usage",{})
            used_model=obj.get("model") or used_model; _log_usage(used_model,u.get("prompt_tokens"),u.get("completion_tokens"))
            led[key]={"status":"success","model":used_model,"ts":time.time(),"response":content}; _save_ledger(led); return content
        except LLMTransient as exc:
            last=exc
            if attempt==1: time.sleep(2)
        except LLMPermanent as exc:
            led[key]={"status":"failed","model":model,"ts":time.time(),"error":str(exc)[:200]}; _save_ledger(led); raise
        except Exception as exc: last=exc
    led[key]={"status":"failed","model":model,"ts":time.time(),"error":str(last)[:200]}; _save_ledger(led)
    raise last or RuntimeError("LLM chat failed")
