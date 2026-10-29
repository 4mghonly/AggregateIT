import unittest
from datetime import date,timedelta
from v2_b101_b106_parity_gates import assess,AREAS
TODAY=date(2026,10,29)
def row(day,product="arabic",value="same"):
 return {"date":day.isoformat(),"product":product,"input_sha256":"a"*64,
         "v1":{a:[value] for a in AREAS},"v2":{a:[value] for a in AREAS},
         "evidence":{k:True for k in ("v1_executed","v2_executed","same_input_verified","model_fallback_exercised","historical_baseline_authenticated","visual_reviewed","source_provenance_verified")}}
class B101B106Tests(unittest.TestCase):
 def test_empty_holds(self):
  x=assess([],as_of=TODAY.isoformat())
  self.assertFalse(x["same_input_seven_date_evidence_complete"])
  self.assertFalse(x["can_release"])
 def test_single_day_never_satisfies_seven(self):
  x=assess([row(TODAY)],as_of=TODAY.isoformat())
  self.assertEqual(x["received_rows"],1)
  self.assertFalse(x["all_dimensions_matched"])
 def test_complete_window_still_needs_owner_review(self):
  rows=[row(TODAY-timedelta(days=i),p) for i in range(7) for p in ("english","arabic")]
  x=assess(rows,as_of=TODAY.isoformat())
  self.assertTrue(x["same_input_seven_date_evidence_complete"])
  self.assertTrue(x["all_dimensions_matched"])
  self.assertFalse(x["production_cutover_authorized"])
 def test_missing_model_failover_holds(self):
  rows=[row(TODAY-timedelta(days=i),p) for i in range(7) for p in ("english","arabic")]
  rows[0]["evidence"]["model_fallback_exercised"]=False
  x=assess(rows,as_of=TODAY.isoformat())
  self.assertFalse(x["all_dimensions_matched"])
  self.assertEqual(x["results"][0]["dimensions"]["translation_fallback"]["status"],"UNVERIFIED")
 def test_missing_v1_execution_cannot_claim_parity(self):
  r=row(TODAY);r["evidence"]["v1_executed"]=False
  x=assess([r],as_of=TODAY.isoformat())
  self.assertEqual(x["results"][0]["dimensions"]["arabic_filter"]["status"],"UNVERIFIED")
 def test_changed_event_reports_disagreement(self):
  r=row(TODAY);r["v2"]["event_clustering"]=["different"]
  x=assess([r],as_of=TODAY.isoformat())
  self.assertEqual(x["results"][0]["dimensions"]["event_clustering"]["v1_only"],1)
 def test_duplicate_day_refused(self):
  with self.assertRaisesRegex(ValueError,"duplicate_date_product"):
   assess([row(TODAY),row(TODAY)],as_of=TODAY.isoformat())
 def test_future_date_refused(self):
  with self.assertRaisesRegex(ValueError,"outside_seven_day_window"):
   assess([row(TODAY+timedelta(days=1))],as_of=TODAY.isoformat())
if __name__=="__main__":unittest.main()
