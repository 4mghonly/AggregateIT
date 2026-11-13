import unittest
from v2_article_body_gate import headline_geography_candidates,classify_geography

class ExpandedGeographyTests(unittest.TestCase):
 def test_arabic_north_africa(self):
  self.assertIn(("north_africa","LY"),headline_geography_candidates("ليبيا تعلن إجراءات أمنية",language="ar"))
  self.assertIn(("north_africa","MA"),headline_geography_candidates("المغرب يبحث اتفاقا دبلوماسيا",language="ar"))
 def test_english_north_africa(self):
  self.assertIn(("north_africa","LY"),headline_geography_candidates("Libya announces security measures",language="en"))
 def test_arabic_bahrain(self):
  self.assertIn(("gcc","BH"),headline_geography_candidates("البحرين تعلن إجراءات أمنية",language="ar"))
if __name__=="__main__":unittest.main()
