import ast
import unittest
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[1]/"v2_b47_four_product_held.py"
class WeeklyHistoryContract(unittest.TestCase):
 def test_optional_verified_history_parameter(self):
  tree=ast.parse(SOURCE.read_text())
  fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="compose_held_products")
  self.assertIn("weekly_history",[x.arg for x in fn.args.kwonlyargs])
 def test_history_validation_is_explicit(self):
  source=SOURCE.read_text()
  self.assertIn("raise ValueError('invalid_weekly_history')",source)
  self.assertIn("len(weekly_history[p])>59",source)
 def test_history_flows_into_source_bound_rollup(self):
  source=SOURCE.read_text()
  self.assertIn("rollup_week([*history,plan]",source)
  self.assertIn("report['days_with_snapshots']==7",source)
if __name__=="__main__":unittest.main()
