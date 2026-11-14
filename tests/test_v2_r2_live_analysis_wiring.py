import inspect
import unittest
from v2_b46_live_editorial import compile_captured_articles
class LiveAnalysisWiring(unittest.TestCase):
 def test_explicit_analysis_provider_hook_exists(self):
  self.assertIn("analysis_provider",inspect.signature(compile_captured_articles).parameters)
 def test_provider_must_be_callable(self):
  with self.assertRaisesRegex(ValueError,"invalid_analysis_provider"):
   compile_captured_articles([],as_of="2026-11-14T08:00:00+00:00",slot_id="2026-11-14T08:00:00+00:00",analysis_provider="not_callable")
 def test_provider_never_grants_publication_authority(self):
  result=compile_captured_articles([],as_of="2026-11-14T08:00:00+00:00",slot_id="2026-11-14T08:00:00+00:00",analysis_provider=lambda **kw:[])
  self.assertFalse(result["can_send"])
if __name__=="__main__":unittest.main()
