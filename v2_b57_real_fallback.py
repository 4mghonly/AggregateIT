"""B57 original Arabic failover orchestration with real OpenRouter fallback.

User-authorized USD 0.50 cumulative. Two self-authored EN/SO samples maximum;
primary transport failures are *injected* to test the actual production
failover controller, while fallback calls real GPT OSS provider once each.
No provider secrets, response bodies or source texts persisted to artifacts.
"""
from __future__ import annotations
import json,os
from datetime import datetime,timezone
from unittest.mock import patch
import requests
import arabic_live_v2 as producer
from v2_b55_budgeted_models import API,_usage_cost
from v2_b56_second_provider import CAP,PRIOR_B55_RESERVED,PRIOR_B55_SPENT,reserve

PRIOR_B56_RESERVED=0.074446
PRIOR_B56_SPENT=0.0023537
MODEL="openai/gpt-oss-120b"
MAX_FALLBACK_CALLS=2
MAX_COMPLETION=700

def _row(language):
    if language=="en":
        title="Somalia officials proposed 12 clinics on 27 October."
        summary="The plan has not been approved; no clinic has opened."
    elif language=="so":
        title="Mas'uuliyiinta Soomaaliya waxay soo jeediyeen 12 xarumood 27 Oktoobar."
        summary="Qorshaha lama ansixin, mana jirin xarun la furay."
    else:raise ValueError("disallowed_eval_language")
    return {"title":title,"summary":summary,"language":language,
            "source":"synthetic-b57","source_id":"synthetic-b57-"+language}

def evaluate(*,api_key=None,transport=None):
    if api_key is None:api_key=os.environ.get("OPENROUTER_API_KEY","")
    if not api_key:
        return {"schema":"aggregateit-v2-b57-real-fallback/1","status":"HOLD_API_KEY_MISSING",
                "actual_fallback_calls":0,"can_release":False}
    sender=transport or requests.post
    liability=0.;billed=0.;calls=0;records=[]
    for lang in ("en","so"):
        source=_row(lang)
        captured=[]
        def route(prefix):
            if prefix=="ARABIC_LLM_":
                return {"model":"simulated-primary-transport-failure","role":"primary"}
            if prefix=="ARABIC_LLM_FALLBACK_":
                return {"model":MODEL,"role":"fallback"}
            raise ValueError("unapproved_route")
        def route_call(route,system,user,max_tokens,deadline=None):
            nonlocal calls,liability,billed
            if route["role"]=="primary":
                raise RuntimeError("simulated_primary_outage")
            if route["role"]!="fallback" or route["model"]!=MODEL:
                raise RuntimeError("unsafe_fallback_model")
            if calls>=MAX_FALLBACK_CALLS:
                raise RuntimeError("fallback_call_limit")
            request=json.dumps(user,ensure_ascii=False)
            prompt=system+"\nTranslate to Arabic and preserve 12, 27 and negation. Return only exact items JSON."
            reservation=reserve(prompt+request,"fallback")
            if PRIOR_B56_RESERVED+liability+reservation>CAP:
                raise RuntimeError("cumulative_budget_hold")
            liability+=reservation;calls+=1
            payload={"model":MODEL,
                "messages":[{"role":"system","content":prompt},
                 {"role":"user","content":request}],
                "temperature":0,"max_tokens":MAX_COMPLETION,
                "response_format":{"type":"json_object"},
                "usage":{"include":True}}
            response=sender(API,headers={"Authorization":"Bearer "+api_key,
                 "Content-Type":"application/json"},
                 json=payload,timeout=(7,35),allow_redirects=False)
            try:
                if response.status_code!=200:raise RuntimeError("http_"+str(response.status_code))
                if len(response.content)>30000:raise RuntimeError("oversized_response")
                data=response.json()
                cost=_usage_cost(data)
                if cost is not None:
                    billed+=cost
                    if cost>reservation or PRIOR_B56_SPENT+billed>CAP:
                        raise RuntimeError("provider_price_outside_reserved_budget")
                if not isinstance(data,dict) or not data.get("choices"):
                    raise RuntimeError("empty_chat_choices")
                row=data["choices"][0]
                if row.get("finish_reason") in ("length","content_filter"):
                    raise RuntimeError("truncated_or_blocked")
                content=row.get("message",{}).get("content")
                if not isinstance(content,str) or len(content)>12000:
                    raise RuntimeError("invalid_content_format")
                fence=chr(96)*3
                content=content.strip()
                if content.startswith(fence+"json") and content.endswith(fence):
                    content=content[len(fence)+4:-len(fence)].strip()
                return json.loads(content)
            finally:
                response.close()
        with patch.object(producer,"_route",side_effect=route),patch.object(producer,"_route_call",side_effect=route_call):
            try:
                translated,health,selected=producer.translate_items_with_failover([source])
                good=selected=="fallback" and len(translated)==1
                output=translated[0] if good else {}
                source_numbers=producer._numbers(source["title"]+" "+source["summary"])
                translated_numbers=producer._numbers(output.get("title_ar","")+" "+output.get("summary_ar",""))
                good=good and source_numbers==translated_numbers and producer.is_arabic(
                    output.get("title_ar","")+" "+output.get("summary_ar",""))
                negative=any(x in output.get("summary_ar","") for x in ("لم","لا ","ليس","غير","دون"))
                good=good and negative
                records.append({"language":lang,"actual_fallback_called":bool(calls),
                     "production_controller_selected_fallback":selected=="fallback",
                     "structural_pass":bool(good),
                     "result":"STRUCTURAL_PASS" if good else "HOLD_OUTPUT_QUALITY"})
            except Exception as exc:
                records.append({"language":lang,"result":"HOLD_"+type(exc).__name__,
                    "structural_pass":False})
    return {"schema":"aggregateit-v2-b57-real-fallback/1","status":"HELD_ORCHESTRATION_REHEARSAL",
        "checked_at":datetime.now(timezone.utc).isoformat(),
        "actual_fallback_calls":calls,"records":records,
        "cumulative_reported_usd":round(PRIOR_B56_SPENT+billed,8),
        "cumulative_reserved_usd":round(PRIOR_B56_RESERVED+liability,8),
        "authorized_cap_usd":CAP,
        "primary_outage":"SIMULATED_NOT_ACTUAL",
        "fallback_endpoint":"REAL_PROVIDER",
        "live_full_production_fallback_verified":False,
        "genuine_news_story_translation_verified":False,
        "model_semantic_equivalence_verified":False,
        "original_publisher_text_sent":False,
        "discord_sent":False,"can_release":False}
if __name__=="__main__":
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    result=evaluate()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"calls":result["actual_fallback_calls"],
        "records":[(x["language"],x["result"]) for x in result.get("records",[])],
        "total_usd":result.get("cumulative_reported_usd"),
        "reserved_usd":result.get("cumulative_reserved_usd"),
        "can_release":False}))
