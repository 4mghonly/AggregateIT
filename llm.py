"""llm.py — Unified Qwen API wrapper with automatic token usage tracking.
Logs input/output tokens to reports/token_usage.json for daily auditing."""
import os, json, time, requests

BASE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(BASE, "reports")
USAGE_FILE = os.path.join(REPORTS, "token_usage.json")

def _log_usage(model, in_tokens, out_tokens):
    try:
        os.makedirs(REPORTS, exist_ok=True)
        data = {}
        if os.path.exists(USAGE_FILE):
            with open(USAGE_FILE) as f: data = json.load(f)
        day = time.strftime("%Y-%m-%d")
        if day not in data: data[day] = {"in": 0, "out": 0, "calls": 0}
        data[day]["in"] += in_tokens
        data[day]["out"] += out_tokens
        data[day]["calls"] += 1
        with open(USAGE_FILE, "w") as f: json.dump(data, f, indent=2)
    except Exception: pass

def chat(messages, model=None, temperature=0.3, timeout=90):
    """Drop-in replacement for direct requests.post to Qwen."""
    base = os.environ.get("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1").rstrip("/")
    model = model or os.environ.get("QWEN_MODEL", "qwen3.8-2.4t-a95b")
    r = requests.post(base + "/chat/completions",
        headers={"Authorization": "Bearer " + os.environ["QWEN_API_KEY"]},
        json={
            "model": model, 
            "temperature": temperature, 
            "max_tokens": 4000, 
            "messages": messages, 
            "enable_thinking": False
        }, 
        timeout=timeout)
    r.raise_for_status()
    res = r.json()
    usage = res.get("usage", {})
    _log_usage(model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
    return res["choices"][0]["message"]["content"]
