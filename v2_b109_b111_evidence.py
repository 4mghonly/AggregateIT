"""B109-B111 no-post evidence quality: classify failures and prohibit fabricated parity."""
from __future__ import annotations
from datetime import date
from hashlib import sha256
import json

def classify_translation_failure(http_status:int|None, *,primary_attempted:bool,fallback_attempted:bool)->dict:
    if http_status is not None and (type(http_status) is not int or not 100<=http_status<=599):
        raise ValueError("invalid_http_status")
    if type(primary_attempted) is not bool or type(fallback_attempted) is not bool:
        raise ValueError("invalid_attempt_flags")
    if http_status in (401,403):
        category="AUTH_OR_PROVIDER_ACCESS"
    elif http_status==429:
        category="RATE_LIMIT"
    elif http_status is not None and http_status>=500:
        category="PROVIDER_UNAVAILABLE"
    elif http_status is None:
        category="NO_HTTP_RESULT"
    else:
        category="OTHER_HTTP_FAILURE"
    return {"category":category,"http_status":http_status,
            "primary_attempted":primary_attempted,"fallback_attempted":fallback_attempted,
            "credential_validity_verified":False,"failover_success_verified":False,
            "retry_same_credential_recommended":False if category=="AUTH_OR_PROVIDER_ACCESS" else None,
            "can_release":False}

def partial_shadow_receipt(shadow:dict, *,capture_date:str)->dict:
    day=date.fromisoformat(capture_date).isoformat()
    if not isinstance(shadow,dict) or shadow.get("schema")!="aggregateit-v2-b49-single-slot-preflight/1" or shadow.get("can_release") is not False:
        raise ValueError("untrusted_shadow")
    rows=shadow.get("rows",[])
    if not isinstance(rows,list) or len(rows)!=2 or {r.get("product") for r in rows}!={"english","arabic"}:
        raise ValueError("missing_bilingual_rows")
    observations={}
    for r in rows:
        digest=r.get("source_sha256")
        if not isinstance(digest,str) or len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("invalid_source_digest")
        observations[r["product"]]={"input_sha256":digest,
            "parser_parity":r.get("v1_v2_parser_parity") is True,
            "headline_identity_parity":r.get("v1_v2_headline_identity_parity") is True,
            "v2_story_count":r.get("v2_source_linked_daily_stories"),
            "full_editorial_parity_verified":False}
    return {"schema":"aggregateit-v2-b111-partial-daily-shadow/1","date":day,
            "observations":observations,
            "full_processing_comparison_rows":0,
            "b101_b106_seven_day_parity_accepted":False,
            "no_post":True,"can_release":False}

def report_from_file(path:str, *,capture_date:str)->dict:
    with open(path,encoding="utf8") as f:
        shadow=json.load(f)
    return partial_shadow_receipt(shadow,capture_date=capture_date)
if __name__=="__main__":
    import argparse
    from pathlib import Path
    p=argparse.ArgumentParser()
    p.add_argument("--shadow",required=True)
    p.add_argument("--date",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    try:
        result=report_from_file(args.shadow,capture_date=args.date)
    except (OSError,ValueError,TypeError,KeyError) as exc:
        result={"schema":"aggregateit-v2-b111-partial-daily-shadow/1",
                "status":"HOLD_MISSING_OR_INVALID_EVIDENCE","failure_class":type(exc).__name__,
                "full_processing_comparison_rows":0,"can_release":False}
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({"status":result.get("status","PARTIAL_SHADOW_CAPTURED"),
        "full_processing_comparison_rows":0,"can_release":False}))
