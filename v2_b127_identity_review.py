"""B127 per-source V1/V2 editorial disagreement review, no publisher text or delivery.

Inputs are seven B124 review artifacts and seven authenticated B120 source rosters,
plus independently accepted B126 weekly totals. Identity is SHA256 of exact source URL.
"""
from datetime import datetime,timezone
from hashlib import sha256
from collections import Counter
from urllib.parse import urlsplit
import re

SCHEMA="aggregateit-v2-b127-identity-matched-review/1"
B124="aggregateit-v2-b124-editorial-disagreement-review/1"
B126="aggregateit-v2-b126-weekly-editorial-audit/1"
HEX=re.compile(r"[a-f0-9]{64}\Z")
PRODUCTS=("english","arabic")

def build_queue(reviews,rosters,b126,*,expected_sha):
    issues=[]
    rows=[]
    counts={p:Counter() for p in PRODUCTS}
    if not isinstance(b126,dict) or b126.get("schema")!=B126 or b126.get("source_roster_seven_days") is not True or b126.get("candidate_sha")!=expected_sha or b126.get("can_release") is not False or b126.get("issues")!=[]:
        issues.append("b126_not_verified")
    days=b126.get("verified_dates",[]) if isinstance(b126,dict) else []
    if not isinstance(days,list) or len(days)!=7 or len(set(days))!=7:
        issues.append("invalid_b126_window")
    if not isinstance(reviews,list) or len(reviews)!=7 or not isinstance(rosters,list) or len(rosters)!=7:
        issues.append("expected_seven_review_roster_pairs")
    if isinstance(reviews,list) and isinstance(rosters,list):
        for index,(review,roster) in enumerate(zip(reviews[:7],rosters[:7])):
            if not isinstance(review,dict) or not isinstance(roster,dict):
                issues.append("invalid_pair")
                continue
            day=roster.get("utc_date")
            try:
                observed=datetime.fromisoformat(review.get("observed_at","").replace("Z","+00:00"))
                valid_day=observed.tzinfo is not None and observed.astimezone(timezone.utc).date().isoformat()==day
            except (ValueError,TypeError):
                valid_day=False
            if (not valid_day or index>=len(days) or day!=days[index] or
                roster.get("head_sha")!=expected_sha or review.get("schema")!=B124 or
                review.get("can_release") is not False):
                issues.append("review_roster_provenance_mismatch")
                continue
            products=roster.get("products",{})
            if not isinstance(products,dict) or set(products)!=set(PRODUCTS):
                issues.append("missing_roster_products")
                continue
            roster_ids={}
            for p in PRODUCTS:
                stories=products[p].get("stories",[]) if isinstance(products[p],dict) else []
                if not isinstance(stories,list) or len(stories)>15:
                    issues.append("invalid_roster_stories")
                    stories=[]
                roster_ids[p]={x.get("identity_sha256") for x in stories if isinstance(x,dict)}
                if len(roster_ids[p])!=len(stories):
                    issues.append("duplicate_roster_identity")
            seen=set()
            source_rows=review.get("rows")
            if not isinstance(source_rows,list) or len(source_rows)>100:
                issues.append("invalid_review_rows")
                continue
            for item in source_rows:
                if not isinstance(item,dict):
                    issues.append("invalid_review_row")
                    continue
                product=item.get("product")
                url=item.get("source_url")
                identity=item.get("identity_sha256")
                if product not in PRODUCTS or not isinstance(url,str) or len(url)>1600 or not isinstance(identity,str):
                    issues.append("invalid_source_identity")
                    continue
                parsed=urlsplit(url)
                if parsed.scheme!="https" or not parsed.hostname or parsed.username or parsed.password or not HEX.fullmatch(identity) or sha256(url.encode("utf8")).hexdigest()!=identity:
                    issues.append("source_identity_hash_mismatch")
                    continue
                key=(product,identity)
                if key in seen:
                    issues.append("duplicate_review_identity")
                    continue
                seen.add(key)
                v1=item.get("v1_selected")
                v2=item.get("v2_selected")
                if type(v1) is not bool or type(v2) is not bool or v1==v2:
                    issues.append("not_a_selection_disagreement")
                    continue
                decision="v1_only" if v1 else "v2_only"
                if (identity in roster_ids[product])!=v2:
                    issues.append("v2_roster_identity_disagreement")
                if item.get("analyst_reviewed") is not False or item.get("materiality")!="UNASSESSED" or item.get("publisher_rights")!="UNVERIFIED":
                    issues.append("untrusted_adjudication_or_rights_claim")
                if decision=="v2_only" and item.get("v2_decision_stage")!="selected":
                    issues.append("v2_stage_disagreement")
                if decision=="v1_only" and (not isinstance(item.get("v2_rejection_reason"),str) or not item["v2_rejection_reason"]):
                    issues.append("missing_v2_rejection_reason")
                counts[product][decision]+=1
                rows.append({"utc_date":day,"github_run_id":roster.get("github_run_id"),
                             "product":product,"identity_sha256":identity,
                             "source_url":url,"decision":decision,
                             "v2_decision_stage":item.get("v2_decision_stage"),
                             "v2_rejection_reason":item.get("v2_rejection_reason"),
                             "materiality":"UNASSESSED","analyst_reviewed":False,
                             "publisher_rights":"UNVERIFIED"})
    for p in PRODUCTS:
        totals=b126.get("products",{}).get(p,{}) if isinstance(b126,dict) else {}
        for field in ("v1_only","v2_only"):
            if counts[p][field]!=totals.get(field):
                issues.append("b126_"+p+"_"+field+"_count_mismatch")
    ok=not issues and len(rows)>0
    return {"schema":SCHEMA,"candidate_sha":expected_sha,
            "evidence_reconciled":ok,"disagreement_count":len(rows),
            "counts":{p:dict(counts[p]) for p in PRODUCTS},
            "rows":sorted(rows,key=lambda x:(x["utc_date"],x["product"],x["identity_sha256"])),
            "review_status":"PENDING_INDEPENDENT_REVIEW",
            "independent_adjudication_verified":False,
            "publisher_rights_verified":False,"can_release":False,
            "issues":sorted(set(issues))}
