import json,tempfile,unittest
from pathlib import Path
from v2_recovery_backfill import backfill

class BackfillTests(unittest.TestCase):
 def test_two_languages_seven_days_from_archives(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);archives=[]
   for day in range(1,8):
    for product,quote in (("english","Security update"),("arabic","تطورات أمنية")):
     plan={"schema":"aggregateit-editorial-plan/1","product":product,"as_of":f"2026-11-{day:02d}T12:00:00+00:00",
       "items":[{"event_id":"evt_"+product,"region":"iran","priority":90,"topic":"security","evidence":{"quote":quote+str(day),"source_url":"https://example.org/story"}}]}
     p=root/f"{product}-{day}.json";p.write_text(json.dumps(plan));archives.append(p)
   r=backfill(archives,root/"history.db",root/"out")
   self.assertTrue(r["english"]["complete_week"])
   self.assertTrue(r["arabic"]["complete_week"])
   self.assertEqual(r["arabic"]["days_observed"],7)
 def test_missing_days_not_faked(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/"plan.json"
   p.write_text(json.dumps({"schema":"aggregateit-editorial-plan/1","product":"english","as_of":"2026-11-07T12:00:00+00:00","items":[]}))
   r=backfill([p],root/"db",root/"out")
   self.assertFalse(r["english"]["complete_week"])
if __name__=="__main__":unittest.main()
