import unittest
from v2_editorial_quality_metrics import assess_coverage

class EditorialQualityMetrics(unittest.TestCase):
    def test_reports_weak_diversity_without_fabricating_regions(self):
        r=assess_coverage({"english":[{"source_id":"a","region":"gcc"},{"source_id":"a","region":"gcc"}],"arabic":[{"source_id":"b","region":"yemen"}]})
        self.assertEqual(r["english"]["publisher_count"],1)
        self.assertEqual(r["english"]["region_count"],1)
        self.assertEqual(r["english"]["concentration"],1.0)
        self.assertFalse(r["english"]["diverse_sources"])
    def test_healthy_diversity(self):
        r=assess_coverage({"english":[{"source_id":"a","region":"gcc"},{"source_id":"b","region":"iran"},{"source_id":"c","region":"yemen"}],"arabic":[]})
        self.assertEqual(r["english"]["region_count"],3)
        self.assertTrue(r["english"]["diverse_sources"])
if __name__=="__main__":unittest.main()
