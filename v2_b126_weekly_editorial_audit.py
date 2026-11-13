"""B126: audited source-roster continuity and aggregate V1/V2 selection disagreements.

Counts are diagnostic; they cannot prove model, translation, editorial or delivery parity.
"""
from datetime import date,timedelta
from collections import Counter

SCHEMA="aggregateit-v2-b126-weekly-editorial-audit/1"
B125="aggregateit-v2-b125-independent-reconciliation/1"
FIELDS=("operational_v2_selected","v1_selected","both_selected","v2_only","v1_only")

def audit(paired,b125,*,expected_sha):
    issues=[]
    totals={p:Counter() for p in ("english","arabic")}
    days=[]
    if not isinstance(paired,list) or len(paired)!=7:
        issues.append("expected_seven_paired_receipts")
    if not isinstance(b125,dict) or b125.get("schema")!=B125 or b125.get("seven_verified") is not True or b125.get("can_release") is not False or b125.get("candidate_sha")!=expected_sha or b125.get("issues")!=[]:
        issues.append("b125_not_independently_verified")
    if isinstance(paired,list):
        for row in paired[:45]:
            if not isinstance(row,dict) or row.get("head_sha")!=expected_sha:
                issues.append("invalid_candidate_receipt")
                continue
            day=row.get("utc_date")
            try:
                parsed=date.fromisoformat(day)
            except (TypeError,ValueError):
                issues.append("invalid_utc_date")
                continue
            days.append(day)
            products=row.get("products")
            if not isinstance(products,dict) or set(products)!={"english","arabic"}:
                issues.append("missing_bilingual_selection")
                continue
            for product in ("english","arabic"):
                counts=products[product]
                if not isinstance(counts,dict) or any(type(counts.get(k)) is not int or counts[k]<0 for k in FIELDS):
                    issues.append("invalid_selection_counts")
                    continue
                if (counts["v1_selected"]!=counts["both_selected"]+counts["v1_only"] or
                    counts["operational_v2_selected"]!=counts["both_selected"]+counts["v2_only"] or
                    counts["operational_v2_selected"]<=0):
                    issues.append("selection_arithmetic_mismatch")
                    continue
                totals[product].update({k:counts[k] for k in FIELDS})
    ordered=sorted(days)
    if (len(ordered)!=7 or len(set(ordered))!=7 or
        any(date.fromisoformat(ordered[i+1])-date.fromisoformat(ordered[i])!=timedelta(days=1) for i in range(6)) or
        not isinstance(b125,dict) or ordered!=b125.get("verified_dates")):
        issues.append("date_window_not_reconciled")
    complete=not issues
    return {"schema":SCHEMA,"candidate_sha":expected_sha,
            "source_roster_seven_days":complete,"verified_dates":ordered if complete else [],
            "products":{p:dict(totals[p]) for p in ("english","arabic")},
            "selection_disagreements_observed":any(totals[p]["v1_only"] or totals[p]["v2_only"] for p in totals),
            "full_model_parity":False,"weekly_full_product_verified":False,
            "editorial_adjudication_verified":False,"can_release":False,
            "issues":sorted(set(issues))}
