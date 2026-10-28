"""B91-93 coverage, repeatability and release gate audit. No network or publishing."""
from __future__ import annotations
import json
from pathlib import Path
from v2_editorial import AR_REGIONS

def audit(acceptance:dict, history:list[dict])->dict:
 if acceptance.get("schema")!="aggregateit-v2-b88-b90-acceptance/1" or acceptance.get("can_release") is not False:
  raise ValueError("untrusted_acceptance")
 if not isinstance(history,list) or len(history)>30:raise ValueError("invalid_history")
 coverage=acceptance["b89_source_coverage"]
 if set(coverage)!={"english","arabic"}:raise ValueError("missing_languages")
 missing=sorted(AR_REGIONS-set(coverage["arabic"]["represented_regions"]))
 observed=set()
 for row in history:
  if not isinstance(row,dict) or row.get("schema")!="aggregateit-v2-b88-b90-acceptance/1" or row.get("can_release") is not False:raise ValueError("untrusted_history")
  stamp=row.get("observed_date")
  if not isinstance(stamp,str) or len(stamp)!=10:raise ValueError("missing_observed_date")
  observed.add(stamp)
 # Historical artifacts from one day cannot masquerade as seven days.
 days=len(observed)
 return {"schema":"aggregateit-v2-b91-b93-audit/1","b91":{"arabic_target_regions":len(AR_REGIONS),"arabic_regions_represented":len(AR_REGIONS)-len(missing),"missing_regions":missing,"source_redundancy_proven":False},"b92":{"distinct_observed_days":days,"seven_day_evidence_met":days>=7},"b93":{"independent_visual_qa":False,"full_v1_v2_parity":False,"live_model_fallback_verified":False,"discord_delivery_verified":False,"can_release":False},"can_release":False,"discord_sent":False}

def main():
 a=json.loads(Path("b88_b90_acceptance.json").read_text())
 # The current run represents one date only, even if multiple workflow attempts occurred.
 from datetime import datetime,timezone
 a["observed_date"]=datetime.now(timezone.utc).date().isoformat()
 report=audit(a,[a])
 Path("b91_b93_audit.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":main()
