import unittest
from v2_b112_final_acceptance import assess

class B112Tests(unittest.TestCase):
 def test_live_arabic_recovered_but_shadow_zero_is_hold(self):
  live={'schema':'aggregateit-v2-b46-live-chain/1','can_release':False,'editorial':{'products':{'english':{'story_count':3},'arabic':{'story_count':1}}},'arabic_zero_story_diagnosis':{'counts':{'body_gate_rejections':{'no_grounded_region':4}}},'source_recovery':{'arabic':{'fallback_used':True}}}
  shadow={'schema':'aggregateit-v2-b49-single-slot-preflight/1','can_release':False,'rows':[{'product':'english','v2_source_linked_daily_stories':3},{'product':'arabic','v2_source_linked_daily_stories':0}]}
  result=assess(live,shadow)
  self.assertTrue(result['arabic_live_recovered'])
  self.assertTrue(result['arabic_capture_discrepancy'])
  self.assertFalse(result['can_release'])
 def test_untrusted_shadow_rejected(self):
  with self.assertRaises(ValueError):
   assess({'schema':'aggregateit-v2-b46-live-chain/1','can_release':False},{'schema':'wrong','can_release':False})
if __name__=='__main__':unittest.main()
