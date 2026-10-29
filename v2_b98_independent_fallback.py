"""B97/B98 independent publisher fallback router.

Only validated publisher identities with explicitly matching article domains
may be considered. The router is deterministic, bounded, and no-post.
"""
from __future__ import annotations
from urllib.parse import urlsplit

def route(primary:str,providers:list[dict],*,max_candidates:int=4)->dict:
 if not isinstance(primary,str) or not primary or not isinstance(providers,list) or len(providers)>12:raise ValueError("invalid_fallback_configuration")
 if type(max_candidates)!=int or not 1<=max_candidates<=4:raise ValueError("invalid_attempt_budget")
 seen=set();attempts=[];winner=None
 for p in providers:
  if not isinstance(p,dict):raise ValueError("invalid_provider")
  name=p.get("publisher_id")
  if not isinstance(name,str) or not name or name in seen:raise ValueError("duplicate_or_missing_publisher")
  seen.add(name)
  url=p.get("article_url")
  if not isinstance(url,str):raise ValueError("invalid_article_url")
  parsed=urlsplit(url)
  domain=p.get("verified_article_host")
  if parsed.scheme!="https" or parsed.hostname!=domain or parsed.username or parsed.password or parsed.port not in (None,443):raise ValueError("publisher_domain_mismatch")
  if not all(p.get(flag) is True for flag in ("publisher_identity_verified","feed_capture_verified","article_body_gate_verified","source_rights_reviewed")):
   attempts.append({"publisher_id":name,"status":"HOLD_UNVERIFIED_PUBLISHER"})
   continue
  if len([a for a in attempts if a["status"]!="HOLD_UNVERIFIED_PUBLISHER"])>=max_candidates:break
  ok=p.get("live_article_evidence_eligible") is True
  attempts.append({"publisher_id":name,"status":"ELIGIBLE" if ok else "FAILED_SOURCE_EVIDENCE"})
  if ok:
   winner=name;break
 return {"schema":"aggregateit-v2-b98-independent-fallback/1","primary":primary,"selected_publisher":winner,"independent_fallback_used":winner is not None and winner!=primary,"attempts":attempts,"can_release":False}

if __name__=="__main__":
 import json
 print(json.dumps(route("primary",[])))
