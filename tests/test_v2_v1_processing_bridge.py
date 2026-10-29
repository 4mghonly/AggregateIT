import unittest
from v2_v1_processing_bridge import arabic_select_v1_baseline, event_duplicate_decision

class V1ProcessingBridgeTests(unittest.TestCase):
 def test_uae_emphasis_without_other_region_quota(self):
  rows=[dict(id="uae",country="AE",score=70,source_id="a"),
        dict(id="iran",country="IR",score=99,source_id="b"),
        dict(id="iraq",country="IQ",score=95,source_id="c"),
        dict(id="jordan",country="JO",score=12,source_id="d")]
  self.assertEqual([x["id"] for x in arabic_select_v1_baseline(rows,3)],["uae","iran","iraq"])
 def test_no_uae_item_relevance_only(self):
  rows=[dict(id="low",country="JO",score=10,source_id="a"),dict(id="high",country="IR",score=90,source_id="b")]
  self.assertEqual([x["id"] for x in arabic_select_v1_baseline(rows,1)],["high"])
 def test_source_diversity_keeps_critical_story(self):
  rows=[dict(id="a",country="IR",score=95,source_id="same"),dict(id="b",country="IQ",score=90,source_id="same"),dict(id="c",country="TR",score=80,source_id="other")]
  self.assertEqual([x["id"] for x in arabic_select_v1_baseline(rows,3)],["a","b","c"])
 def test_similar_titles_distinct_action_are_not_duplicates(self):
  a={"title":"Iran launches missiles toward Israel","published":10000}
  b={"title":"Israel launches missiles toward Iran","published":10001}
  self.assertFalse(event_duplicate_decision(a,b)["duplicate"])
 def test_same_event_rewording_is_candidate_not_auto_merge(self):
  a={"title":"Iran launches missiles toward Israel","published":10000}
  b={"title":"Iran launches missiles at Israel","published":10001}
  self.assertTrue(event_duplicate_decision(a,b)["candidate"])
  self.assertFalse(event_duplicate_decision(a,b)["duplicate"])
 def test_exact_normalized_title_is_duplicate(self):
  a={"title":"Iran launches missiles toward Israel","published":10000}
  b={"title":"IRAN launches missiles toward Israel!","published":10001}
  self.assertTrue(event_duplicate_decision(a,b)["duplicate"])
if __name__=="__main__":unittest.main()
