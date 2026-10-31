import unittest
from v2_b116_collection_policy import should_try_source, source_attempt_budget
class CollectionPolicyTests(unittest.TestCase):
 def test_normal_collection_does_not_stop_after_one_publisher(self):
  self.assertTrue(should_try_source(position=1,quality_preview=False,eligible_count=3,distinct_publishers=1,offline_snapshots=False))
 def test_stop_when_diverse_and_sufficient(self):
  self.assertFalse(should_try_source(position=5,quality_preview=False,eligible_count=9,distinct_publishers=3,offline_snapshots=False))
 def test_offline_snapshots_do_not_open_network(self):
  self.assertFalse(should_try_source(position=1,quality_preview=True,eligible_count=0,distinct_publishers=0,offline_snapshots=True))
 def test_bounded_feed_budget(self):
  self.assertLessEqual(source_attempt_budget(True),12)
  self.assertLessEqual(source_attempt_budget(False),8)
if __name__=="__main__":unittest.main()
