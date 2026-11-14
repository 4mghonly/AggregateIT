import inspect
import unittest
from v2_b46_live_editorial_runner import run
class RunnerCapacityTests(unittest.TestCase):
 def test_runner_exposes_editorial_capacity(self):
  self.assertIn("editorial_max_items",inspect.signature(run).parameters)
 def test_invalid_capacity_fails_before_network(self):
  with self.assertRaisesRegex(ValueError,"invalid_editorial_capacity"):
   run(editorial_max_items=0)
if __name__=="__main__":unittest.main()
