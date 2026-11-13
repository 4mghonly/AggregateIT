import unittest
from v2_b128_adjudication import assess
SHA="b67a9e4115f4f88049716d608e54a6d06ef5f15f"
def fixtures():
    rows=[{"utc_date":"2026-11-06","product":"arabic","identity_sha256":"a"*64,"source_url":"https://example.org/a","decision":"v1_only","v2_rejection_reason":"no_grounded_region","analyst_reviewed":False,"materiality":"UNASSESSED","publisher_rights":"UNVERIFIED"},
          {"utc_date":"2026-11-06","product":"english","identity_sha256":"b"*64,"source_url":"https://example.org/b","decision":"v2_only","v2_rejection_reason":None,"analyst_reviewed":False,"materiality":"UNASSESSED","publisher_rights":"UNVERIFIED"}]
    queue={"schema":"aggregateit-v2-b127-identity-matched-review/1","candidate_sha":SHA,"evidence_reconciled":True,"disagreement_count":2,"rows":rows,"issues":[],"can_release":False}
    return queue,{"schema":"aggregateit-v2-b126-weekly-editorial-audit/1","candidate_sha":SHA,"source_roster_seven_days":True,"verified_dates":["2026-11-%02d"%i for i in range(6,13)],"can_release":False,"issues":[]}
class Tests(unittest.TestCase):
    def test_triage_does_not_adjudicate(self):
        q,b=fixtures();out=assess(q,b,expected_sha=SHA)
        self.assertTrue(out["review_queue_valid"])
        self.assertEqual(out["triage"]["grounding"],1)
        self.assertEqual(out["triage"]["v2_only_requires_review"],1)
        self.assertEqual(out["reviewed_count"],0)
        self.assertFalse(out["independent_adjudication_verified"])
        self.assertFalse(out["weekly_full_product_verified"])
        self.assertFalse(out["can_release"])
    def test_mismatch_count_fails_closed(self):
        q,b=fixtures();q["disagreement_count"]=3
        self.assertFalse(assess(q,b,expected_sha=SHA)["review_queue_valid"])
    def test_untrusted_review_flag_fails_closed(self):
        q,b=fixtures();q["rows"][0]["analyst_reviewed"]=True
        self.assertFalse(assess(q,b,expected_sha=SHA)["review_queue_valid"])
    def test_duplicate_identity_fails_closed(self):
        q,b=fixtures();q["rows"].append(dict(q["rows"][0]));q["disagreement_count"]=3
        self.assertFalse(assess(q,b,expected_sha=SHA)["review_queue_valid"])
    def test_bad_sha_fails_closed(self):
        q,b=fixtures();b["candidate_sha"]="f"*40
        self.assertFalse(assess(q,b,expected_sha=SHA)["review_queue_valid"])
    def test_weekly_four_products_not_inferred_from_roster(self):
        q,b=fixtures();out=assess(q,b,expected_sha=SHA,weekly={"four_products":True})
        self.assertFalse(out["weekly_full_product_verified"])
if __name__=="__main__":unittest.main()
