import tempfile,unittest
from pathlib import Path
from v2_recovery_pipeline import persist_bilingual_editorial

class PipelineRecoveryTests(unittest.TestCase):
 def test_persist_two_languages_and_write_weekly(self):
  with tempfile.TemporaryDirectory() as d:
   editorial={"products":{}}
   for product,quote in (("english","Security development"),("arabic","تطور أمني")):
    editorial["products"][product]={"editorial_plan":{"schema":"aggregateit-editorial-plan/1","product":product,"as_of":"2026-11-13T10:00:00+00:00","items":[{"event_id":"evt_"+product,"region":"iran","priority":90,"topic":"security","evidence":{"quote":quote,"source_url":"https://example.org/"+product,"source_id":"src"}}]}}
   result=persist_bilingual_editorial(editorial,Path(d)/"history.db",Path(d)/"weekly")
   self.assertEqual(result["english"]["stored"],1)
   self.assertEqual(result["arabic"]["stored"],1)
   self.assertTrue((Path(d)/"weekly"/"arabic-weekly.html").exists())
   self.assertIn("1/7", (Path(d)/"weekly"/"english-weekly.html").read_text())
 def test_missing_language_fails(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):persist_bilingual_editorial({"products":{"english":{}}},Path(d)/"h.db",Path(d)/"out")
if __name__=="__main__":unittest.main()
