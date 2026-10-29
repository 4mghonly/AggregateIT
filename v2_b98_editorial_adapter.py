"""B98 deterministic integration adapter: convert independently validated source captures
into the existing editorial compiler without pretending synthetic tests are live evidence.
"""
from __future__ import annotations
from v2_b98_independent_fallback import route
from v2_b46_live_editorial import ALLOWED,compile_captured_articles

def compile_with_fallback(primary:str,providers:list[dict],*,as_of:str,slot_id:str):
 decision=route(primary,providers)
 chosen=decision["selected_publisher"]
 if chosen is None:
  return {"fallback":decision,"editorial":None,"status":"HOLD_NO_ELIGIBLE_PUBLISHER","can_release":False}
 provider=next(p for p in providers if p["publisher_id"]==chosen)
 product=provider.get("product")
 config=ALLOWED.get(product)
 # The current editorial compiler supports only the original publisher identities.
 # Refuse to mislabel an independent publisher as BBC or Al Jazeera.
 if not config or provider.get("source_id")!=config["source_id"] or provider.get("verified_article_host") not in config["hosts"]:
  return {"fallback":decision,"editorial":None,"status":"HOLD_PUBLISHER_NOT_ONBOARDED_IN_EDITORIAL_COMPILER","can_release":False}
 capture=provider.get("capture")
 if not isinstance(capture,dict) or capture.get("source_id")!=config["source_id"] or capture.get("product")!=product:
  return {"fallback":decision,"editorial":None,"status":"HOLD_MISSING_OR_INVALID_CAPTURE","can_release":False}
 result=compile_captured_articles([capture],as_of=as_of,slot_id=slot_id)
 return {"fallback":decision,"editorial":result,"status":"HELD_EDITORIAL_COMPILED","can_release":False}
