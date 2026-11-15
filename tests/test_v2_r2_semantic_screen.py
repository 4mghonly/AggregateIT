import unittest
from v2_r2_semantic_screen import screen

class SemanticScreenTests(unittest.TestCase):
    def test_uncertain_english_claim_requires_review(self):
        r=screen(product="english",quote="Officials proposed a new measure.",assessment="Officials implemented the measure.")
        self.assertIn("uncertainty_missing_review",r["flags"])
        self.assertFalse(r["independent_fact_verified"])
    def test_unattributed_number_requires_review(self):
        r=screen(product="english",quote="Officials met on Monday.",assessment="Officials met 12 times.")
        self.assertIn("numbers_not_in_excerpt",r["flags"])
    def test_arabic_script_gate(self):
        r=screen(product="arabic",quote="قد يعلن المسؤولون خطة.",assessment="Officials announced the plan.")
        self.assertIn("arabic_script_insufficient",r["flags"])
    def test_negation_mismatch(self):
        r=screen(product="english",quote="The ministry denied the report.",assessment="The ministry confirmed the report.")
        self.assertIn("negation_mismatch_review",r["flags"])
    def test_clear_is_not_verified(self):
        r=screen(product="english",quote="The committee met today.",assessment="The committee met today.")
        self.assertEqual(r["status"],"SCREEN_CLEAR_UNVERIFIED")
        self.assertFalse(r["independent_fact_verified"])
if __name__=="__main__":unittest.main()
