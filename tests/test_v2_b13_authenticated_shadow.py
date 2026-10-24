"""B13 authenticated run anchors must not claim same-input V1/V2 quality gains."""
import json
import unittest
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'fixtures/v2/b13_authenticated_shadow_evidence_2026-10-24.json'

class ShadowEnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(PATH.read_text(encoding='utf8'))
    def test_three_github_artifacts_attested_by_sha256_match(self):
        items=self.data['v1_english']+self.data['v1_arabic']
        self.assertEqual(len(items),3)
        for record in items:
            self.assertTrue(record['artifact_sha256_verified_against_download'])
            self.assertEqual(len(record['artifact_sha256']),64)
            self.assertEqual(len(record['sha']),40)
            self.assertTrue(record['run_url'].startswith('https://github.com/4mghonly/AggregateIT/actions/runs/'))
    def test_authentic_english_runs_bracket_v2_but_are_not_quality_comparable(self):
        a,b=self.data['v1_english']
        t=datetime.fromisoformat(self.data['v2_b13']['source_observed_utc'])
        self.assertLess(datetime.fromisoformat(a['run_started_at'].replace('Z','+00:00')),t)
        self.assertGreater(datetime.fromisoformat(b['run_started_at'].replace('Z','+00:00')),t)
        self.assertFalse(self.data['same_window_comparison_available'])
        self.assertFalse(self.data['comparison_assessment']['identical_corpus_or_window'])
    def test_arabic_production_window_does_not_match_v2_slot(self):
        ar=self.data['v1_arabic'][0]
        self.assertNotEqual(ar['reported_window_start'],self.data['v2_b13']['slot_marker'])
        self.assertEqual(ar['translation_requested_foreign'],9)
        self.assertEqual(ar['translation_completed_foreign'],5)
        self.assertFalse(self.data['comparison_assessment']['replay_comparable'])
    def test_held_v2_not_promoted_by_v1_delivery_success(self):
        self.assertTrue(self.data['v1_arabic'][0]['delivery_confirmed'])
        self.assertFalse(self.data['v2_b13']['discord_sent'])
        self.assertFalse(self.data['comparison_assessment']['delivery_authorized'])

if __name__=='__main__':unittest.main()
