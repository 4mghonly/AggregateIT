"""B66-B71 offline evidence intake: reject fabricated production acceptance."""
from __future__ import annotations
from v2_b61_week_lineage import evaluate_week_lineage
from v2_b60_original_edition_qa import KNOWN_DEFECTS

def _digest(value):
    return isinstance(value,str) and len(value)==64 and all(c in "0123456789abcdef" for c in value)

def b66_sources(rows):
    """At least two distinct compatible, independently observed source receipts."""
    if not isinstance(rows,list) or len(rows)>20: raise ValueError("invalid_sources")
    accepted=set();issues=[];digests=set()
    for row in rows:
        if not isinstance(row,dict):raise ValueError("invalid_source_receipt")
        publisher=row.get("publisher")
        if not isinstance(publisher,str) or not publisher.strip():raise ValueError("missing_publisher")
        if (row.get("http_status")==200 and row.get("parse_compatible") is True
            and type(row.get("fresh_items")) is int and row["fresh_items"]>0
            and row.get("observed_from_live_fetch") is True
            and _digest(row.get("response_sha256"))):
            if row["response_sha256"] in digests:
                issues.append("duplicate_response_digest")
            else:
                accepted.add(publisher.strip().casefold())
                digests.add(row["response_sha256"])
        else:issues.append(publisher)
    return {"compatible_distinct_sources":len(accepted),"unqualified":issues,
            "technical_floor_met":len(accepted)>=2,"activation_allowed":False,
            "arabic_semantic_quality_verified":False,"can_release":False}

def b67_translation(rows):
    """Only evidence-bound human-readable review records; no automatic quality approval."""
    if not isinstance(rows,list) or len(rows)>100:raise ValueError("invalid_translation_rows")
    accepted=0;issues=[]
    for row in rows:
        if not isinstance(row,dict):raise ValueError("invalid_translation_receipt")
        if (row.get("original_language") in ("en","so")
            and _digest(row.get("original_sha256")) and _digest(row.get("arabic_sha256"))
            and row.get("numbers_preserved") is True and row.get("negation_preserved") is True
            and row.get("attribution_preserved") is True and row.get("review_provenance")=="independent"):
            accepted+=1
        else:issues.append("missing_independent_semantic_evidence")
    return {"reviewed_rows":accepted,"issues":issues,
            "publisher_story_semantic_fidelity_verified":False,"can_release":False}

def b68_visual(pages, reviewed_defects):
    """Technical defect register; cannot replace image and phone review."""
    if not isinstance(reviewed_defects,dict):raise ValueError("missing_defect_register")
    outstanding=[key for key in KNOWN_DEFECTS if reviewed_defects.get(key)!="resolved_with_source_synced_visual_receipt"]
    return {"pages_present":len(pages) if isinstance(pages,list) else 0,
            "outstanding_defects":outstanding,
            "physical_client_review_verified":False,"can_release":False}

def b69_week(records, as_of):
    result=evaluate_week_lineage(records,as_of=as_of)
    return {"observed_days":result["observed_days"],
            "missing_days":result["missing_days"],
            "structurally_complete":result["seven_distinct_days_structurally_present"],
            "offhost_signed":False,"can_release":False}

def b70_parity(pairs):
    """Compare independently pinned same-slot source digests; editorial parity remains held."""
    if not isinstance(pairs,list) or len(pairs)>50:raise ValueError("invalid_pairs")
    matching=0;rejected=0
    for pair in pairs:
        if not isinstance(pair,dict):raise ValueError("invalid_pair")
        if (pair.get("same_utc_slot") is True and _digest(pair.get("source_sha256"))
            and _digest(pair.get("v1_edition_sha256")) and _digest(pair.get("v2_edition_sha256"))
            and pair.get("v1_source_sha256")==pair["source_sha256"]
            and pair.get("v2_source_sha256")==pair["source_sha256"]):
            matching+=1
        else:rejected+=1
    return {"same_source_pairs":matching,"rejected_pairs":rejected,
            "full_editorial_model_render_delivery_parity_verified":False,"can_release":False}

def b71_delivery(model_receipts, discord_receipts):
    """Model/Discord self assertions never become independent client proof."""
    if not isinstance(model_receipts,list) or not isinstance(discord_receipts,list):
        raise ValueError("invalid_delivery_receipts")
    return {"model_receipts_supplied":len(model_receipts),
            "discord_receipts_supplied":len(discord_receipts),
            "live_primary_fallback_independently_verified":False,
            "independent_discord_client_receipts_verified":False,
            "discord_sent":False,"can_release":False}

def execute_all(*,sources=(),translations=(),pages=(),defects=None,
                week=(),as_of="2026-10-28T18:00:00+04:00",pairs=(),
                model_receipts=(),discord_receipts=()):
    results={"b66":b66_sources(list(sources)),"b67":b67_translation(list(translations)),
             "b68":b68_visual(list(pages),defects or {}),
             "b69":b69_week(list(week),as_of),
             "b70":b70_parity(list(pairs)),
             "b71":b71_delivery(list(model_receipts),list(discord_receipts))}
    return {"schema":"aggregateit-v2-b66-b71-offline/1","results":results,
            "production_release":"HOLD","can_release":False,
            "paid_calls":0,"discord_sent":False}
