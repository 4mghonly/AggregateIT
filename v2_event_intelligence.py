"""No-post deterministic V1-inspired filtering and event intelligence.

All fuzzy and cross-language matches are review-only. Authenticated prior
versions are required for historical claims. Never changes evidence identity.
"""
from __future__ import annotations
from collections import defaultdict
from difflib import SequenceMatcher
import re

SECURITY=("security","military","missile","drone","attack","border","sanctions","ceasefire","diplomacy","nuclear","naval","terror","police",
          "امن","أمن","عسكري","صاروخ","مسيرة","مسيّرة","هجوم","حدود","عقوبات","هدنة","دبلوماس","دبلوماسية","نووي","بحري","شرطة",
          "sécurité","militaire","attaque","güvenlik","saldırı","امنیت","نظامی","حمله","موشک","amni","weerar")
ROUTINE=("traffic","football","sport","restaurant","hotel","lottery","weather","promotion",
         "مرور","ازدحام","مباراة","رياضة","مطعم","فندق","طقس","ترويج")
STRATEGIC=("missile","attack","sanctions","border","military","ceasefire","nuclear","naval","terror",
           "صاروخ","هجوم","عقوبات","حدود","عسكري","هدنة","نووي","بحري","ارهاب","إرهاب")
def _hit(text,word):
 return bool(re.search(r"(?<!\w)"+re.escape(word)+r"(?!\w)",text))
def arabic_filter(text,*,region,uae_secondary=False,headline=None,lead=None):
 """B114 unified Arabic topic/relevance decision; geography supplied by evidence.

 A legacy one-argument call is treated as headline-like text for compatibility.
 When source-backed headline and article lead are available, pass both so
 collector prechecks and editorial compiler use identical evidence.
 """
 from v2_b114_arabic_topic_policy import classify_arabic_event
 title=str(text or "") if headline is None else headline
 opening="" if lead is None else lead
 result=classify_arabic_event(title,opening,region=region,
                              uae_secondary=uae_secondary)
 return result

def _tokens(title):
 return set(re.findall(r"\w+",str(title or "").casefold()))
def cluster_candidates(rows,*,limit=200):
 """V1-inspired similarity proposals; never combine source-backed event IDs."""
 if not isinstance(rows,list) or len(rows)>limit:raise ValueError("unbounded_events")
 groups=[{"event_id":r["event_id"],"source_id":r.get("source_id"),"region":r.get("region")} for r in rows]
 pairs=[]
 for i,left in enumerate(rows):
  for right in rows[i+1:]:
   if left.get("region")!=right.get("region"):continue
   a,b=_tokens(left.get("title")),_tokens(right.get("title"))
   sim=len(a&b)/len(a|b) if a and b else 0
   if sim>=0.45:
    pairs.append({"left":left["event_id"],"right":right["event_id"],
                  "similarity":round(sim,3),"review_required":True,
                  "reason":"title_overlap_not_event_identity"})
 return {"groups":groups,"review_pairs":pairs[:50],"omitted_pairs":max(0,len(pairs)-50),"automatic_merges":0}

def suppress_display_duplicates(rows, *, similarity=0.92):
 """Display-only same-publisher duplicate suppression; evidence IDs untouched.

 Cross-publisher similarities remain visible and eligible for independent
 corroboration review. Region and publisher must match.
 """
 if not isinstance(rows,list) or len(rows)>200:
  raise ValueError("unbounded_display_candidates")
 visible=[];hidden=[]
 for row in rows:
  if not isinstance(row,dict) or not row.get("event_id") or not row.get("source_id"):
   raise ValueError("invalid_display_candidate")
  normalized=" ".join(str(row.get("title","")).casefold().split())
  duplicate=False
  for prior in visible:
   if prior["source_id"]!=row["source_id"] or prior.get("region")!=row.get("region"):
    continue
   old=" ".join(str(prior.get("title","")).casefold().split())
   if normalized and old and SequenceMatcher(None,normalized,old).ratio()>=similarity:
    duplicate=True;break
  if duplicate:hidden.append(row["event_id"])
  else:visible.append(row)
 return {"visible":visible,"hidden_event_ids":hidden,"automatic_merges":0}

def multilingual_candidates(english,arabic,*,limit=12):
 """Geographic join only; no translation or identity claim."""
 pairs=[]
 for a in english:
  for b in arabic:
   if a.get("region") and a.get("region")==b.get("region"):
    pairs.append({"english_event_id":a["event_id"],"arabic_event_id":b["event_id"],
                  "reason":"common_region_only","semantic_identity":"unverified",
                  "review_required":True})
 return {"pairs":pairs[:limit],"omitted_pairs":max(0,len(pairs)-limit),
         "automatic_merges":0,"model_called":False}
def event_evolution(current,authenticated_previous=None):
 """Event-ID/version changes only; never infer escalation from unverified prose."""
 if authenticated_previous is None:return {k:"unknown_no_baseline" for k in current}
 return {k:("new" if k not in authenticated_previous else
            "unchanged" if authenticated_previous[k]==v else "updated")
         for k,v in current.items()}
