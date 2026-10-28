import json,tempfile,unittest
from pathlib import Path
from datetime import date,timedelta
from v2_b95_b97_history import consolidate,make_daily
class HistoryTests(unittest.TestCase):
 def setUp(self):
  self.a={"schema":"aggregateit-v2-b88-b90-acceptance/1","can_release":False,"b89_source_coverage":{x:{"selected_stories":3} for x in ("english","arabic")}}
 def test_seven_genuine_distinct_days(self):
  today=date.today()
  with tempfile.TemporaryDirectory() as d:
   for i in range(7):
    day=(today-timedelta(days=i)).isoformat()
    Path(d,day+".json").write_text(json.dumps(make_daily(self.a,day=day)))
   r=consolidate(Path(d),today=today)
   self.assertTrue(r["seven_day_evidence_met"])
   self.assertFalse(r["can_release"])
 def test_one_day_not_week(self):
  with tempfile.TemporaryDirectory() as d:
   day=date.today().isoformat()
   Path(d,"a.json").write_text(json.dumps(make_daily(self.a,day=day)))
   Path(d,"b.json").write_text(json.dumps(make_daily(self.a,day=day)))
   self.assertEqual(consolidate(Path(d),today=date.today())["last_seven_days"]["arabic"],1)
 def test_conflicting_duplicate_fails(self):
  with tempfile.TemporaryDirectory() as d:
   day=date.today().isoformat();r=make_daily(self.a,day=day)
   Path(d,"a.json").write_text(json.dumps(r))
   r["stories"]["arabic"]=0
   Path(d,"b.json").write_text(json.dumps(r))
   with self.assertRaises(ValueError):consolidate(Path(d),today=date.today())
if __name__=="__main__":unittest.main()
