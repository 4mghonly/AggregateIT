import inspect
import unittest
from v2_b47_four_product_held import compose_held_products
class WeeklyHistoryContract(unittest.TestCase):
 def test_optional_verified_history_parameter(self):
  self.assertIn("weekly_history",inspect.signature(compose_held_products).parameters)
 def test_history_requires_two_product_mapping(self):
  with self.assertRaisesRegex(ValueError,"invalid_weekly_history"):
   compose_held_products({},output_dir="/tmp",as_of="2026-11-14T12:00:00+00:00",weekly_history=[])
 def test_history_lists_must_be_bounded(self):
  with self.assertRaisesRegex(ValueError,"invalid_weekly_history"):
   compose_held_products({},output_dir="/tmp",as_of="2026-11-14T12:00:00+00:00",weekly_history={"english":[{}]*61,"arabic":[]})
if __name__=="__main__":unittest.main()
