"""B114 history: multiple GitHub runs are not multiple days."""
import json,tempfile,unittest
from datetime import date
from pathlib import Path
from v2_b114_capture_provenance import inspect_slots

class CaptureProvenanceTests(unittest.TestCase):
 def test_multiple_captures_same_date_do_not_inflate_seven_days(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)
   for run,digest,day in (("40991845436","a","2026-10-29"),
                          ("41011433624","b","2026-10-29"),
                          ("41011462021","c","2026-10-29"),
                          ("40991845436","d","2026-10-28")):
    item={"schema":"aggregateit-v2-b95-daily-history/1","day":day,
          "stories":{"english":3,"arabic":1},"evidence_sha256":digest*64,"can_release":False}
    (root/(run+"-"+day+".json")).write_text(json.dumps(item))
   got=inspect_slots(root,today=date(2026,10,30))
   self.assertEqual(got["captured_run_slots"],4)
   self.assertEqual(got["distinct_run_days_count"],2)
   self.assertEqual(got["independent_capture_variants_same_day"],["2026-10-29"])
   self.assertEqual(got["same_run_day_conflicts"],[])
   self.assertFalse(got["seven_distinct_dates_with_capture"])
   self.assertFalse(got["can_release"])

 def test_mismatched_run_date_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)
   data={"schema":"aggregateit-v2-b95-daily-history/1","day":"2026-10-29",
         "stories":{"english":2,"arabic":1},"evidence_sha256":"a"*64,"can_release":False}
   (root/"40991845436-2026-10-28.json").write_text(json.dumps(data))
   with self.assertRaisesRegex(ValueError,"run_filename_date_mismatch"):
    inspect_slots(root,today=date(2026,10,30))

if __name__=="__main__":unittest.main()
