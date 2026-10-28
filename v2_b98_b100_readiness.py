"""B98-100: no-post source, visual and LLM failover readiness gates."""
from __future__ import annotations
import json
from pathlib import Path

def assess(live:dict,visual:dict)->dict:
 if live.get("schema")!="aggregateit-v2-b46-live-chain/1" or live.get("can_release") is not False:raise ValueError("untrusted_live")
 if visual.get("schema")!="aggregateit-v2-b88-b90-acceptance/1" or visual.get("can_release") is not False:raise ValueError("untrusted_visual")
 sources={}
 for lang in ("english","arabic"):
  item=live.get("source_attempts",{}).get(lang)
  if not isinstance(item,dict):raise ValueError("missing_source")
  sources[lang]={"feed_ok":item.get("feed_ok") is True,"article_capture_successes":item.get("capture_successes",0),"article_rejection_reasons":item.get("body_gate_rejections",{}),"independent_fallback_feed_tested":False,"automatic_replacement_authorized":False}
 b88=visual["b88_visual"]
 if b88.get("native_pages")!=5 or b88.get("all_4k_png_verified") is not True:raise ValueError("missing_valid_visual_pages")
 return {"schema":"aggregateit-v2-b98-b100-readiness/1","b98":{"source_health":sources,"source_fallback_verified":False},"b99":{"five_4k_pages_validated":True,"readability_independently_verified":False,"arabic_rtl_independently_verified":False,"font_clipping_independently_verified":False},"b100":{"primary_llm_live_tested":False,"fallback_llm_live_tested":False,"translation_quality_verified":False,"graceful_degradation_verified":False},"can_release":False,"discord_sent":False}
def main():
 live=json.loads(Path("b80_b81_live_editorial.json").read_text())
 visual=json.loads(Path("b88_b90_acceptance.json").read_text())
 result=assess(live,visual)
 Path("b98_b100_readiness.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
