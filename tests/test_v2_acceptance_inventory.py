import unittest
from v2_acceptance_inventory import assess,EVIDENCE_SCHEMA
from v2_b62_precanary import RELEASE_ITEMS
class AcceptanceInventoryTests(unittest.TestCase):
    def test_missing_all_nine_gates_hold(self):
        result=assess({"schema":EVIDENCE_SCHEMA,"checks":{}})
        self.assertEqual(len(result["missing_or_incomplete"]),len(RELEASE_ITEMS))
        self.assertEqual(result["release_status"],"HOLD")
        self.assertFalse(result["can_release"])
    def test_boolean_claim_does_not_count(self):
        result=assess({"schema":EVIDENCE_SCHEMA,"checks":{RELEASE_ITEMS[0]:True}})
        self.assertFalse(result["receipts_structurally_present"][RELEASE_ITEMS[0]])
    def test_even_complete_receipts_cannot_self_authorize(self):
        item={"artifact_url":"https://github.com/example/a","sha256":"a"*64,
              "reviewed_at":"2026-10-28T17:00:00Z","independent_verification":True,"result":"pass"}
        result=assess({"schema":EVIDENCE_SCHEMA,"checks":{k:item for k in RELEASE_ITEMS}})
        self.assertEqual(result["missing_or_incomplete"],[])
        self.assertFalse(result["independent_evidence_authenticated"])
        self.assertFalse(result["can_release"])
    def test_invalid_checks_rejected(self):
        with self.assertRaises(ValueError):
            assess({"schema":EVIDENCE_SCHEMA,"checks":[]})
if __name__=="__main__":unittest.main()
