"""B115 daily receipts must retain run provenance and never manufacture dates."""
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from test_v2_replacement_pipeline import AT, fake_fetch, snapshots
from v2_b46_live_editorial_runner import run
from v2_b115_pair_history import make_pair, verify_pair, history


class PairedEvidenceHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.live = run(rss_snapshots=snapshots(), observed_at=AT, fetch=fake_fetch,
                       compare_same_capture=True, market_snapshot={})

    def receipt(self, run_id='41012345678'):
        return make_pair(self.live,run_id=run_id,head_sha='a'*40)

    def test_run_identity_and_bilingual_decisions(self):
        pair=self.receipt()
        self.assertEqual(pair['utc_date'],'2026-10-29')
        self.assertEqual(pair['products']['english']['operational_v2_selected'],1)
        self.assertEqual(pair['products']['arabic']['operational_v2_selected'],1)
        self.assertEqual(verify_pair(pair,run_id='41012345678',today=date(2026,10,30)),pair)
        self.assertFalse(pair['can_release'])

    def test_wrong_run_id_and_date_rejected(self):
        pair=self.receipt()
        with self.assertRaisesRegex(ValueError,'paired_run_identity_mismatch'):
            verify_pair(pair,run_id='41099999999',today=date(2026,10,30))
        with self.assertRaisesRegex(ValueError,'filename_day_mismatch'):
            verify_pair(pair,run_id='41012345678',today=date(2026,10,30),
                        expected_day='2026-10-28')

    def test_two_runs_same_date_count_as_one_date(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            for run_id in ('41012345678','41012345679'):
                pair=self.receipt(run_id)
                (root/(run_id+'-2026-10-29.json')).write_text(json.dumps(pair))
            report=history(root,today=date(2026,10,30))
            self.assertEqual(report['historical_runs'],2)
            self.assertEqual(report['distinct_capture_days'],1)
            self.assertEqual(report['english_positive_days'],1)
            self.assertEqual(report['arabic_positive_days'],1)
            self.assertFalse(report['seven_positive_bilingual_days'])
            self.assertFalse(report['can_release'])

    def test_inconsistent_selection_and_malformed_files_fail_closed(self):
        pair=self.receipt()
        pair['products']['english']['both_selected']=30
        with self.assertRaisesRegex(ValueError,'inconsistent_pair_selection'):
            verify_pair(pair,run_id='41012345678',today=date(2026,10,30))
        with TemporaryDirectory() as tmp:
            (Path(tmp)/'2026-10-29.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'unsafe_pair_history_file'):
                history(Path(tmp),today=date(2026,10,30))

    def test_fake_seven_day_claim_cannot_override_missing_dates(self):
        with TemporaryDirectory() as tmp:
            pair=self.receipt()
            pair['seven_positive_bilingual_days']=True
            (Path(tmp)/'41012345678-2026-10-29.json').write_text(json.dumps(pair))
            report=history(Path(tmp),today=date(2026,10,30))
            self.assertEqual(report['distinct_capture_days'],1)
            self.assertFalse(report['seven_distinct_paired_capture_dates'])


if __name__=='__main__':unittest.main()
