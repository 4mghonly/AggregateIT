"""llm.py v4 — central Qwen controller (Update E).
ONE gateway for every Qwen call (engine, briefing, slides).
- Idempotency ledger: identical prompt+model+version never calls the API twice
  (data/qwen_ledger.json, persisted by the existing data/ cache).
- Per-run budget: QWEN_MAX_CALLS (default 40) hard-caps API calls.
- Retries: max ONE retry, transient failures only (429/5xx/timeout).
  4xx (auth/model/path) raise immediately — no wasted retries.
- preflight() validates endpoint+key+model at startup.
- Token usage logged to reports/token_usage.json (per day, with model).
"""
import os, json, time, hashlib, requests
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.environ.get("QWEN_API_KEY", "")
BASE_URL = os.environ.get("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1").rstrip("/")
DEFAULT_MODEL = "qwen3.8-2.4t-a95b"
MODEL = os.environ.get("QWEN_MODEL") or DEFAULT_MODEL
MAX_CALLS = int(os.environ.get("QWEN_MAX_CALLS") or 40)
PROMPT_VERSION = 1
USAGE_FILE = os.path.join(BASE, "reports", "token_usage.json")
LEDGER_FILE = os.path.join(BASE, "data", "qwen_ledger.json")

class BudgetExceeded(RuntimeError): pass
class LLMPermanent(RuntimeError): pass
class LLMTransient(RuntimeError): pass

_calls = 0
print("LLM MODEL:", MODEL, "| budget:", MAX_CALLS)

def _load_json(path, fallback):
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except Exception: return fallback

def _save_json(path, obj):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f: json.dump(obj, f)
    except Exception: pass

def _save_ledger(led):
    if len(led) > 600:
        led = dict(sorted(led.items(), key=lambda kv: kv[1].get("ts", 0), reverse=True)[:400])
    _save_json(LEDGER_FILE, led)

def _ledger_key(model, messages):
    blob = json.dumps(messages, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(("%s|v%d|%s" % (model, PROMPT_VERSION, blob)).encode("utf-8")).hexdigest()

def _log_usage(model, inp, outp, cached=False):
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        data = _load_json(USAGE_FILE, {})
        e = data.get(today, {})
        e["in"] = e.get("in", 0) + int(inp or 0)
        e["out"] = e.get("out", 0) + int(outp or 0)
        e["calls"] = e.get("calls", 0) + (0 if cached else 1)
        e["cached"] = e.get("cached", 0) + (1 if cached else 0)
        e["model"] = model
        data[today] = e
        _save_json(USAGE_FILE, data)
    except Exception: pass

def preflight():
    if not API_KEY: return False, "QWEN_API_KEY missing"
    try:
        r = requests.post(BASE_URL + "/chat/completions",
            headers={"Authorization": "Bearer " + API_KEY, "Content-Type": "application/json"},
            json={"model": MODEL, "messages": [{"role": "user", "content": "ping"}],
                  "max_tokens": 1, "enable_thinking": False}, timeout=20)
        return (True, "ok") if r.status_code == 200 else (False, "HTTP %d %s" % (r.status_code, r.text[:120]))
    except Exception as e:
        return False, str(e)[:120]

def _post(messages, model, temperature, max_tokens, timeout):
    r = requests.post(BASE_URL + "/chat/completions",
        headers={"Authorization": "Bearer " + API_KEY, "Content-Type": "application/json"},
        json={"model": model, "temperature": temperature, "max_tokens": max_tokens,
              "messages": messages, "enable_thinking": False},
        timeout=timeout)
    if r.status_code in (429, 500, 502, 503, 504):
        raise LLMTransient("HTTP %d" % r.status_code)
    if 400 <= r.status_code < 500:
        raise LLMPermanent("HTTP %d %s" % (r.status_code, r.text[:200]))
    r.raise_for_status()
    return r.json()

def chat(messages, model=None, temperature=0.3, timeout=90, max_tokens=2000):
    global _calls
    model = model or MODEL
    key = _ledger_key(model, messages)
    led = _load_json(LEDGER_FILE, {})
    hit = led.get(key)
    if hit and hit.get("status") == "success":
        print("QWEN LEDGER HIT (no API call)")
        _log_usage(model, 0, 0, cached=True)
        return hit["response"]
    if _calls >= MAX_CALLS:
        raise BudgetExceeded("QWEN_MAX_CALLS=%d reached" % MAX_CALLS)
    _calls += 1
    print("QWEN CALL %d/%d model=%s" % (_calls, MAX_CALLS, model))
    last = None
    for attempt in (1, 2):
        try:
            obj = _post(messages, model, temperature, max_tokens, timeout)
            content = obj["choices"][0]["message"]["content"]
            u = obj.get("usage", {})
            _log_usage(model, u.get("prompt_tokens"), u.get("completion_tokens"))
            led[key] = {"status": "success", "model": model, "ts": time.time(), "response": content}
            _save_ledger(led)
            return content
        except LLMTransient as e:
            last = e
            if attempt == 1: time.sleep(2)
        except LLMPermanent as e:
            led[key] = {"status": "failed", "model": model, "ts": time.time(), "error": str(e)[:200]}
            _save_ledger(led)
            raise
        except Exception as e:
            last = e
    led[key] = {"status": "failed", "model": model, "ts": time.time(), "error": str(last)[:200]}
    _save_ledger(led)
    raise last or RuntimeError("llm chat failed")
