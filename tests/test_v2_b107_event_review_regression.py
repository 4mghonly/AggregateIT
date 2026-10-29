import unittest
from v2_event_intelligence import cluster_candidates,multilingual_candidates
class CandidateRankingTests(unittest.TestCase):
 def test_region_only_candidate_not_semantic(self):
  a=[{"event_id":"a","region":"iran","title":"Iran announces sanctions"}]
  b=[{"event_id":"b","region":"iran","title":"إيران تعلن عقوبات"}]
  result=multilingual_candidates(a,b)
  self.assertEqual(result["pairs"][0]["semantic_identity"],"unverified")
  self.assertEqual(result["automatic_merges"],0)
 def test_cluster_same_event_review_only(self):
  rows=[{"event_id":"a","region":"iran","title":"Iran missile attack at border","source_id":"s1"},
        {"event_id":"b","region":"iran","title":"Iran missile attack at border","source_id":"s2"}]
  result=cluster_candidates(rows)
  self.assertEqual(len(result["review_pairs"]),1)
  self.assertEqual(result["automatic_merges"],0)
 def test_cluster_reverse_direction_not_silently_merged(self):
  rows=[{"event_id":"a","region":"iran","title":"Iran attacks Israel","source_id":"s1"},
        {"event_id":"b","region":"iran","title":"Israel attacks Iran","source_id":"s2"}]
  result=cluster_candidates(rows)
  self.assertEqual(result["automatic_merges"],0)
if __name__=="__main__":unittest.main()
