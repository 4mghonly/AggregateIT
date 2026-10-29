"""B98 source fallback selection: explicitly allowlisted candidates only.

A fallback can be selected only when its independently captured article
passes the same publisher evidence gate. No cross-publisher source identity
substitution, automatic trust promotion or publication.
"""
from __future__ import annotations
from urllib.parse import urlsplit
from v2_article_body_gate import extract_body,article_evidence
from v2_b46_live_editorial import ALLOWED

def choose_eligible(product:str,candidates:list[dict],*,max_attempts:int=6)->dict:
 if product not in ALLOWED or type(max_attempts)!=int or not 1<=max_attempts<=6:raise ValueError("invalid_fallback_scope")
 if not isinstance(candidates,list) or len(candidates)>12:raise ValueError("invalid_fallback_candidates")
 config=ALLOWED[product];attempts=0;rejections={}
 for candidate in candidates:
  if not isinstance(candidate,dict):raise ValueError("invalid_fallback_candidate")
  url=candidate.get("article_url")
  if not isinstance(url,str):raise ValueError("invalid_fallback_url")
  parts=urlsplit(url)
  if parts.scheme!="https" or parts.hostname not in config["hosts"] or parts.username or parts.password or parts.port not in (None,443):
   raise ValueError("unapproved_fallback_publisher")
  if candidate.get("source_id")!=config["source_id"]:raise ValueError("fallback_source_identity_mismatch")
  if attempts>=max_attempts:break
  attempts+=1
  try:
   body=extract_body(candidate["html_bytes"],source_url=url,language=config["language"])
   article_evidence(body,headline=candidate["title"],published_at=candidate["published_at"])
  except (ValueError,KeyError,TypeError) as exc:
   reason=type(exc).__name__ if not isinstance(exc,ValueError) else str(exc)[:80]
   rejections[reason]=rejections.get(reason,0)+1
   continue
  return {"status":"ELIGIBLE_SOURCE_BACKED_CANDIDATE","selected_index":attempts-1,"attempts":attempts,"rejections":rejections,"can_release":False}
 return {"status":"HOLD_NO_ELIGIBLE_FALLBACK","selected_index":None,"attempts":attempts,"rejections":rejections,"can_release":False}
