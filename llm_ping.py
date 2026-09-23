import os
from urllib.parse import urlsplit
import requests
import llm

def shape(label, base, model, key, fallback=False):
    raw=(base or "").strip().rstrip("/")
    parsed=urlsplit(raw) if raw else None
    path=(parsed.path if parsed else "").rstrip("/")
    host=(parsed.hostname or "").lower() if parsed else ""
    chat_path=llm.FALLBACK_CHAT_PATH if fallback else llm.CHAT_PATH
    effective=llm._endpoint_url(raw,chat_path) if raw else ""
    effective_parsed=urlsplit(effective) if effective else None
    effective_path=(effective_parsed.path if effective_parsed else "").rstrip("/")
    api_root=effective[:-len(chat_path)] if effective and effective.endswith(chat_path) else raw
    print(
        f"{label} CONFIG:"
        f" complete={llm._route_complete(fallback)}"
        f" https={bool(parsed and parsed.scheme == 'https')}"
        f" has_host={bool(parsed and parsed.netloc)}"
        f" base_ends_chat={path.endswith('/chat/completions')}"
        f" base_ends_v1={path.endswith('/v1')}"
        f" effective_ends_chat={effective_path.endswith('/chat/completions')}"
        f" has_query={bool(parsed and parsed.query)}"
        f" model_has_slash={'/' in (model or '')}"
        f" model_looks_url={(model or '').startswith(('http://','https://'))}"
        f" host_openrouter={host == 'openrouter.ai'}"
        f" host_alibaba={host.endswith('aliyuncs.com')}"
        f" path_compatible_mode={'/compatible-mode/v1' in path}"
        f" path_native_api={'/api/v1' in path}"
        f" openrouter_base_exact={raw == 'https://openrouter.ai/api/v1'}"
        f" openrouter_full_exact={raw == 'https://openrouter.ai/api/v1/chat/completions'}"
        f" openrouter_free_exact={(model or '').strip() == 'openrouter/free'}"
        f" openrouter_key_shape={(key or '').startswith('sk-or-v1-')}"
    )
    if api_root and key:
        try:
            headers=llm._headers(key,fallback)
            r=requests.get(api_root.rstrip("/")+"/models",headers=headers,timeout=15)
            print(f"{label} MODELS PROBE: HTTP {r.status_code}")
            if r.status_code==200:
                try:
                    obj=r.json()
                    rows=obj.get("data",[]) if isinstance(obj,dict) else []
                    ids={str(x.get("id","")) for x in rows if isinstance(x,dict)}
                    print(f"{label} MODEL PRESENT: {bool(model and model in ids)} catalog_size={len(ids)}")
                except Exception as exc:
                    print(f"{label} MODELS PARSE: {type(exc).__name__}")
            if host=="openrouter.ai":
                public=requests.get(api_root.rstrip("/")+"/models",timeout=15)
                auth=requests.get(api_root.rstrip("/")+"/key",headers=headers,timeout=15)
                print(f"{label} OPENROUTER PUBLIC MODELS: HTTP {public.status_code}")
                print(f"{label} OPENROUTER KEY CHECK: HTTP {auth.status_code}")
                try:
                    probe=llm._request(raw,key,model,[{"role":"user","content":"ping"}],0,1,20,fallback)
                    msg=""
                    try:
                        obj=probe.json()
                        err=obj.get("error",{}) if isinstance(obj,dict) else {}
                        msg=str(err.get("message") or "") if isinstance(err,dict) else str(err)
                    except Exception:
                        pass
                    low=msg.lower()
                    print(
                        f"{label} CHAT ERROR CLASS:"
                        f" http={probe.status_code}"
                        f" no_endpoints={'no endpoint' in low or 'no allowed provider' in low}"
                        f" model_not_found={'model' in low and ('not found' in low or 'unknown' in low)}"
                        f" auth={'auth' in low or 'api key' in low}"
                        f" rate={'rate' in low or 'limit' in low}"
                        f" tool={'tool' in low}"
                    )
                except Exception as exc:
                    print(f"{label} CHAT ERROR CLASS: {type(exc).__name__}")
        except Exception as exc:
            print(f"{label} MODELS PROBE: {type(exc).__name__}")

shape("PRIMARY",llm.BASE_URL,llm.MODEL,llm.API_KEY,False)
shape("FALLBACK",llm.FALLBACK_BASE_URL,llm.FALLBACK_MODEL,llm.FALLBACK_API_KEY,True)
ok,detail=llm.preflight()
print("LLM PREFLIGHT:", "OK" if ok else "FAIL", detail)
if not ok:
    raise SystemExit("No configured LLM route returned HTTP 200")
