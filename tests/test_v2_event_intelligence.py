import unittest
from v2_event_intelligence import arabic_filter, cluster_candidates, multilingual_candidates, event_evolution
class ProcessingParityTests(unittest.TestCase):
 def test_arabic_filter(self):
  self.assertFalse(arabic_filter("ازدحام مروري بسبب مباراة",region="gcc")["admit"])
  self.assertTrue(arabic_filter("هجوم صاروخي على الحدود",region="iran")["admit"])
  self.assertFalse(arabic_filter("هجوم صاروخي على الحدود",region=None)["admit"])
 def test_reverse_direction_not_merged(self):
  rows=[{"event_id":"a","title":"Iran strikes Israel","region":"iran","published":1000,"source_id":"s1"},{"event_id":"b","title":"Israel strikes Iran","region":"iran","published":1001,"source_id":"s2"}]
  self.assertEqual(cluster_candidates(rows)["automatic_merges"],0)
  self.assertEqual(len(cluster_candidates(rows)["groups"]),2)
 def test_multilingual_review_not_merge(self):
  en=[{"event_id":"a","region":"iran","title":"Iran sanctions announced"}]
  ar=[{"event_id":"b","region":"iran","title":"إيران تعلن عقوبات"}]
  x=multilingual_candidates(en,ar)
  self.assertEqual(x["automatic_merges"],0)
  self.assertEqual(len(x["pairs"]),1)
 def test_history_requires_authenticated_baseline(self):
  self.assertEqual(event_evolution({"a":"v2"},None)["a"],"unknown_no_baseline")
  self.assertEqual(event_evolution({"a":"v2"},{"a":"v1","b":"v3"})["a"],"updated")
  self.assertEqual(event_evolution({"a":"v2"},{"a":"v2"})["a"],"unchanged")
if __name__=="__main__":unittest.main()
