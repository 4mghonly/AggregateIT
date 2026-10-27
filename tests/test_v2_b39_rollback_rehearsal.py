"""B39 real filesystem-only durable receipt re-open and release hold regression."""
import unittest
import tempfile
from pathlib import Path
from v2_b39_rollback_rehearsal import exercise_durable_no_send,assess_cutover_blockers

class DurableNoSendTests(unittest.TestCase):
    def test_ambiguous_marker_persists_both_products(self):
        with tempfile.TemporaryDirectory() as d:
            r=exercise_durable_no_send(Path(d),slot_id='2026-10-27T06:00:00+04:00')
        self.assertTrue(r['ambiguous_survived_reopen'])
        self.assertFalse(r['retry_allowed'])
        self.assertEqual(r['products'],['arabic','english'])
        self.assertFalse(r['discord_sent'])
        self.assertEqual(r['rollback_acceptance'],'TABLETOP_ONLY')

    def test_wrong_destination_and_blind_retry_refused(self):
        with tempfile.TemporaryDirectory() as d:
            r=exercise_durable_no_send(Path(d),slot_id='2026-10-27T06:00:00+04:00')
        self.assertTrue(r['wrong_destination_refused'])
        self.assertTrue(r['blind_retry_refused'])

    def test_naive_slot_refused(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                exercise_durable_no_send(Path(d),slot_id='2026-10-27T06:00:00')

    def test_self_reported_passes_do_not_authorize_cutover(self):
        shadow={'schema':'aggregateit-v2-b38-live-parser-pair/1','status':'COMPARED','parity_all':True}
        rehearsal={'schema':'aggregateit-v2-b39-no-send-durable-rehearsal/1',
                   'ambiguous_survived_reopen':True,'retry_allowed':False,
                   'wrong_destination_refused':True,'blind_retry_refused':True}
        r=assess_cutover_blockers(shadow,rehearsal)
        self.assertEqual(r['status'],'HOLD')
        self.assertFalse(r['can_release'])
        self.assertIn('unverified_live_discord_client',r['blockers'])
        self.assertIn('no_authenticated_full_system_v1_v2_comparison',r['blockers'])

    def test_untrusted_claims_refused(self):
        with self.assertRaises(ValueError):
            assess_cutover_blockers({'schema':'bad'}, {'schema':'bad'})
