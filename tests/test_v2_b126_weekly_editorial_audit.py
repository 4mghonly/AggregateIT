import unittest
from v2_b126_weekly_editorial_audit import audit
SHA="b67a9e4115f4f88049716d608e54a6d06ef5f15f"
def receipt(day,run,eng=(6,7,6,0,1),ara=(6,10,4,2,6)):
    return {"utc_date":day,"github_run_id":str(run),"head_sha":SHA,
            "products":{p:dict(zip(("operational_v2_selected","v1_selected","both_selected","v2_only","v1_only"),v))
                        for p,v in (("english",eng),("arabic",ara))}}
class B126Tests(unittest.TestCase):
    def setUp(self):
        self.rows=[receipt("2026-11-%02d"%d,10000000+d) for d in range(6,13)]
        self.b125={"schema":"aggregateit-v2-b125-independent-reconciliation/1","candidate_sha":SHA,
                   "seven_verified":True,"verified_dates":[r["utc_date"] for r in self.rows],
                   "issues":[],"can_release":False}
    def test_full_window_reports_differences_without_claiming_model_parity(self):
        a=audit(self.rows,self.b125,expected_sha=SHA)
        self.assertTrue(a["source_roster_seven_days"])
        self.assertEqual(a["products"]["arabic"]["v1_only"],42)
        self.assertEqual(a["products"]["arabic"]["v2_only"],14)
        self.assertFalse(a["full_model_parity"])
        self.assertFalse(a["weekly_full_product_verified"])
        self.assertFalse(a["can_release"])
    def test_missing_day_fails(self):
        self.assertFalse(audit(self.rows[:-1],self.b125,expected_sha=SHA)["source_roster_seven_days"])
    def test_unverified_b125_fails(self):
        self.b125["seven_verified"]=False
        self.assertFalse(audit(self.rows,self.b125,expected_sha=SHA)["source_roster_seven_days"])
    def test_invalid_selection_arithmetic_fails(self):
        self.rows[0]["products"]["arabic"]["v2_only"]=99
        self.assertFalse(audit(self.rows,self.b125,expected_sha=SHA)["source_roster_seven_days"])
    def test_wrong_sha_fails(self):
        self.rows[0]["head_sha"]="c"*40
        self.assertFalse(audit(self.rows,self.b125,expected_sha=SHA)["source_roster_seven_days"])
    def test_duplicate_date_fails(self):
        self.rows.append(dict(self.rows[0]))
        self.assertFalse(audit(self.rows,self.b125,expected_sha=SHA)["source_roster_seven_days"])
if __name__=="__main__":unittest.main()
