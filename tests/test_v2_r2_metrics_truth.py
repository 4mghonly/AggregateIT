import unittest
from v2_b46_live_editorial import compile_captured_articles,metrics_only
class MetricsTruth(unittest.TestCase):
 def test_no_capture_reports_no_model_call(self):
  r=compile_captured_articles([],as_of="2026-11-14T08:00:00+00:00",slot_id="2026-11-14T08:00:00+00:00")
  m=metrics_only(r)
  self.assertEqual(m["analysis_provider_status"],{"english":"not_configured","arabic":"not_configured"})
  self.assertEqual(m["model_call_status"],"not_configured")
  self.assertFalse(m["model_called"])
 def test_provider_with_no_stories_does_not_claim_model_call(self):
  r=compile_captured_articles([],as_of="2026-11-14T08:00:00+00:00",slot_id="2026-11-14T08:00:00+00:00",analysis_provider=lambda **kw:[])
  m=metrics_only(r)
  self.assertEqual(m["model_call_status"],"no_eligible_stories")
  self.assertFalse(m["model_called"])
if __name__=="__main__":unittest.main()
