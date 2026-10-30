import unittest
from v2_keyword_priority import score_v1_keyword_title, score_keyword_context

class KeywordContextTests(unittest.TestCase):
    def setUp(self):
        self.config={"clusters":[{"id":"security","prio":"High","phrases":["ceasefire"],"tags":[]}]}

    def test_uses_article_context_when_headline_is_generic(self):
        score,hits=score_keyword_context("Leaders announce progress","Officials discussed a ceasefire",self.config)
        self.assertIn("security",hits)
        self.assertGreater(score,50)

    def test_preserves_title_signal(self):
        title=score_v1_keyword_title("Ceasefire talks",self.config)
        context=score_keyword_context("Ceasefire talks","Additional context",self.config)
        self.assertEqual(title,context)

    def test_no_unrelated_substring_match(self):
        _,hits=score_keyword_context("Meeting","There is no ceasefiresignal here",self.config)
        self.assertEqual(hits,[])

if __name__=="__main__":unittest.main()
