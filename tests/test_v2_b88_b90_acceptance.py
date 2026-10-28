import unittest
from v2_b88_b90_acceptance import assess
class AcceptanceTests(unittest.TestCase):
 def test_missing_evidence_rejected(self):
  with self.assertRaises(ValueError):assess({}, {}, {})
 def test_no_false_release_even_with_valid_pages(self):
  pages=[{"filename":f"{lang}-no-post-{n}.png","dimensions":[3840,2160],"sha256":"a"*64} for lang,count in (("english",2),("arabic",3)) for n in range(1,count+1)]
  live={"schema":"aggregateit-v2-b46-live-chain/1","can_release":False,"source_attempts":{x:{"article_evidence_eligible":3,"body_gate_rejections":{}} for x in ("english","arabic")},"editorial":{"products":{x:{"story_count":3,"represented_regions":[]} for x in ("english","arabic")}}}
  shadow={"schema":"aggregateit-v2-b49-single-slot-preflight/1","can_release":False,"all_parser_parity":True,"all_source_headline_parity":True}
  result=assess(live,shadow,{"schema":"aggregateit-v2-b86-visual-review/1","pages":pages,"can_release":False})
  self.assertFalse(result["can_release"])
  self.assertFalse(result["b88_visual"]["independent_readability_review"])
  self.assertFalse(result["b90_parity"]["full_v1_v2_parity"])
if __name__=="__main__":unittest.main()
