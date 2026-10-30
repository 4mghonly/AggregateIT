import unittest
from v2_v1_full_scoring import score_english_v1

class ScoringTagEnhancement(unittest.TestCase):
    def test_cluster_tags_add_relevance_without_title_phrase(self):
        cfg={"clusters":[{"id":"strategic","prio":"High","phrases":["unlikely phrase"],"tags":["naval"]}]}
        result=score_english_v1("Regional meeting","Officials discussed naval security.",keyword_config=cfg,watchlist={"tickers":[],"keywords":[]})
        self.assertIn("strategic",result["keyword_ids"])
        self.assertGreater(result["priority"],50)
    def test_no_duplicate_cluster_weight_when_phrase_and_tag_match(self):
        cfg={"clusters":[{"id":"strategic","prio":"High","phrases":["naval"],"tags":["security"]}]}
        result=score_english_v1("Naval security talks",keyword_config=cfg,watchlist={"tickers":[],"keywords":[]})
        self.assertEqual(result["components"]["keyword"],3)
if __name__=="__main__":unittest.main()
