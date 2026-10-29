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

# Deterministic migration of V1 Arabic impact and routine-vs-strategic gates.
# Kept pure: source evidence and publisher-date verification remain upstream.
_STRATEGIC=("sanctions","diplomacy","military","border","ceasefire","security","naval",
            "عقوبات","دبلوماسية","عسكري","حدود","هدنة","أمن","امن")
_HIGH=("sanctions","ceasefire","military","border","naval",
       "عقوبات","هدنة","عسكري","حدود")
_ROUTINE=("traffic","weather","promotion","lottery","sport","football",
          "مرور","ازدحام","طقس","رياضة","مباراة")
def _phrase_hit(text,phrase):
    return re.search(r"(?<!\\w)"+re.escape(phrase)+r"(?!\\w)",text,re.UNICODE) is not None

def arabic_relevance_gate(text):
    folded=str(text or "").casefold()
    strategic=any(_phrase_hit(folded,t) for t in _STRATEGIC)
    routine=any(_phrase_hit(folded,t) for t in _ROUTINE)
    return strategic and (not routine or strategic)

def arabic_impact_priority(text,*,age_hours,is_uae=False,official=False):
    """V1-inspired age/impact ranking mapped to V2 integer 0..100."""
    folded=str(text or "").casefold()
    age=max(0.0,float(age_hours))
    strategic=any(_phrase_hit(folded,t) for t in _STRATEGIC)
    impact=sum(_phrase_hit(folded,t) for t in _HIGH)
    routine=any(_phrase_hit(folded,t) for t in _ROUTINE)
    v1=max(0.0,4.0-age/4.0)+min(8.0,2.0*impact)
    v1+=2.5 if strategic else 0.0
    v1+=1.25 if official else 0.0
    v1+=0.6 if is_uae else 0.0
    if routine and not strategic:v1-=4.0
    return max(0,min(100,round(45+v1*3)))
