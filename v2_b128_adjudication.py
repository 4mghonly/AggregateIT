"""B128: classify review workload, verify completeness, never impersonate an adjudicator.

A source-linked weekly roster is not a four-product analytical weekly publication.
No publisher article text, model calls, production delivery or invented review outcomes.
"""
from collections import Counter
from datetime import date
import re

SCHEMA="aggregateit-v2-b128-adjudication-readiness/1"
REASONS={
 "no_grounded_region":"grounding",
 "ambiguous_geography":"grounding",
 "article_body_container_missing":"extraction",
 "arabic_topic_without_explicit_trigger":"relevance",
 "arabic_not_security_relevant":"relevance",
 "rank_diversity_or_page_budget":"ranking",
}
DIGEST=re.compile(r"[0-9a-f]{64}\Z")

def assess(queue,b126,*,expected_sha,weekly=None):
    issues=[]
    if (not isinstance(queue,dict) or queue.get("schema")!="aggregateit-v2-b127-identity-matched-review/1" or
        queue.get("candidate_sha")!=expected_sha or queue.get("evidence_reconciled") is not True or
        queue.get("can_release") is not False or queue.get("issues")!=[]):
        issues.append("untrusted_b127")
    if (not isinstance(b126,dict) or b126.get("schema")!="aggregateit-v2-b126-weekly-editorial-audit/1" or
        b126.get("candidate_sha")!=expected_sha or b126.get("source_roster_seven_days") is not True or
        b126.get("can_release") is not False or b126.get("issues")!=[]):
        issues.append("untrusted_b126")
    rows=queue.get("rows",[]) if isinstance(queue,dict) else []
    if (not isinstance(rows,list) or len(rows)>500 or
        type(queue.get("disagreement_count")) is not int or queue["disagreement_count"]!=len(rows)):
        issues.append("invalid_queue_size")
        rows=rows[:500] if isinstance(rows,list) else []
    counts=Counter()
    seen=set()
    window=b126.get("verified_dates",[]) if isinstance(b126,dict) else []
    for row in rows:
        if not isinstance(row,dict):
            issues.append("invalid_row")
            continue
        key=(row.get("utc_date"),row.get("product"),row.get("identity_sha256"))
        if key in seen:
            issues.append("duplicate_source_date")
        seen.add(key)
        if (row.get("utc_date") not in window or row.get("product") not in ("english","arabic") or
            not isinstance(row.get("identity_sha256"),str) or not DIGEST.fullmatch(row["identity_sha256"]) or
            row.get("decision") not in ("v1_only","v2_only")):
            issues.append("invalid_row_identity")
        if (row.get("analyst_reviewed") is not False or row.get("materiality")!="UNASSESSED" or
            row.get("publisher_rights")!="UNVERIFIED"):
            issues.append("unsupported_review_or_rights_claim")
        if row.get("decision")=="v2_only":
            counts["v2_only_requires_review"]+=1
        else:
            reason=row.get("v2_rejection_reason")
            counts[REASONS.get(reason,"unclassified_rejection")]+=1
    valid=not issues
    return {"schema":SCHEMA,"candidate_sha":expected_sha,"review_queue_valid":valid,
            "disagreement_count":len(rows),"triage":dict(sorted(counts.items())),
            "reviewed_count":0,"pending_count":len(rows),
            "independent_adjudication_verified":False,
            "weekly_source_roster_verified":bool(valid and b126.get("source_roster_seven_days") is True),
            "weekly_full_product_verified":False,
            "full_model_parity_verified":False,"can_release":False,
            "issues":sorted(set(issues))}
