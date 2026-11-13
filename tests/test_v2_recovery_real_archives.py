import json,tempfile,unittest,zipfile
from pathlib import Path
from v2_recovery_arabic_archive import import_arabic_briefs
from v2_recovery_english_archive import import_english_runs

class GenuineArchiveImportTests(unittest.TestCase):
 def test_bilingual_archives_preserve_real_dates(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   for day in range(7,14):
    ar={"schema_version":"arabic-brief-v3","sample":False,"window_end":f"2026-11-{day:02d}T18:00:00+04:00","events":[
      {"title_ar":"تطور أمني","summary_ar":"تقرير عن تطور أمني","region":"iran","topic":"security","severity":"high","sources":[{"url":f"https://example.org/ar/{day}"}]}]}
    en={"run":f"2026-11-{day:02d}T12:00:00+00:00","events":[{"event_id":f"evt-{day}","title":"Security development",
      "importance":"High","what_changed":"Reported development","analysis":{"assessment":"A cautious assessment of reported security developments."},"sources":[{"url":f"https://example.org/en/{day}"}]}]}
    with zipfile.ZipFile(root/f"ar-{day}.zip","w") as z:z.writestr("briefing.json",json.dumps(ar))
    with zipfile.ZipFile(root/f"en-{day}.zip","w") as z:z.writestr("run.json",json.dumps(en))
   ar_db=root/"arabic_v2.sqlite";en_db=root/"english_v1_baseline.sqlite";out=root/"out"
   a=import_arabic_briefs(sorted(root.glob("ar-*.zip")),ar_db,out)
   e=import_english_runs(sorted(root.glob("en-*.zip")),en_db,out)
   self.assertTrue(a["complete_week"])
   self.assertTrue(e["complete_week"])
   self.assertEqual(a["days_observed"],7)
   self.assertEqual(e["days_observed"],7)
   self.assertTrue((out/"arabic-weekly.html").exists())
   self.assertTrue((out/"english-weekly.html").exists())
   self.assertIn("Historical model assessment (unverified)",(out/"english-weekly.html").read_text())
 def test_reject_synthetic_arabic_archive(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"briefing.json"
   p.write_text(json.dumps({"schema_version":"arabic-brief-v3","sample":True,"window_end":"2026-11-13","events":[]}))
   with self.assertRaises(ValueError):import_arabic_briefs([p],Path(d)/"db",Path(d)/"out")
if __name__=="__main__":unittest.main()
