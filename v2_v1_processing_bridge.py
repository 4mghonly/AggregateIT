"""Pure, bounded migration of V1 editorial selection and dedup primitives.

No import of production engines, side effects, network, storage or delivery.
V1 inspiration: arabic_live_v2.select/_dedupe_key and main.cluster_events.
"""
from __future__ import annotations
import re
from difflib import SequenceMatcher
from collections import Counter

def arabic_select_v1_baseline(rows, limit=13, source_cap=2):
    """UAE-only emphasis; relevance-ranked remainder, V1 source diversity cap.

    The cap is soft: high-impact news is not dropped just because its publisher
    already has two selected items. No per-region quotas.
    """
    if not 1<=limit<=30 or not 1<=source_cap<=10:
        raise ValueError("invalid_selection_limits")
    ranked=sorted(rows,key=lambda x:(-float(x["score"]),str(x.get("id",""))))
    chosen=[]
    uae=next((x for x in ranked if x.get("country")=="AE"),None)
    if uae is not None:
        chosen.append(uae)
    counts=Counter(x.get("source_id") for x in chosen)
    for row in ranked:
        if len(chosen)>=limit:break
        if row is uae:continue
        source=row.get("source_id")
        if counts[source]>=source_cap:continue
        chosen.append(row);counts[source]+=1
    for row in ranked:
        if len(chosen)>=limit:break
        if not any(row is x for x in chosen):chosen.append(row)
    return chosen

def _normalize_title(title):
    return re.sub(r"[^\w]+"," ",str(title or "").casefold(),flags=re.UNICODE).strip()

def event_duplicate_decision(a,b):
    """Exact-title dedup; fuzzy matches require review, not silent event merge."""
    ta=_normalize_title(a.get("title"))
    tb=_normalize_title(b.get("title"))
    if not ta or not tb:return {"duplicate":False,"candidate":False,"reason":"empty_title"}
    try:
        hours=abs(float(a.get("published",0))-float(b.get("published",0)))/3600
    except (ValueError,TypeError):
        return {"duplicate":False,"candidate":False,"reason":"invalid_timestamp"}
    if hours>72:return {"duplicate":False,"candidate":False,"reason":"outside_window"}
    if ta==tb:return {"duplicate":True,"candidate":True,"reason":"identical_normalized_title"}
    ratio=SequenceMatcher(None,ta,tb).ratio()
    # Similar text is insufficient to infer event identity, particularly when
    # actor and target are reversed or the event changes over time.
    return {"duplicate":False,"candidate":ratio>=0.78,"reason":"fuzzy_review_only" if ratio>=0.78 else "distinct"}
