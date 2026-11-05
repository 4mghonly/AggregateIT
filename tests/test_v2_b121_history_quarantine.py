import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from v2_b121_history_quarantine import inspect_b95_provenance

def put(root,name,day,digest,eng=3,arab=3):
    (root/name).write_text(json.dumps({
        'schema':'aggregateit-v2-b95-daily-history/1',
        'day':day,'stories':{'english':eng,'arabic':arab},
        'evidence_sha256':digest,'can_release':False}),encoding='utf8')

class HistoryQuarantineTests(unittest.TestCase):
    def test_same_date_different_real_digests_is_quarantined_not_chosen(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            put(root,'111-2026-10-30.json','2026-10-30','a'*64)
            put(root,'112-2026-10-30.json','2026-10-30','b'*64)
            out=inspect_b95_provenance(root,today=date(2026,11,5))
            self.assertEqual(out['quarantined_days'],['2026-10-30'])
            self.assertFalse(out['history_accepted'])
            self.assertEqual(out['days']['2026-10-30']['variants'],2)
            self.assertEqual(len(list(root.glob('*.json'))),2)

    def test_duplicate_same_digest_is_consistent_not_additional_day(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            put(root,'111-2026-10-30.json','2026-10-30','a'*64)
            put(root,'112-2026-10-30.json','2026-10-30','a'*64)
            out=inspect_b95_provenance(root,today=date(2026,11,5))
            self.assertEqual(out['distinct_consistent_days'],1)
            self.assertEqual(out['quarantined_days'],[])
            self.assertFalse(out['seven_day_release_evidence_met'])

    def test_file_without_run_identity_is_unattributed_not_trusted(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            put(root,'2026-10-30.json','2026-10-30','a'*64)
            out=inspect_b95_provenance(root,today=date(2026,11,5))
            self.assertEqual(out['unattributed_files'],['2026-10-30.json'])
            self.assertFalse(out['history_accepted'])

if __name__=='__main__': unittest.main()
