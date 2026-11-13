import tempfile,unittest
from pathlib import Path
from v2_product_recovery import ProductHistory, build_weekly_intelligence, compact_sections

class RecoveryTests(unittest.TestCase):
 def test_seven_day_history_and_change(self):
  with tempfile.TemporaryDirectory() as d:
   h=ProductHistory(Path(d)/"history.sqlite")
   for day in range(1,8):
    h.record("ar",f"2026-11-{day:02d}",[{"event_id":"iran-1","headline":"تطور عسكري","region":"iran","summary":f"تطور {day}","source_url":"https://example.org/iran","priority":90}])
   result=build_weekly_intelligence(h,"ar","2026-11-07")
   self.assertEqual(result["days_observed"],7)
   self.assertEqual(result["events"][0]["observation_days"],7)
   self.assertEqual(result["events"][0]["change_count"],6)
   self.assertEqual(len(result["events"][0]["timeline"]),7)
   h.close()
 def test_rejects_irrelevant_and_duplicate(self):
  with tempfile.TemporaryDirectory() as d:
   h=ProductHistory(Path(d)/"h.db")
   rows=[{"event_id":"a","headline":"A","region":"iran","summary":"Security","source_url":"https://example.org/a","priority":85,"topic":"security"},{"event_id":"a","headline":"A","region":"iran","summary":"Security","source_url":"https://example.org/a","priority":85,"topic":"security"},{"event_id":"museum","headline":"Museum","region":"turkey","summary":"Opening","source_url":"https://example.org/b","priority":12,"topic":"culture"}]
   h.record("en","2026-11-01",rows)
   self.assertEqual(len(build_weekly_intelligence(h,"en","2026-11-01")["events"]),1)
   h.close()
 def test_no_empty_panels(self):
  self.assertEqual(compact_sections({"critical":[],"maritime":[],"developments":[{"title":"A"}]}),{"developments":[{"title":"A"}]})
 def test_rejects_bad_sources(self):
  with tempfile.TemporaryDirectory() as d:
   h=ProductHistory(Path(d)/"h.db")
   with self.assertRaises(ValueError):h.record("en","2026-11-01",[{"event_id":"x","headline":"X","region":"iran","summary":"X","source_url":"file:///secret","priority":90}])
   h.close()
if __name__=="__main__":unittest.main()
