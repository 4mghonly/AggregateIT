import unittest
from datetime import datetime, timezone, timedelta
from v2_b125_evidence_reconciliation import reconcile

SHA = "b67a9e4115f4f88049716d608e54a6d06ef5f15f"
def pair(day, run):
    return {"utc_date":day,"github_run_id":str(run),"head_sha":SHA,"input_manifest_sha256":"a"*64,"observed_at":day+"T07:01:00Z","observed_at":day+"T07:01:00Z",
            "products":{"english":{"operational_v2_selected":6},"arabic":{"operational_v2_selected":6}}}
def roster(day,run):
    return {"utc_date":day,"github_run_id":str(run),"head_sha":SHA,"capture_sha256":"a"*64,"observed_at":day+"T07:01:00Z","observed_at":day+"T07:01:00Z",
            "products":{"english":{"story_count":6,"stories":[{}]*6},"arabic":{"story_count":6,"stories":[{}]*6}}}
def meta(day,run):
    return {"id":run,"head_sha":SHA,"head_branch":"rebuild/aggregateit-v2",
            "status":"completed","conclusion":"success","event":"workflow_dispatch",
            "path":".github/workflows/v2-b80-b83-live-acceptance.yml",
            "run_started_at":day+"T07:00:00Z"}
class EvidenceReconciliationTests(unittest.TestCase):
    def setUp(self):
        from datetime import date,timedelta
        self.days=[(date(2026,11,6)+timedelta(days=i)).isoformat() for i in range(7)]
        self.pairs=[pair(d,i+10000000) for i,d in enumerate(self.days)]
        self.rosters=[roster(d,i+10000000) for i,d in enumerate(self.days)]
        self.runs=[meta(d,i+10000000) for i,d in enumerate(self.days)]
    def assess(self):
        return reconcile(self.pairs,self.rosters,self.runs,expected_sha=SHA)
    def test_seven_independently_matched_dates(self):
        result=self.assess()
        self.assertTrue(result["seven_verified"])
        self.assertEqual(result["verified_dates"],self.days)
        self.assertFalse(result["can_release"])
        self.assertFalse(result["model_parity_verified"])
    def test_missing_roster_fails_closed(self):
        self.rosters.pop()
        self.assertFalse(self.assess()["seven_verified"])
    def test_wrong_capture_hash_fails_closed(self):
        self.rosters[2]["capture_sha256"]="b"*64
        self.assertFalse(self.assess()["seven_verified"])
    def test_wrong_sha_fails_closed(self):
        self.pairs[3]["head_sha"]="c"*40
        self.assertFalse(self.assess()["seven_verified"])
    def test_duplicate_date_fails_closed(self):
        self.pairs.append(dict(self.pairs[0]))
        self.assertFalse(self.assess()["seven_verified"])
    def test_no_actual_arabic_fails_closed(self):
        self.pairs[0]["products"]["arabic"]["operational_v2_selected"]=0
        self.assertFalse(self.assess()["seven_verified"])
    def test_unverified_run_fails_closed(self):
        self.runs[0]["conclusion"]="failure"
        self.assertFalse(self.assess()["seven_verified"])
    def test_fake_capture_date_metadata_is_not_accepted(self):
        self.runs[0]["run_started_at"]="2026-11-05T07:00:00Z"
        self.assertFalse(self.assess()["seven_verified"])
    def test_wrong_workflow_fails_closed(self):
        self.runs[0]["path"]="other.yml"
        self.assertFalse(self.assess()["seven_verified"])
    def test_missing_run_start_fails_closed(self):
        del self.runs[0]["run_started_at"]
        self.assertFalse(self.assess()["seven_verified"])
    def test_nonconsecutive_dates_fails_closed(self):
        self.pairs[6]["utc_date"]="2026-11-14"
        self.rosters[6]["utc_date"]="2026-11-14"
        self.runs[6]["run_started_at"]="2026-11-14T07:00:00Z"
        self.assertFalse(self.assess()["seven_verified"])
if __name__=="__main__":
    unittest.main()
