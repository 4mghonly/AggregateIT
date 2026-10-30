"""Regression tests for V2 quality-mode geography without weakening attribution."""
import unittest
from v2_article_body_gate import classify_geography

class QualityGeographyTests(unittest.TestCase):
    def test_english_lead_explicit_country_without_headline_country(self):
        result=classify_geography(
            "Officials announce new regional security measures",
            "Officials in Qatar announced new regional security measures following consultations.",
            language="en")
        self.assertEqual(result["subject_country"],"QA")
        self.assertEqual(result["classification_status"],"article_lead_single_explicit_country")

    def test_english_lead_ambiguous_countries_still_rejected(self):
        with self.assertRaisesRegex(ValueError,"ambiguous_geography"):
            classify_geography("Regional officials announce talks",
                "Officials in Qatar and Saudi Arabia announced talks.",language="en")

    def test_english_lead_without_country_still_rejected(self):
        with self.assertRaisesRegex(ValueError,"no_grounded_region"):
            classify_geography("Regional officials announce talks",
                "Officials announced new talks after a meeting.",language="en")

if __name__=="__main__":
    unittest.main()
