import unittest
from v2_event_intelligence import suppress_display_duplicates
class DisplayDuplicates(unittest.TestCase):
 def test_same_publisher_near_duplicate_hidden_without_merging_events(self):
  rows=[{"event_id":"a","source_id":"one","region":"yemen","title":"Yemen security forces report missile attack near port"},
        {"event_id":"b","source_id":"one","region":"yemen","title":"Yemen security forces report missile attack near port"},
        {"event_id":"c","source_id":"two","region":"yemen","title":"Yemen security forces report missile attack near port"}]
  result=suppress_display_duplicates(rows)
  self.assertEqual([r["event_id"] for r in result["visible"]],["a","c"])
  self.assertEqual(result["hidden_event_ids"],["b"])
  self.assertEqual(result["automatic_merges"],0)
 def test_distinct_headlines_retained(self):
  rows=[{"event_id":"a","source_id":"one","region":"yemen","title":"Yemen port incident"},
        {"event_id":"b","source_id":"one","region":"yemen","title":"Yemen central bank policy"}]
  self.assertEqual(len(suppress_display_duplicates(rows)["visible"]),2)
if __name__=="__main__":unittest.main()
