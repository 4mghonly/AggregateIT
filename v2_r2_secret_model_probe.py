"""One-request, no-send, sanitized R2 inference acceptance using GitHub Actions secrets."""
import json,os
from v2_r2_http_transport import make_http_caller
from v2_r2_model_adapter import make_analysis_provider

def run():
    base=os.getenv("V2_LLM_BASE_URL","")
    model=os.getenv("V2_LLM_MODEL","")
    key=os.getenv("V2_LLM_API_KEY","")
    if not (base and model and key):
        return {"status":"HOLD_MODEL_SECRETS_MISSING","attempts":0,"can_release":False}
    # Self-authored fixture, not copyrighted publisher text or confidential material.
    item={"event_id":"fixture-proposal","evidence":{"excerpt_id":"fixture-excerpt",
          "quote":"Officials proposed two clinics but no funding was approved.",
          "source_url":"https://example.org/fixture"}}
    try:
        caller=make_http_caller(base_url=base,model=model,api_key=key)
        candidates=make_analysis_provider(caller=caller)(
            product="english",items=[item],as_of="2026-11-14T12:00:00+00:00")
        status="STRUCTURAL_PASS_UNVERIFIED" if candidates else "MODEL_ABSTAINED"
    except Exception as exc:
        # Never log exception messages: some HTTP libraries embed credentials.
        status="HOLD_"+type(exc).__name__
    return {"schema":"aggregateit-r2-model-secret-probe/1","status":status,
            "attempts":1,"fixture_only":True,"publisher_text_sent":False,
            "semantic_truth_independently_verified":False,"can_release":False}
if __name__=="__main__":
    print(json.dumps(run(),sort_keys=True))
