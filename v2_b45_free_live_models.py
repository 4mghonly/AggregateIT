"""B45 live, bounded FREE-only English/Somali→Arabic probe; synthetic input only."""
from datetime import datetime,timezone
from hashlib import sha256
from urllib.parse import urlsplit
from arabic_live_v2 import _route,_route_call,TRANSLATE_SYSTEM
from v2_b45_source_translation_review import inspect_translations

def free_route_guard(route):
    if not isinstance(route,dict):return "NOT_CONFIGURED"
    p=urlsplit(route.get("base",""))
    model=route.get("model")
    if (p.scheme!="https" or p.hostname!="openrouter.ai" or
        not p.path.startswith("/api/v1") or route.get("chat")!="/chat/completions" or
        not isinstance(model,str) or not (model=="openrouter/free" or model.endswith(":free")) or
        not isinstance(route.get("key"),str) or not route["key"]):
        return "NOT_VERIFIED_FREE_ROUTE"
    if route.get("options"):return "UNAPPROVED_ROUTE_OPTIONS"
    return "FREE_ROUTE_CONFIGURED"

def fixture(lang):
    if lang=="en":
        title="Somalia officials discussed plans for 12 clinics on 27 October."
        summary="The planned opening was not confirmed and was only a proposal."
    elif lang=="so":
        title="Mas'uuliyiinta Soomaaliya waxay ka hadleen qorshaha 12 xarumood 27 Oktoobar."
        summary="Furitaanka lama xaqiijin waxaana la sheegay in uu yahay qorshe keliya."
    else:raise ValueError("invalid_original_language")
    digest=sha256((lang+"\n"+title+"\n"+summary).encode()).hexdigest()
    return {"source_id":"synthetic-"+lang,"language":lang,"title":title,
            "summary":summary,"source_sha256":digest}

def run_probe(*,primary=None,fallback=None,caller=None,resolve_env=True,one_english_retry=False):
    if caller is None:caller=_route_call
    routes={"primary":primary if primary is not None else (_route("ARABIC_LLM_") if resolve_env else {}),
            "fallback":fallback if fallback is not None else (_route("ARABIC_LLM_FALLBACK_") if resolve_env else {})}
    outcome={};calls=0
    for route_name,lang in (("primary","en"),("primary","so"),("fallback","en")):
        route=routes[route_name]
        guard=free_route_guard(route)
        status=outcome.setdefault(route_name,{"configuration":guard,"calls":0,"languages":{}})
        if guard!="FREE_ROUTE_CONFIGURED":
            status["languages"][lang]="HOLD_"+guard
            continue
        item=fixture(lang);calls+=1;status["calls"]+=1
        req={"items":[{"index":0,"source_sha256":item["source_sha256"],
            "language":lang,"title":item["title"],"summary":item["summary"]}]}
        system=TRANSLATE_SYSTEM+"\nEach item MUST echo source_sha256 unchanged. Preserve the 12 and 27 quantities exactly once, and the fact that opening is NOT confirmed."
        try:
            response=caller(route,system,req,max_tokens=400)
            graded=inspect_translations([item],response)
            status["languages"][lang]=("STRUCTURAL_PASS" if graded["structural_review_passed"]==1
                and not graded["reasons"] else "HOLD_STRUCTURAL_TRANSLATION")
        except Exception as exc:
            status["languages"][lang]="HOLD_"+type(exc).__name__
    if one_english_retry and outcome["primary"]["languages"]["en"]!="STRUCTURAL_PASS":
        route=routes["primary"]
        if free_route_guard(route)=="FREE_ROUTE_CONFIGURED":
            item=fixture("en")
            short_system=("Return JSON only: items=[{index,title_ar,summary_ar,source_sha256}]. "
                          "Translate the given English to Arabic. Preserve 12, 27, negation, and exact source_sha256.")
            request={"items":[{"index":0,"title":item["title"],"summary":item["summary"],
                      "source_sha256":item["source_sha256"],"language":"en"}]}
            calls+=1;outcome["primary"]["calls"]+=1
            try:
                response=caller(route,short_system,request,max_tokens=240)
                judged=inspect_translations([item],response)
                outcome["primary"]["languages"]["en_retry"]=(
                    "STRUCTURAL_PASS" if judged["structural_review_passed"]==1 and not judged["reasons"]
                    else "HOLD_STRUCTURAL_TRANSLATION")
            except Exception as exc:
                outcome["primary"]["languages"]["en_retry"]="HOLD_"+type(exc).__name__
    return {"schema":"aggregateit-v2-b45-live-free-diagnostic/1",
        "checked_at":datetime.now(timezone.utc).isoformat(),"routes":outcome,
        "actual_free_provider_attempts":calls,
        "english_structural_pass":any(outcome["primary"]["languages"].get(k)=="STRUCTURAL_PASS" for k in ("en","en_retry")),
        "english_retry_attempted":"en_retry" in outcome["primary"]["languages"],
        "somali_structural_pass":outcome["primary"]["languages"]["so"]=="STRUCTURAL_PASS",
        "real_fallback_endpoint_tested":outcome["fallback"]["calls"]>0,
        "paid_route_calls":0,"publisher_text_sent_to_model":False,
        "independent_semantic_quality_verified":False,"real_publisher_translation_verified":False,
        "primary_failure_then_real_fallback_tested":False,
        "discord_sent":False,"can_release":False}

if __name__=="__main__":
    import argparse,json
    from pathlib import Path
    a=argparse.ArgumentParser();a.add_argument("--output",required=True,type=Path)
    a.add_argument("--one-english-retry",action="store_true")
    opt=a.parse_args();report=run_probe(one_english_retry=opt.one_english_retry)
    opt.output.parent.mkdir(parents=True,exist_ok=True)
    opt.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"primary_en":report["english_structural_pass"],
        "primary_so":report["somali_structural_pass"],
        "fallback_endpoint_tested":report["real_fallback_endpoint_tested"],
        "english_retry_attempted":report["english_retry_attempted"],
        "free_requests":report["actual_free_provider_attempts"],
        "paid_calls":0,"can_release":False}))
