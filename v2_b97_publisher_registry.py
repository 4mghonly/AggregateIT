"""B97/B98 explicit independent-publisher admission registry.

A feed cannot become a fallback merely because its URL responds. The operator
must provide publisher-identity, feed/article-domain and evidence-gate receipts.
Unvalidated publishers are held; no production sources are modified.
"""
from __future__ import annotations
from urllib.parse import urlsplit

def evaluate(publishers:list[dict],*,required_languages=("english","arabic"))->dict:
 if not isinstance(publishers,list) or len(publishers)>30:raise ValueError("invalid_publisher_registry")
 verified={lang:set() for lang in required_languages}
 held={}
 for item in publishers:
  if not isinstance(item,dict):raise ValueError("invalid_publisher")
  identity=item.get("publisher_id")
  lang=item.get("language")
  if not isinstance(identity,str) or not 1<=len(identity)<=64 or lang not in verified:raise ValueError("invalid_publisher_identity")
  if identity in held or any(identity in v for v in verified.values()):raise ValueError("duplicate_publisher_identity")
  url=item.get("feed_url")
  if not isinstance(url,str):raise ValueError("invalid_publisher_feed")
  parts=urlsplit(url)
  if parts.scheme!="https" or not parts.hostname or parts.username or parts.password or parts.port not in (None,443):raise ValueError("unsafe_publisher_feed")
  if item.get("publisher_identity_verified") is True and item.get("feed_capture_verified") is True and item.get("article_body_gate_verified") is True and item.get("source_rights_reviewed") is True:
   verified[lang].add(identity)
  else:held[identity]="HOLD_MISSING_INDEPENDENT_PUBLISHER_EVIDENCE"
 return {"schema":"aggregateit-v2-b97-publisher-registry/1","verified_publisher_counts":{k:len(v) for k,v in verified.items()},"independent_fallback_available":{k:len(v)>=2 for k,v in verified.items()},"held_publishers":held,"can_release":False}

if __name__=="__main__":
 import json
 print(json.dumps(evaluate([])))
