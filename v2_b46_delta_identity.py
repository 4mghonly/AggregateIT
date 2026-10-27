"""B46 stage 3: strictly operator-HMAC-bound prior edition versions and review-only joins.

A valid HMAC protects an operator's journal checkpoint, NOT publisher authenticity,
fact accuracy, external checkpoint retention or automatic same-event identity.
Never infer a previous slot from an unsourced map. No file or network I/O.
"""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
from v2_evidence import _time
from v2_evidence_anchor import verify_anchor
from v2_evidence_journal import EvidenceJournal

def _utc(value):
    return datetime.fromisoformat(_time(value)).astimezone(timezone.utc)

def versions_from_signed_journal(snapshot:dict, *, as_of:str)->dict:
    if not isinstance(snapshot,dict) or set(snapshot)!={"journal_text","anchor","key_id","secret"}:
        raise ValueError("prior_snapshot_requires_exact_signed_journal")
    data=snapshot["journal_text"]
    anchor=snapshot["anchor"]
    if not isinstance(data,str) or not isinstance(anchor,dict):
        raise ValueError("invalid_prior_journal")
    receipt=anchor.get("receipt")
    if not isinstance(receipt,dict):
        raise ValueError("prior_anchor_receipt_missing")
    prior=EvidenceJournal.replay(data,expected_head=receipt.get("head_sha256"))
    recalculated=prior.receipt()
    if recalculated!=receipt:
        raise ValueError("prior_journal_receipt_mismatch")
    verify_anchor(anchor,recalculated,secret=snapshot["secret"],expected_key_id=snapshot["key_id"])
    start=_utc(anchor["issued_at_utc"])
    present=_utc(as_of)
    if not start < present or (present-start).total_seconds()>7*86400:
        raise ValueError("prior_anchor_outside_bounded_window")
    if recalculated["seq"]<1 or not prior.ledger._events:
        raise ValueError("prior_edition_no_evidence_events")
    versions={event_id:history[-1]["version_id"]
              for event_id,history in prior.ledger._events.items() if history}
    if not versions or len(versions)>200:
        raise ValueError("unbounded_prior_events")
    return {"versions":versions,
            "baseline_status":"operator_hmac_verified_not_independently_retained",
            "prior_anchor_sha256":sha256(
                 __import__('json').dumps(anchor,ensure_ascii=False,sort_keys=True,
                      separators=(',',':')).encode('utf8')).hexdigest(),
            "independent_off_host_checkpoint_verified":False,
            "publisher_event_truth_verified":False}

def review_only_cross_language_pairs(products:dict, *, max_pairs:int=12)->dict:
    if type(max_pairs) is not int or not 1<=max_pairs<=30:
        raise ValueError("invalid_pair_ceiling")
    if not isinstance(products,dict) or set(products)!={"english","arabic"}:
        raise ValueError("invalid_product_pair")
    records={}
    for product in ("english","arabic"):
        x=products[product]
        if not isinstance(x,dict) or x.get("no_publication_authority") is not True:
            raise ValueError("untrusted_editorial_products")
        stories=x.get("newsroom",{}).get("stories")
        if not isinstance(stories,list) or len(stories)>30:
            raise ValueError("invalid_editorial_stories")
        records[product]=stories
    pairs=[];total=0
    for left in records["english"]:
        for right in records["arabic"]:
            if (not isinstance(left,dict) or not isinstance(right,dict)
                or not isinstance(left.get("region"),str)
                or not isinstance(right.get("region"),str)):
                raise ValueError("invalid_pair_record")
            if left["region"]!=right["region"]:continue
            if (not isinstance(left.get("event_id"),str) or
                not isinstance(right.get("event_id"),str)
                or not isinstance(left.get("excerpt_id"),str) or
                not isinstance(right.get("excerpt_id"),str)):
                raise ValueError("unlinked_pair")
            total+=1
            if len(pairs)<max_pairs:
                pair_hash=sha256((left["event_id"]+"|"+right["event_id"]).encode("utf8")).hexdigest()
                pairs.append({"pair_digest":pair_hash,"region":left["region"],
                    "english_event_id":left["event_id"],"arabic_event_id":right["event_id"],
                    "english_excerpt_id":left["excerpt_id"],"arabic_excerpt_id":right["excerpt_id"],
                    "reason":"common_geographic_region_only",
                    "semantic_event_identity":"UNVERIFIED",
                    "operator_review_required":True})
    return {"schema":"aggregateit-v2-b46-cross-language-review/1",
            "candidate_pairs":pairs,"candidate_count":total,
            "omitted_over_budget":max(0,total-len(pairs)),
            "publisher_independence_verified":False,"automatic_merge_performed":False,
            "model_translation_called":False,"can_publish":False}
