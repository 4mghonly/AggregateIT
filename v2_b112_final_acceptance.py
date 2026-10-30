"""B112: fail-closed real bilingual acceptance synthesis, never authorizes publication."""
from __future__ import annotations
import json
from pathlib import Path

def assess(live:dict, shadow:dict, parity:dict|None=None)->dict:
    if live.get("schema")!="aggregateit-v2-b46-live-chain/1" or live.get("can_release") is not False:
        raise ValueError("untrusted_live_capture")
    if shadow.get("schema")!="aggregateit-v2-b49-single-slot-preflight/1" or shadow.get("can_release") is not False:
        raise ValueError("untrusted_shadow_capture")
    diag=live.get("arabic_zero_story_diagnosis")
    if not isinstance(diag,dict):
        raise ValueError("missing_arabic_diagnostics")
    live_counts=live.get("editorial",{}).get("products",{})
    if set(live_counts)!={"english","arabic"}:
        raise ValueError("missing_live_products")
    live_stories={p:live_counts[p]["story_count"] for p in ("english","arabic")}
    if any(type(v) is not int or v<0 for v in live_stories.values()):
        raise ValueError("invalid_live_story_counts")
    rows=shadow.get("rows",[])
    if not isinstance(rows,list) or len(rows)!=2 or {r.get("product") for r in rows}!={"english","arabic"}:
        raise ValueError("missing_shadow_products")
    shadow_stories={r["product"]:r["v2_source_linked_daily_stories"] for r in rows}
    if any(type(v) is not int or v<0 for v in shadow_stories.values()):
        raise ValueError("invalid_shadow_story_counts")
    source_recovery=live.get("source_recovery",{}).get("arabic",{})
    if parity is not None and parity.get("schema")!="aggregateit-v2-b101-b106-parity-gates/1":
        raise ValueError("untrusted_parity")
    complete=parity is not None and parity.get("same_input_seven_date_evidence_complete") is True and parity.get("all_dimensions_matched") is True
    return {"schema":"aggregateit-v2-b112-final-preparation/1",
            "live_stories":live_stories,"shadow_stories":shadow_stories,
            "arabic_live_recovered":live_stories["arabic"]>0,
            "arabic_shadow_recovered":shadow_stories["arabic"]>0,
            "arabic_capture_discrepancy":live_stories["arabic"]!=shadow_stories["arabic"],
            "arabic_rejection_counts":diag.get("counts",{}).get("body_gate_rejections",{}),
            "arabic_fallback_used":source_recovery.get("fallback_used") is True,
            "same_capture_for_live_and_shadow_verified":False,
            "full_seven_day_evidence_complete":complete,
            "current_model_fallback_verified":False,
            "native_visual_equivalence_verified":False,
            "release_readiness":"HOLD_ADDITIONAL_REAL_EVIDENCE_REQUIRED",
            "can_release":False,"discord_sent":False}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--live",required=True)
    p.add_argument("--shadow",required=True)
    p.add_argument("--parity")
    p.add_argument("--output",required=True)
    a=p.parse_args()
    try:
        live=json.loads(Path(a.live).read_text(encoding="utf8"))
        shadow=json.loads(Path(a.shadow).read_text(encoding="utf8"))
        parity=json.loads(Path(a.parity).read_text(encoding="utf8")) if a.parity else None
        result=assess(live,shadow,parity)
    except (OSError,ValueError,TypeError,KeyError) as exc:
        result={"schema":"aggregateit-v2-b112-final-preparation/1",
                "release_readiness":"HOLD_MISSING_OR_INVALID_EVIDENCE",
                "failure_class":type(exc).__name__,"can_release":False,"discord_sent":False}
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
