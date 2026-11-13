import unittest
from hashlib import sha256
from v2_b127_identity_review import build_queue

SHA="b67a9e4115f4f88049716d608e54a6d06ef5f15f"
URL="https://example.org/story"
HASH=sha256(URL.encode()).hexdigest()
def fixture():
    dates=["2026-11-%02d"%d for d in range(6,13)]
    b126={"schema":"aggregateit-v2-b126-weekly-editorial-audit/1","candidate_sha":SHA,
          "source_roster_seven_days":True,"verified_dates":dates,"issues":[],"can_release":False,
          "products":{"english":{"v1_only":0,"v2_only":7},"arabic":{"v1_only":7,"v2_only":0}}}
    reviews=[]
    rosters=[]
    for i,day in enumerate(dates):
        run=str(42178164780+i)
        url=URL+"/"+str(i)
        identity=sha256(url.encode()).hexdigest()
        reviews.append({"schema":"aggregateit-v2-b124-editorial-disagreement-review/1",
          "observed_at":day+"T07:01:00+00:00","can_release":False,
          "rows":[{"product":"english","source_url":url,"identity_sha256":identity,
                   "v1_selected":False,"v2_selected":True,"v2_decision_stage":"selected",
                   "v2_rejection_reason":None,"analyst_reviewed":False,"materiality":"UNASSESSED",
                   "publisher_rights":"UNVERIFIED"},
                  {"product":"arabic","source_url":url+"/ar","identity_sha256":sha256((url+"/ar").encode()).hexdigest(),
                   "v1_selected":True,"v2_selected":False,"v2_decision_stage":"rejected_body_or_evidence",
                   "v2_rejection_reason":"article_body_container_missing",
                   "analyst_reviewed":False,"materiality":"UNASSESSED","publisher_rights":"UNVERIFIED"}]})
        rosters.append({"utc_date":day,"github_run_id":run,"head_sha":SHA,
                        "products":{"english":{"stories":[{"source_url":url,"identity_sha256":identity}]},
                                    "arabic":{"stories":[]}}})
    return reviews,rosters,b126
class B127Tests(unittest.TestCase):
    def test_matching_real_identity_and_counts(self):
        r,s,b=fixture();out=build_queue(r,s,b,expected_sha=SHA)
        self.assertTrue(out["evidence_reconciled"])
        self.assertEqual(out["disagreement_count"],14)
        self.assertEqual(out["review_status"],"PENDING_INDEPENDENT_REVIEW")
        self.assertFalse(out["can_release"])
        self.assertEqual({row["decision"] for row in out["rows"]},{"v1_only","v2_only"})
        self.assertNotIn("headline",out["rows"][0])
    def test_hash_mismatch_fails(self):
        r,s,b=fixture();r[0]["rows"][0]["identity_sha256"]="a"*64
        self.assertFalse(build_queue(r,s,b,expected_sha=SHA)["evidence_reconciled"])
    def test_missing_v2_roster_identity_fails(self):
        r,s,b=fixture();s[0]["products"]["english"]["stories"]=[]
        self.assertFalse(build_queue(r,s,b,expected_sha=SHA)["evidence_reconciled"])
    def test_duplicate_identity_fails(self):
        r,s,b=fixture();r[0]["rows"].append(dict(r[0]["rows"][0]))
        self.assertFalse(build_queue(r,s,b,expected_sha=SHA)["evidence_reconciled"])
    def test_aggregate_mismatch_fails(self):
        r,s,b=fixture();b["products"]["arabic"]["v1_only"]=99
        self.assertFalse(build_queue(r,s,b,expected_sha=SHA)["evidence_reconciled"])
    def test_unverified_b126_fails(self):
        r,s,b=fixture();b["source_roster_seven_days"]=False
        self.assertFalse(build_queue(r,s,b,expected_sha=SHA)["evidence_reconciled"])
    def test_unreviewed_cannot_become_adjudicated(self):
        r,s,b=fixture();r[0]["rows"][0]["analyst_reviewed"]=True
        self.assertFalse(build_queue(r,s,b,expected_sha=SHA)["independent_adjudication_verified"])
    def test_v1_only_must_not_be_in_v2_roster(self):
        r,s,b=fixture();row=r[0]["rows"][1]
        s[0]["products"]["arabic"]["stories"]=[{"source_url":row["source_url"],"identity_sha256":row["identity_sha256"]}]
        self.assertFalse(build_queue(r,s,b,expected_sha=SHA)["evidence_reconciled"])
    def test_date_mismatch_fails(self):
        r,s,b=fixture();r[0]["observed_at"]="2026-11-05T07:01:00+00:00"
        self.assertFalse(build_queue(r,s,b,expected_sha=SHA)["evidence_reconciled"])
if __name__=="__main__":unittest.main()
