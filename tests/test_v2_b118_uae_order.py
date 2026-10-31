import unittest
from v2_b118_layout_gate import prioritize_uae
class UaeOrder(unittest.TestCase):
 def test_uae_moves_first_without_dropping_others(self):
  rows=[{"subject_country":"YE","event_id":"y"},{"subject_country":"AE","event_id":"u"},{"subject_country":"IR","event_id":"i"}]
  out=prioritize_uae(rows)
  self.assertEqual([x["event_id"] for x in out],["u","y","i"])
  self.assertEqual(rows[0]["event_id"],"y")
 def test_no_uae_preserves_order(self):
  rows=[{"subject_country":"YE"},{"subject_country":"IR"}]
  self.assertEqual(prioritize_uae(rows),rows)
if __name__=="__main__":unittest.main()
