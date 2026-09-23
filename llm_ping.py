import os
from urllib.parse import urlsplit
import requests
import llm

def shape(label, base, model, key, fallback=False):
    raw=(base or "").strip().rstrip("/")
    parsed=urlsplit(raw) if raw else None
    path=(parsed.path if parsed else "").rstrip("/")
    openrouter_base=(raw == "https://openrouter.ai/api/v1")
    openrouter_model=((model or "").strip() == "openrouter/free")
    openrouter_key=(key or "").startswith("sk-or-v1-")
    print(
        f"{label} CONFIG:"
        f" complete={llm._route_complete(fallback)}"
        f" https={bool(parsed and parsed.scheme == 'https')}"
        f" has_host={bool(parsed and parsed.netloc)}"
        f" base_ends_chat={path.endswith('/chat/completions')}"
        f" base_ends_v1={path.endswith('/v1')}"
        f" has_query={bool(parsed and parsed.query)}"
        f" model_has_slash={'/' in (model or '')}"
        f" model_looks_url={(model or '').startswith(('http://','https://'))}"
        f" openrouter_base_exact={openrouter_base}"
        f" openrouter_free_exact={openrouter_model}"
        f" openrouter_key_shape={openrouter_key}"
    )
    if raw and key:
        try:
            r=requests.get(raw+"/models",headers=llm._headers(key,fallback),timeout=15)
            print(f"{label} MODELS PROBE: HTTP {r.status_code}")
        except Exception as exc:
            print(f"{label} MODELS PROBE: {type(exc).__name__}")

shape("PRIMARY",llm.BASE_URL,llm.MODEL,llm.API_KEY,False)
shape("FALLBACK",llm.FALLBACK_BASE_URL,llm.FALLBACK_MODEL,llm.FALLBACK_API_KEY,True)
ok,detail=llm.preflight()
print("LLM PREFLIGHT:", "OK" if ok else "FAIL", detail)
if not ok:
    raise SystemExit("No configured LLM route returned HTTP 200")
