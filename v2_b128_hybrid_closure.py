"""B128 A-D offline hybrid review and weekly-product acceptance; never publishes.

LLM judgments are provisional. Independent acceptance requires a human decision
and a second independently sourced review, both with evidence and provenance.
"""
from collections import Counter
from hashlib import sha256
from datetime import datetime,timezone
import re
SCHEMA="aggregateit-v2-b128-hybrid-closure/1"
DISPOSITIONS={"correct_v1","correct_v2","both_defensible","both_incorrect","insufficient_evidence"}
HEX=re.compile(r"[a-f0-9]{64}\Z")

def evaluate(queue,b126,four,verdicts,*,expected_sha):
    issues=[]
    if not isinstance(queue,dict) or queue.get("schema")!="aggregateit-v2-b127-identity-matched-review/1" or queue.get("candidate_sha")!=expected_sha or queue.get("evidence_reconciled") is not True or queue.get("issues")!=[]:
        issues.append("invalid_b127")
    if not isinstance(b126,dict) or b126.get("schema")!="aggregateit-v2-b126-weekly-editorial-audit/1" or b126.get("candidate_sha")!=expected_sha or b126.get("source_roster_seven_days") is not True or b126.get("issues")!=[]:
        issues.append("invalid_b126")
    rows=queue.get("rows",[]) if isinstance(queue,dict) else []
    if not isinstance(rows,list) or len(rows)>500 or queue.get("disagreement_count")!=len(rows):
        issues.append("invalid_review_rows")
        rows=[]
    if not isinstance(verdicts,list) or len(verdicts)>1000:
        issues.append("invalid_verdicts")
        verdicts=[]
    keys={(r.get("utc_date"),r.get("product"),r.get("identity_sha256")) for r in rows if isinstance(r,dict)}
    if len(keys)!=len(rows):
        issues.append("duplicate_review_rows")
    bykey={}
    for v in verdicts:
        if not isinstance(v,dict):
            issues.append("invalid_verdict")
            continue
        key=(v.get("utc_date"),v.get("product"),v.get("identity_sha256"))
        if key not in keys:
            issues.append("unmatched_verdict")
            continue
        if key in bykey:
            issues.append("duplicate_verdict")
            continue
        bykey[key]=v
    accepted=0
    provisional=0
    packet=[]
    for row in rows:
        key=(row["utc_date"],row["product"],row["identity_sha256"])
        v=bykey.get(key)
        status="PENDING_REVIEW"
        if v:
            if v.get("disposition") in DISPOSITIONS:
                status="PROVISIONAL"
                provisional+=1
                checks=v.get("independent_checks",[])
                if (v.get("reviewer_type")=="human" and isinstance(v.get("reviewer_id"),str) and
                    v["reviewer_id"].strip() and isinstance(v.get("rationale"),str) and len(v["rationale"].strip())>=30 and
                    isinstance(v.get("evidence_refs"),list) and len(v["evidence_refs"])>=1 and
                    isinstance(checks,list) and len(checks)>=1 and
                    any(isinstance(c,dict) and c.get("reviewer_id") not in (None,v["reviewer_id"]) and
                        c.get("disposition")==v["disposition"] and
                        c.get("evidence_refs") and c.get("reviewer_type") in ("human","independent_evaluator")
                        for c in checks) and v["disposition"]!="insufficient_evidence"):
                    status="EVIDENCE_REVIEWED"
                    accepted+=1
            else:
                issues.append("invalid_disposition")
        packet.append({"utc_date":row["utc_date"],"product":row["product"],
                       "identity_sha256":row["identity_sha256"],"source_url":row["source_url"],
                       "selection_difference":row["decision"],"recorded_v2_reason":row.get("v2_rejection_reason"),
                       "review_status":status,"reviewer_rubric":"B128-HYBRID-1",
                       "required_checks":["source_provenance","editorial_scope","factual_grounding","relevance",
                                          "translation_if_applicable","publisher_rights","independent_second_review"]})
    weekly={}
    missing={}
    if not isinstance(four,dict) or four.get("schema")!="aggregateit-v2-b47-four-product-held/1":
        issues.append("invalid_four_product_receipt")
        four={}
    products=four.get("weekly",{})
    for p in ("english","arabic"):
        item=products.get(p,{}) if isinstance(products,dict) else {}
        days=item.get("days_with_real_daily_snapshots")
        if type(days) is not int or not 0<=days<=7:
            issues.append("invalid_weekly_day_count")
            days=0
        missing[p]=7-days
        weekly[p]={"observed_days":days,"required_days":7,
                   "complete_history_flag":item.get("complete_seven_day_history") is True,
                   "pdf_rendered":item.get("pdf_rendered") is True,
                   "independent_product_evidence":False}
    return {"schema":SCHEMA,"candidate_sha":expected_sha,
            "review_packet":packet,"adjudication":{"total":len(rows),"accepted":accepted,
               "provisional":provisional,"pending":len(rows)-accepted,
               "independent_adjudication_verified":False},
            "weekly":{"products":weekly,"missing_snapshot_days":missing,
                      "verified":False,"four_product_reporting_verified":False},
            "remediation":{"requires_fresh_weekly_reconstruction":any(missing.values()),
                           "requires_independent_source_review":len(rows)>accepted,
                           "requires_translation_visual_delivery_rights_acceptance":True},
            "release_status":"HOLD","can_release":False,"issues":sorted(set(issues))}
