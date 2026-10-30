import tempfile,unittest,json
from pathlib import Path
from datetime import date
from v2_b95_b97_history import diagnose_conflicts,consolidate

class HistoryConflictTests(unittest.TestCase):
 def test_conflicts_are_reported_not_silently_merged(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)
   for name,digest in [('a','a'*64),('b','b'*64)]:
    row={'schema':'aggregateit-v2-b95-daily-history/1','day':'2026-10-30','stories':{'english':3,'arabic':1},'evidence_sha256':digest,'can_release':False}
    (root/(name+'.json')).write_text(json.dumps(row))
   d=diagnose_conflicts(root,today=date(2026,10,30))
   self.assertEqual(d['conflicting_days'],1)
   self.assertFalse(d['can_release'])
   with self.assertRaises(ValueError):consolidate(root,today=date(2026,10,30))
 def test_agreeing_duplicates_are_not_conflicts(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)
   row={'schema':'aggregateit-v2-b95-daily-history/1','day':'2026-10-30','stories':{'english':3,'arabic':1},'evidence_sha256':'a'*64,'can_release':False}
   for name in ['a','b']:(root/(name+'.json')).write_text(json.dumps(row))
   self.assertEqual(diagnose_conflicts(root,today=date(2026,10,30))['conflicting_days'],0)
if __name__=='__main__':unittest.main()
