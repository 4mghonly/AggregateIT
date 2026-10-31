import unittest
from v2_b46_live_editorial import SOURCE_CATALOG

class ExpandedPreviewSources(unittest.TestCase):
    def test_more_than_two_publishers_each_language(self):
        for product in ("english","arabic"):
            self.assertGreaterEqual(len(SOURCE_CATALOG[product]),5)
            self.assertEqual(len({s["source_id"] for s in SOURCE_CATALOG[product]}),len(SOURCE_CATALOG[product]))
    def test_arabic_includes_regional_publishers(self):
        self.assertTrue(any(s["source_id"]=="ar-s081" for s in SOURCE_CATALOG["arabic"]))
        self.assertTrue(any(s["source_id"]=="ar-s033" for s in SOURCE_CATALOG["arabic"]))
if __name__=="__main__":unittest.main()
