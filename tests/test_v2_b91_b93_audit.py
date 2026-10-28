import unittest
from v2_b91_b93_audit import audit
class B91B93Tests(unittest.TestCase):
 def setUp(self):
  self.row={"schema":"aggregateit-v2-b88-b90-acceptance/1","can_release":False,"observed_date":"2026-10-28","b89_source_coverage":{"english":{"represented_regions":["gcc"]},"arabic":{"represented_regions":["gcc","egypt"]}}}
 def test_one_day_cannot_satisfy_week(self):
  r=audit(self.row,[self.row,self.row])
  self.assertEqual(r["b92"]["distinct_observed_days"],1)
  self.assertFalse(r["b92"]["seven_day_evidence_met"])
  self.assertFalse(r["can_release"])
 def test_seven_distinct_days_only(self):
  from datetime import date,timedelta
  history=[dict(self.row,observed_date=(date(2026,10,1)+timedelta(days=i)).isoformat()) for i in range(7)]
  r=audit(self.row,history)
  self.assertTrue(r["b92"]["seven_day_evidence_met"])
  self.assertFalse(r["can_release"])
 def test_untrusted_history_rejected(self):
  with self.assertRaises(ValueError):audit(self.row,[{"can_release":True}])
if __name__=="__main__":unittest.main()
