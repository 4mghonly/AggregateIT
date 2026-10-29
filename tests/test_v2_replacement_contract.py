"""Option A: guard against changing existing V1 cadence and delivery routing."""
import tempfile
import unittest
from pathlib import Path
from v2_replacement_contract import check_contract, REQUIRED

class ReplacementContinuityTests(unittest.TestCase):
 def test_current_repository_preserves_v1_contract(self):
  result=check_contract(Path(__file__).resolve().parent.parent)
  self.assertTrue(result["continuity_verified"],result["violations"])
  self.assertEqual(result["checked_files"],len(REQUIRED))
  self.assertFalse(result["cutover_authorized"])
 def test_missing_gazette_schedule_is_blocked(self):
  root=Path(__file__).resolve().parent.parent
  with tempfile.TemporaryDirectory() as tmp:
   alt=Path(tmp)
   for name in REQUIRED:
    p=alt/name
    p.parent.mkdir(parents=True,exist_ok=True)
    text=(root/name).read_text(encoding="utf8")
    if name==".github/workflows/slide.yml":
     text=text.replace('cron: "30 11 * * *"','cron: "30 12 * * *"')
    p.write_text(text,encoding="utf8")
   result=check_contract(alt)
   self.assertFalse(result["continuity_verified"])
   self.assertTrue(any("gazette_schedule" in x for x in result["violations"]))
 def test_missing_arabic_discord_route_is_blocked(self):
  root=Path(__file__).resolve().parent.parent
  with tempfile.TemporaryDirectory() as tmp:
   alt=Path(tmp)
   for name in REQUIRED:
    p=alt/name;p.parent.mkdir(parents=True,exist_ok=True)
    text=(root/name).read_text(encoding="utf8")
    if name==".github/workflows/arabic-scheduler.yml":
     text=text.replace("DISCORD_WEBHOOK_ARABIC: ${{ secrets.DISCORD_WEBHOOK_ARABIC }}","DISCORD_WEBHOOK_ARABIC: ''")
    p.write_text(text,encoding="utf8")
   self.assertFalse(check_contract(alt)["continuity_verified"])
if __name__=="__main__":unittest.main()
