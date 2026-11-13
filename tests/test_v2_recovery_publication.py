import tempfile,unittest
from pathlib import Path
from v2_recovery_publication import ingest_editorial_plan, render_recovery_html
from v2_product_recovery import ProductHistory,build_weekly_intelligence

class PublicationRecoveryTests(unittest.TestCase):
 def test_plan_is_persisted_and_rendered_without_empty_boxes(self):
  with tempfile.TemporaryDirectory() as d:
   h=ProductHistory(Path(d)/"history.db")
   plan={"schema":"aggregateit-editorial-plan/1","product":"arabic","as_of":"2026-11-07T12:00:00+00:00","items":[{"event_id":"evt_iran","region":"iran","priority":91,"topic":"security","evidence":{"quote":"تطورات أمنية موثقة","source_url":"https://example.org/a","source_id":"publisher-a"}}]}
   self.assertEqual(ingest_editorial_plan(h,plan),1)
   report=build_weekly_intelligence(h,"ar","2026-11-07")
   html=render_recovery_html(report)
   self.assertIn('dir="rtl"',html)
   self.assertIn("تطورات أمنية موثقة",html)
   self.assertNotIn("No comparable market observations",html)
   self.assertNotIn("لا توجد تطورات",html)
   h.close()
 def test_no_fake_weekly_completeness(self):
  with tempfile.TemporaryDirectory() as d:
   h=ProductHistory(Path(d)/"history.db")
   h.record("en","2026-11-07",[{"event_id":"a","headline":"A","summary":"A","region":"iran","priority":80,"source_url":"https://example.org/a"}])
   html=render_recovery_html(build_weekly_intelligence(h,"en","2026-11-07"))
   self.assertIn("1/7 days",html)
   self.assertNotIn("7/7 days",html)
   h.close()
if __name__=="__main__":unittest.main()
