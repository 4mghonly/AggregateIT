import unittest
from v2_b128_hybrid_closure import evaluate
SHA="b67a9e4115f4f88049716d608e54a6d06ef5f15f"
def fixture():
 rows=[{"utc_date":"2026-11-06","product":"arabic","identity_sha256":"a"*64,"source_url":"https://example.org/a","decision":"v1_only","v2_rejection_reason":"no_grounded_region","materiality":"UNASSESSED","analyst_reviewed":False,"publisher_rights":"UNVERIFIED"}]
 queue={"schema":"aggregateit-v2-b127-identity-matched-review/1","candidate_sha":SHA,"evidence_reconciled":True,"disagreement_count":1,"rows":rows,"issues":[],"can_release":False}
 b126={"schema":"aggregateit-v2-b126-weekly-editorial-audit/1","candidate_sha":SHA,"source_roster_seven_days":True,"verified_dates":["2026-11-%02d"%i for i in range(6,13)],"issues":[],"can_release":False}
 four={"schema":"aggregateit-v2-b47-four-product-held/1","real_7_day_reporting_verified":False,"weekly":{p:{"schema":"aggregateit-v2-weekly-rollup/1","days_with_real_daily_snapshots":1,"required_full_week_days":7,"complete_seven_day_history":False,"pdf_rendered":True,"can_release":False} for p in ("english","arabic")}}
 return queue,b126,four
class HybridTests(unittest.TestCase):
 def test_realistic_missing_evidence_is_explicit(self):
  q,b,f=fixture();x=evaluate(q,b,f,[],expected_sha=SHA)
  self.assertEqual(x["adjudication"]["pending"],1)
  self.assertEqual(x["adjudication"]["accepted"],0)
  self.assertEqual(x["weekly"]["missing_snapshot_days"]["english"],6)
  self.assertFalse(x["weekly"]["verified"])
  self.assertFalse(x["can_release"])
  self.assertEqual(len(x["review_packet"]),1)
 def test_self_asserted_llm_verdict_not_independent(self):
  q,b,f=fixture();verdict=[{"utc_date":"2026-11-06","product":"arabic","identity_sha256":"a"*64,"disposition":"correct_v1","reviewer_id":"model-a","reviewer_type":"llm","evidence_refs":["https://example.org/a"],"rationale":"test"}]
  x=evaluate(q,b,f,verdict,expected_sha=SHA)
  self.assertEqual(x["adjudication"]["accepted"],0)
  self.assertEqual(x["adjudication"]["pending"],1)
 def test_unknown_identity_rejected(self):
  q,b,f=fixture();v=[{"utc_date":"2026-11-06","product":"arabic","identity_sha256":"b"*64,"disposition":"correct_v1"}]
  self.assertIn("unmatched_verdict",evaluate(q,b,f,v,expected_sha=SHA)["issues"])
 def test_fake_full_week_flag_rejected(self):
  q,b,f=fixture();f["real_7_day_reporting_verified"]=True
  self.assertFalse(evaluate(q,b,f,[],expected_sha=SHA)["weekly"]["verified"])
 def test_complete_week_requires_independent_product_evidence(self):
  q,b,f=fixture()
  for p in ("english","arabic"):
   f["weekly"][p]["days_with_real_daily_snapshots"]=7
   f["weekly"][p]["complete_seven_day_history"]=True
  f["real_7_day_reporting_verified"]=True
  self.assertFalse(evaluate(q,b,f,[],expected_sha=SHA)["weekly"]["verified"])
 def test_duplicate_verdict_rejected(self):
  q,b,f=fixture();v={"utc_date":"2026-11-06","product":"arabic","identity_sha256":"a"*64,"disposition":"correct_v1"}
  self.assertIn("duplicate_verdict",evaluate(q,b,f,[v,v],expected_sha=SHA)["issues"])
if __name__=="__main__":unittest.main()
