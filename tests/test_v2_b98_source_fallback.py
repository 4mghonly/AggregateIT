import unittest
from v2_b98_source_fallback import choose_eligible
class B98Tests(unittest.TestCase):
 def test_reject_unapproved_publisher(self):
  with self.assertRaises(ValueError):choose_eligible("english",[{"article_url":"https://unapproved.example/story","source_id":"en-001"}])
 def test_reject_identity_substitution(self):
  with self.assertRaises(ValueError):choose_eligible("arabic",[{"article_url":"https://www.aljazeera.net/news/1","source_id":"en-001"}])
 def test_no_fallback_is_hold(self):
  r=choose_eligible("english",[])
  self.assertEqual(r["status"],"HOLD_NO_ELIGIBLE_FALLBACK")
  self.assertFalse(r["can_release"])
if __name__=="__main__":unittest.main()
