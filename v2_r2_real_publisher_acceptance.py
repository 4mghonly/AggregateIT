"""Held live-publisher bilingual R2 evaluation; at most four model requests total."""
import json,os
from v2_r2_http_transport import make_http_caller
from v2_r2_model_adapter import make_analysis_provider
from v2_b46_live_editorial_runner import run

def evaluate():
    configs={}
    for role,prefix in (("primary","V2_LLM_"),("fallback","V2_LLM_FALLBACK_")):
        values=[os.getenv(prefix+field,"") for field in ("BASE_URL","MODEL","API_KEY")]
        configs[role]=make_analysis_provider(caller=make_http_caller(
            base_url=values[0],model=values[1],api_key=values[2])) if all(values) else None
    outcomes={role:{"status":"EVALUATED" if provider else "HOLD_MISSING_CONFIG","languages":{}}
              for role,provider in configs.items()}
    calls=[]
    diagnostics=[]
    def provider(*,product,items,as_of):
        if not items:return []
        selected=items[:1]
        accepted=[]
        for role,adapter in configs.items():
            if adapter is None:continue
            try:
                candidates=[]
                for attempt in (1,2):
                    calls.append({"role":role,"product":product,"attempt":attempt})
                    try:
                        candidates=adapter(product=product,items=selected,as_of=as_of)
                        break
                    except ValueError as error:
                        code=str(error)
                        diagnostics.append({"role":role,"product":product,"attempt":attempt,"code":code if code.startswith(("invalid_analysis_","untrusted_analysis_","duplicate_analysis_","invalid_model_","model_")) else "unclassified_value_error"})
                        if attempt==2:raise
                status="STRUCTURAL_PASS_UNVERIFIED" if candidates else "ABSTAINED"
                if role=="primary":accepted=candidates
            except Exception as exc:
                status="HOLD_"+type(exc).__name__+("_"+str(exc) if isinstance(exc,ValueError) and str(exc).startswith(("invalid_analysis_","untrusted_analysis_","duplicate_analysis_")) else "")
            outcomes[role]["languages"][product]=status

        return accepted
    try:
        result=run(analysis_provider=provider,editorial_max_items=3,quality_preview=True)
        receipt=result["editorial"]
        counts={p:receipt["products"][p]["story_count"] for p in ("english","arabic")}
        provider_status=receipt["analysis_provider_status"]
        collection_status="CAPTURED" if all(counts.values()) else "HOLD_INSUFFICIENT_BILINGUAL_PUBLISHER_EVIDENCE"
    except Exception as exc:
        counts={"english":0,"arabic":0}
        provider_status={}
        collection_status="HOLD_"+type(exc).__name__
    complete=collection_status=="CAPTURED" and all(outcomes[role]["languages"].get(lang)=="STRUCTURAL_PASS_UNVERIFIED" for role in outcomes for lang in ("english","arabic"))
    return {"schema":"aggregateit-v2-r2-real-publisher-acceptance/1",
        "structural_gate_pass":complete,
        "results":outcomes,"publisher_story_counts":counts,"provider_status":provider_status,
        "collection_status":collection_status,"model_calls":len(calls),"diagnostics":diagnostics,
        "real_publisher_evidence_evaluated":bool(calls),
        "independent_semantic_review":False,"editorial_release_authorized":False}

if __name__=="__main__":
    report=evaluate()
    # Existing Telegram function describes fixtures, so do not mislabel real evidence.
    # This gate is recorded in Actions logs only until a truthful report format exists.
    print(json.dumps(report,ensure_ascii=False,sort_keys=True))
    if not report["structural_gate_pass"]:
        raise SystemExit(1)
