import unittest,tempfile
from pathlib import Path
from datetime import datetime,timezone
from v2_b94_daily_evidence import record
class B94Tests(unittest.TestCase):
 def setUp(self):
  self.a={"schema":"aggregateit-v2-b88-b90-acceptance/1","can_release":False,"b89_source_coverage":{x:{"selected_stories":3} for x in ("english","arabic")}}
 def test_same_day_does_not_inflate(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"evidence.sqlite";t=datetime.now(timezone.utc).isoformat()
   record(p,self.a,observed_at=t);r=record(p,self.a,observed_at=t)
   self.assertEqual(r["distinct_days_with_stories"],{"english":1,"arabic":1})
   self.assertFalse(r["seven_day_evidence_met"])
 def test_reject_naive_and_release(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):record(Path(d)/"x.sqlite",self.a,observed_at="2026-10-28T10:00:00")
   with self.assertRaises(ValueError):record(Path(d)/"x.sqlite",dict(self.a,can_release=True),observed_at=datetime.now(timezone.utc).isoformat())
if __name__=="__main__":unittest.main()
