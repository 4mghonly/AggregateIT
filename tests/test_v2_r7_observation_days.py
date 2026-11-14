import unittest
from datetime import datetime,timedelta,timezone
from v2_weekly_rollup import rollup_week
class ObservationDays(unittest.TestCase):
 def test_empty_plans_do_not_count_as_observed_days(self):
  now=datetime(2026,11,14,12,tzinfo=timezone.utc)
  plans=[]
  for i in range(7):
   date=(now-timedelta(days=i)).isoformat()
   plans.append({"schema":"aggregateit-editorial-plan/1","product":"english","delivery_authorized":False,"as_of":date,"items":[]})
  result=rollup_week(plans,product="english",as_of=now.isoformat())
  self.assertEqual(result["days_with_snapshots"],0)
  self.assertFalse(result["complete_seven_day_history"])
 def test_one_real_day_and_six_empty_days_is_incomplete(self):
  now=datetime(2026,11,14,12,tzinfo=timezone.utc)
  plans=[]
  for i in range(7):
   date=(now-timedelta(days=i)).isoformat()
   items=([{"event_id":"event-1","version_id":"version-1","region":"gcc","priority":1,"evidence":{"source_id":"src","excerpt_id":"ex","source_url":"https://example.org/1","quote":"Publisher text","original_language":"en"}}] if i==0 else [])
   plans.append({"schema":"aggregateit-editorial-plan/1","product":"english","delivery_authorized":False,"as_of":date,"items":items})
  result=rollup_week(plans,product="english",as_of=now.isoformat())
  self.assertEqual(result["days_with_snapshots"],1)
  self.assertFalse(result["complete_seven_day_history"])
if __name__=="__main__":unittest.main()
