import unittest
from v2_v1_full_scoring import score_english_v1
class EnglishV1ScoreTests(unittest.TestCase):
 def test_keyword_cluster_and_watchlist(self):
  x=score_english_v1("Fed announces inflation update","The Federal Reserve discusses CPI",source_name="Reuters")
  self.assertGreater(x["priority"],50)
  self.assertIn("components",x)
 def test_symbol_boundaries(self):
  a=score_english_v1("NVDA earnings","",source_name="Newswire")
  b=score_english_v1("ANVDA earnings","",source_name="Newswire")
  self.assertGreater(a["components"]["ticker"],b["components"]["ticker"])
 def test_neutral(self):
  self.assertEqual(score_english_v1("Local community announcement","",source_name="Unknown")["components"]["ticker"],0)
if __name__=="__main__":unittest.main()
