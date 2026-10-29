import unittest
from v2_v1_processing_bridge import arabic_impact_priority, arabic_relevance_gate
class ArabicImpactTests(unittest.TestCase):
 def test_priority_changes_with_impact(self):
  self.assertGreater(arabic_impact_priority("strategic sanctions announced",age_hours=1),arabic_impact_priority("routine traffic update",age_hours=1))
 def test_recency(self):
  self.assertGreater(arabic_impact_priority("strategic sanctions announced",age_hours=1),arabic_impact_priority("strategic sanctions announced",age_hours=12))
 def test_uae_emphasis(self):
  self.assertGreater(arabic_impact_priority("strategic sanctions announced",age_hours=1,is_uae=True),arabic_impact_priority("strategic sanctions announced",age_hours=1))
 def test_routine_filtered(self):
  self.assertFalse(arabic_relevance_gate("traffic congestion update"))
  self.assertTrue(arabic_relevance_gate("sanctions announced after diplomatic talks"))
if __name__=="__main__":unittest.main()
