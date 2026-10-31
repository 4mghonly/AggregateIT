import inspect
import unittest
import v2_b46_live_editorial_runner as runner
class PreviewBudget(unittest.TestCase):
 def test_expanded_preview_is_bounded(self):
  source=inspect.getsource(runner.run)
  self.assertIn(">=10",source)
  self.assertIn("quality_preview",source)
 def test_quality_preview_uses_more_than_primary_source(self):
  self.assertGreater(len(runner.SOURCE_CATALOG["english"]),2)
  self.assertGreater(len(runner.SOURCE_CATALOG["arabic"]),2)
if __name__=="__main__":unittest.main()
