import unittest
from v2_product_compiler import compile_daily

SLOT="2026-11-14T08:00:00+00:00"
def plan():
 return {"schema":"aggregateit-editorial-plan/1","delivery_authorized":False,"product":"english","language":"en","slot_id":SLOT,"items":[{"event_id":"evt_1","region":"iran","topic":"geopolitics","change":"new","reporting_status":"publisher_attributed_not_independently_verified","evidence":{"excerpt_id":"ex_1","source_id":"src_1","quote":"A verified original quotation","source_url":"https://example.com/1","original_language":"en"}}]}
class AnalysisContractTests(unittest.TestCase):
 def test_evidence_bound_assessment_is_preserved_without_authorizing_delivery(self):
  p=compile_daily(editorial_plan=plan(),analysis_candidates=[{"event_id":"evt_1","assessment":"This may alter regional diplomacy.","evidence_excerpt_ids":["ex_1"],"confidence":"low"}])
  self.assertEqual(p["stories"][0]["assessment"],"This may alter regional diplomacy.")
  self.assertEqual(p["stories"][0]["analysis_status"],"evidence_referenced_unverified")
  self.assertFalse(p["delivery_authorized"])
  self.assertFalse(p["content_truth_verified"])
 def test_rejects_unknown_evidence(self):
  with self.assertRaisesRegex(ValueError,"analysis_evidence_not_in_edition"):
   compile_daily(editorial_plan=plan(),analysis_candidates=[{"event_id":"evt_1","assessment":"Unsupported","evidence_excerpt_ids":["ex_other"],"confidence":"high"}])
 def test_rejects_unknown_event(self):
  with self.assertRaisesRegex(ValueError,"analysis_event_not_in_edition"):
   compile_daily(editorial_plan=plan(),analysis_candidates=[{"event_id":"evt_other","assessment":"Unsupported","evidence_excerpt_ids":["ex_1"],"confidence":"low"}])
 def test_rejects_empty_or_overconfident_claims(self):
  for assessment,confidence in [("", "low"),("Statement","certain")]:
   with self.subTest(assessment=assessment,confidence=confidence):
    with self.assertRaises(ValueError):
     compile_daily(editorial_plan=plan(),analysis_candidates=[{"event_id":"evt_1","assessment":assessment,"evidence_excerpt_ids":["ex_1"],"confidence":confidence}])
 def test_missing_analysis_abstains(self):
  p=compile_daily(editorial_plan=plan())
  self.assertIsNone(p["stories"][0]["assessment"])
  self.assertEqual(p["stories"][0]["analysis_status"],"abstained")
if __name__=="__main__":unittest.main()
