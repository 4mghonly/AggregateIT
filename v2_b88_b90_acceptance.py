"""B88-B90 fail-closed acceptance synthesis from genuine hosted receipts."""
from __future__ import annotations
import json
from pathlib import Path
from hashlib import sha256

def assess(live,shadow,archive):
 if live.get("schema")!="aggregateit-v2-b46-live-chain/1" or live.get("can_release") is not False:raise ValueError("untrusted_live_receipt")
 if shadow.get("schema")!="aggregateit-v2-b49-single-slot-preflight/1" or shadow.get("can_release") is not False:raise ValueError("untrusted_shadow")
 pages=archive.get("pages",[])
 if archive.get("schema")!="aggregateit-v2-b86-visual-review/1" or len(pages)!=5 or archive.get("can_release") is not False:raise ValueError("incomplete_visual_evidence")
 expected={f"{lang}-no-post-{i}.png" for lang,count in (("english",2),("arabic",3)) for i in range(1,count+1)}
 if {p.get("filename") for p in pages}!=expected or any(p.get("dimensions")!=[3840,2160] or len(p.get("sha256",""))!=64 for p in pages):raise ValueError("invalid_page_manifest")
 source=live["source_attempts"]
 products=live["editorial"]["products"]
 region_gaps={}
 for lang in ("english","arabic"):
  if lang not in source or lang not in products:raise ValueError("missing_language")
  region_gaps[lang]={"eligible_articles":source[lang]["article_evidence_eligible"],"selected_stories":products[lang]["story_count"],"represented_regions":products[lang]["represented_regions"],"rejection_reasons":source[lang]["body_gate_rejections"]}
 visual={"native_pages":len(pages),"all_4k_png_verified":True,"independent_readability_review":False,"text_clipping_independently_verified":False,"arabic_rtl_independently_verified":False}
 parity={"parser_and_headline_equal":shadow.get("all_parser_parity") is True and shadow.get("all_source_headline_parity") is True,"full_v1_v2_parity":False}
 blockers=["independent_visual_qa","seven_real_days_per_language","geographic_source_redundancy","live_llm_translation_and_fallback","full_v1_v2_editorial_render_delivery_parity","independent_discord_delivery_receipts","publisher_factuality_and_release_authorization"]
 if not all(products[x]["story_count"]>0 for x in ("english","arabic")):blockers.insert(0,"missing_bilingual_editorial")
 return {"schema":"aggregateit-v2-b88-b90-acceptance/1","b88_visual":visual,"b89_source_coverage":region_gaps,"b90_parity":parity,"open_gates":blockers,"can_release":False,"discord_sent":False}

def main():
 from v2_b86_visual_archive import validate_page_archive
 live=json.loads(Path("b80_b81_live_editorial.json").read_text())
 shadow=json.loads(Path("b83_same_slot_shadow.json").read_text())
 archive=validate_page_archive(Path("b86-visual-review"))
 result=assess(live,shadow,archive)
 Path("b88_b90_acceptance.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"schema":result["schema"],"visual":result["b88_visual"],"sources":result["b89_source_coverage"],"parity":result["b90_parity"],"open_gates":result["open_gates"]},ensure_ascii=False))
if __name__=="__main__":main()
