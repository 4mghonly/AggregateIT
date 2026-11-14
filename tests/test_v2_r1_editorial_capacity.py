import inspect
import unittest
from v2_b46_live_editorial import compile_captured_articles

class EditorialCapacityContract(unittest.TestCase):
    def test_capacity_is_configurable_without_enabling_publication(self):
        self.assertIn("editorial_max_items",inspect.signature(compile_captured_articles).parameters)
    def test_invalid_capacity_rejected_before_capture_processing(self):
        with self.assertRaisesRegex(ValueError,"invalid_editorial_capacity"):
            compile_captured_articles([],as_of="2026-11-14T08:00:00+00:00",
                slot_id="2026-11-14T08:00:00+00:00",editorial_max_items=0)
    def test_default_remains_bounded(self):
        self.assertEqual(inspect.signature(compile_captured_articles).parameters["editorial_max_items"].default,6)
if __name__=="__main__":unittest.main()
