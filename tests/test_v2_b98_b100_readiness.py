import unittest
from v2_b98_b100_readiness import assess
class B98B100Tests(unittest.TestCase):
 def setUp(self):
  self.live={"schema":"aggregateit-v2-b46-live-chain/1","can_release":False,"source_attempts":{x:{"feed_ok":True,"capture_successes":3,"body_gate_rejections":{}} for x in ("english","arabic")}}
  self.visual={"schema":"aggregateit-v2-b88-b90-acceptance/1","can_release":False,"b88_visual":{"native_pages":5,"all_4k_png_verified":True}}
 def test_honest_hold(self):
  r=assess(self.live,self.visual)
  self.assertFalse(r["b98"]["source_fallback_verified"])
  self.assertFalse(r["b99"]["arabic_rtl_independently_verified"])
  self.assertFalse(r["b100"]["fallback_llm_live_tested"])
  self.assertFalse(r["can_release"])
 def test_missing_visual_fails(self):
  self.visual["b88_visual"]["native_pages"]=0
  with self.assertRaises(ValueError):assess(self.live,self.visual)
if __name__=="__main__":unittest.main()
