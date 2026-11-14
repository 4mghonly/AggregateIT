import inspect
import unittest
from v2_b46_live_editorial import compile_captured_articles
class ProviderFailureDiagnostics(unittest.TestCase):
 def test_explicit_diagnostic_field_is_present(self):
  r=compile_captured_articles([],as_of="2026-11-14T08:00:00+00:00",slot_id="2026-11-14T08:00:00+00:00")
  self.assertIn("analysis_provider_status",r)
  self.assertEqual(r["analysis_provider_status"],{"english":"not_configured","arabic":"not_configured"})
 def test_configured_but_no_stories_is_not_success(self):
  r=compile_captured_articles([],as_of="2026-11-14T08:00:00+00:00",slot_id="2026-11-14T08:00:00+00:00",analysis_provider=lambda **kw:[])
  self.assertEqual(r["analysis_provider_status"],{"english":"no_eligible_stories","arabic":"no_eligible_stories"})
if __name__=="__main__":unittest.main()
