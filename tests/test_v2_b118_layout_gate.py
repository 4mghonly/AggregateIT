import unittest
from v2_b118_layout_gate import layout_preflight
class LayoutGateTests(unittest.TestCase):
 def test_three_arabic_pages_uae_first_analytics_last(self):
  x=layout_preflight([{"region":"gcc","subject_country":"AE"},{"region":"yemen","subject_country":"YE"},{"region":"iran","subject_country":"IR"}],language="ar")
  self.assertEqual(len(x["pages"]),3)
  self.assertEqual(x["pages"][0]["section"],"uae_and_priority")
  self.assertEqual(x["pages"][-1]["section"],"analytics_and_watch")
 def test_empty_uae_is_explicit_not_fabricated(self):
  x=layout_preflight([{"region":"yemen","subject_country":"YE"}],language="ar")
  self.assertFalse(x["uae_evidence_present"])
  self.assertEqual(x["pages"][0]["item_count"],1)
 def test_overflow_flagged(self):
  x=layout_preflight([{"region":"yemen","subject_country":"YE"}]*20,language="ar")
  self.assertFalse(x["within_page_budget"])
if __name__=="__main__":unittest.main()
