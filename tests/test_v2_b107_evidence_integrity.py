import unittest
from datetime import date,timedelta
from v2_b101_b106_parity_gates import assess,AREAS
TODAY=date(2026,10,29)
def row(day,product="arabic",value="same"):
 return {"date":day.isoformat(),"product":product,"input_sha256":"a"*64,
         "v1":{a:[value] for a in AREAS},"v2":{a:[value] for a in AREAS},
         "evidence":{k:True for k in ("v1_executed","v2_executed","same_input_verified","model_fallback_exercised","historical_baseline_authenticated","visual_reviewed","source_provenance_verified")}}
class EvidenceIntegrityTests(unittest.TestCase):
 def test_duplicate_identity_must_not_be_lost(self):
  r=row(TODAY)
  r["v1"]["event_clustering"]=["event-1","event-1"]
  r["v2"]["event_clustering"]=["event-1"]
  x=assess([r],as_of=TODAY.isoformat())
  self.assertEqual(x["results"][0]["dimensions"]["event_clustering"]["status"],"DIFFERENT")
 def test_invalid_digest_format_rejected(self):
  r=row(TODAY);r["input_sha256"]="z"*64
  with self.assertRaises(ValueError):assess([r],as_of=TODAY.isoformat())
 def test_blank_identifiers_rejected(self):
  r=row(TODAY);r["v1"]["arabic_filter"]=[""]
  with self.assertRaises(ValueError):assess([r],as_of=TODAY.isoformat())
 def test_complete_synthetic_window_cannot_authorize_release(self):
  rows=[row(TODAY-timedelta(days=i),p) for i in range(7) for p in ("arabic","english")]
  x=assess(rows,as_of=TODAY.isoformat())
  self.assertFalse(x["can_release"])
  self.assertFalse(x["production_cutover_authorized"])
if __name__=="__main__":unittest.main()
