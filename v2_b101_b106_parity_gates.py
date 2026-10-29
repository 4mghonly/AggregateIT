"""B101-B106 evidence-gated parity assessment, no publishing authority.

Accepts externally collected, same-input comparison receipts. Never treats
fixture-only checks, model configuration or seven synthetic dates as proof.
"""
from __future__ import annotations
from datetime import date,timedelta
from hashlib import sha256
import json

AREAS=("arabic_filter","english_scoring","event_clustering","multilingual_consolidation","historical_evolution","translation_fallback","visual_delivery")
def _valid_row(row):
 if not isinstance(row,dict) or set(row)!={"date","product","input_sha256","v1","v2","evidence"}:raise ValueError("invalid_comparison_row")
 date.fromisoformat(row["date"])
 if row["product"] not in ("english","arabic"):raise ValueError("invalid_product")
 digest=row["input_sha256"]
 if not isinstance(digest,str) or len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest):raise ValueError("invalid_input_digest")
 for side in ("v1","v2"):
  data=row[side]
  if not isinstance(data,dict) or set(data)!=set(AREAS):raise ValueError("incomplete_processing_dimensions")
  for area in AREAS:
   value=data[area]
   if value is not None and (not isinstance(value,list) or len(value)>100 or any(not isinstance(x,str) or len(x)>300 for x in value)):raise ValueError("invalid_dimension_values")
 evidence=row["evidence"]
 if not isinstance(evidence,dict) or set(evidence)!={"v1_executed","v2_executed","same_input_verified","model_fallback_exercised","historical_baseline_authenticated","visual_reviewed","source_provenance_verified"} or any(type(v)!=bool for v in evidence.values()):raise ValueError("invalid_evidence")
 return row

def assess(rows,*,as_of):
 """Measured counts are descriptive, never factual-quality equivalence."""
 today=date.fromisoformat(as_of)
 if not isinstance(rows,list) or len(rows)>14:raise ValueError("unbounded_comparisons")
 seen=set();results=[];coverage={}
 for raw in rows:
  row=_valid_row(raw);day=date.fromisoformat(row["date"])
  if day>today or day<today-timedelta(days=6):raise ValueError("outside_seven_day_window")
  key=(row["date"],row["product"])
  if key in seen:raise ValueError("duplicate_date_product")
  seen.add(key)
  evidence=row["evidence"]
  trusted=all(evidence[k] for k in ("v1_executed","v2_executed","same_input_verified","source_provenance_verified"))
  dimensions={}
  for area in AREAS:
   left,right=row["v1"][area],row["v2"][area]
   if left is None or right is None or not trusted:
    dimensions[area]={"status":"UNVERIFIED"}
   else:
    a,b=set(left),set(right)
    dimensions[area]={"status":"MATCH" if a==b else "DIFFERENT","v1_only":len(a-b),"v2_only":len(b-a)}
  if not evidence["historical_baseline_authenticated"]:dimensions["historical_evolution"]={"status":"UNVERIFIED"}
  if not evidence["model_fallback_exercised"]:dimensions["translation_fallback"]={"status":"UNVERIFIED"}
  if not evidence["visual_reviewed"]:dimensions["visual_delivery"]={"status":"UNVERIFIED"}
  results.append({"date":row["date"],"product":row["product"],"input_sha256":row["input_sha256"],"dimensions":dimensions})
  coverage[key]=all(d["status"]=="MATCH" for d in dimensions.values())
 seven_dates=[(today-timedelta(days=i)).isoformat() for i in range(6,-1,-1)]
 complete=all((d,p) in coverage for d in seven_dates for p in ("english","arabic"))
 matched=complete and all(coverage.values())
 return {"schema":"aggregateit-v2-b101-b106-parity-gates/1","window":seven_dates,
         "received_rows":len(results),"required_rows":14,
         "same_input_seven_date_evidence_complete":complete,
         "all_dimensions_matched":bool(matched),
         "results":results,
         "readiness":"EVIDENCE_COMPLETE_REVIEW_REQUIRED" if matched else "HOLD_INCOMPLETE_OR_DIFFERENT",
         "production_cutover_authorized":False,"can_release":False}
if __name__=="__main__":
 print(json.dumps(assess([],as_of=date.today().isoformat()),indent=2))
