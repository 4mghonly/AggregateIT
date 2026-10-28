"""Evidence-backed V2 acceptance status. Missing independent evidence always blocks release."""
from __future__ import annotations
import json
from pathlib import Path
from v2_b62_precanary import RELEASE_ITEMS

EVIDENCE_SCHEMA="aggregateit-v2-independent-acceptance/1"
def assess(evidence):
    if not isinstance(evidence,dict) or evidence.get("schema")!=EVIDENCE_SCHEMA:
        raise ValueError("invalid_acceptance_evidence")
    if not isinstance(evidence.get("checks",{}),dict):
        raise ValueError("invalid_acceptance_checks")
    checks={}
    details={}
    for key in RELEASE_ITEMS:
        item=evidence.get("checks",{}).get(key)
        if not isinstance(item,dict):
            checks[key]=False
            details[key]="missing_independent_evidence"
            continue
        required=("artifact_url","sha256","reviewed_at","independent_verification")
        valid=(all(isinstance(item.get(x),str) and bool(item[x].strip()) for x in required[:3])
               and isinstance(item.get("sha256"),str)
               and len(item["sha256"])==64
               and all(c in "0123456789abcdef" for c in item["sha256"])
               and item.get("independent_verification") is True
               and item.get("result")=="pass")
        # An unverified self-asserted receipt cannot be admitted.
        checks[key]=valid
        details[key]="receipt_present_requires_external_verification" if valid else "incomplete_or_failed_receipt"
    # This is a readiness inventory, not an authorization mechanism:
    # even complete receipts must be independently verified outside this module.
    return {"schema":"aggregateit-v2-acceptance-inventory/1",
            "receipts_structurally_present":checks,
            "missing_or_incomplete":[k for k,v in checks.items() if not v],
            "receipt_notes":details,
            "independent_evidence_authenticated":False,
            "production_cutover_authorized":False,
            "release_status":"HOLD","can_release":False}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--evidence",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=assess(json.loads(args.evidence.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"open":result["missing_or_incomplete"],"release":result["release_status"]}))
if __name__=="__main__":main()
