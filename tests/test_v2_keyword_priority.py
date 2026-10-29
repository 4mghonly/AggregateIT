import unittest
from v2_keyword_priority import score_v1_keyword_title

class KeywordPriorityTests(unittest.TestCase):
    def test_phrase_and_tag_match(self):
        config={"clusters":[{"id":"ME-01","prio":"Critical","tags":["iran"],"phrases":["strait of hormuz"]}]}
        score, hits=score_v1_keyword_title("Iran reports developments in the Strait of Hormuz",config)
        self.assertGreater(score,50)
        self.assertEqual(hits,["ME-01"])
    def test_word_boundaries_prevent_false_hits(self):
        config={"clusters":[{"id":"X","prio":"High","tags":["war"],"phrases":[]}]}
        self.assertEqual(score_v1_keyword_title("Forward-looking markets",config),(50,[]))
    def test_no_match_stays_neutral(self):
        self.assertEqual(score_v1_keyword_title("Other news",{"clusters":[]}), (50,[]))
    def test_no_geographic_preference(self):
        config={"clusters":[{"id":"X","prio":"High","tags":["security"],"phrases":[]}]}
        a=score_v1_keyword_title("Jordan security development",config)
        b=score_v1_keyword_title("Iran security development",config)
        self.assertEqual(a,b)
    def test_invalid_config_fails_closed(self):
        with self.assertRaises(ValueError):
            score_v1_keyword_title("Test",{"clusters":"bad"})
if __name__=="__main__":unittest.main()
