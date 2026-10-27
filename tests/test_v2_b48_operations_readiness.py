"""B48 operational signals must never be mistaken for production health."""
import unittest
from v2_b48_operations_readiness import evaluate_operations

AT='2026-10-27T09:00:00+00:00'
def fixture():
    daily={p:{'page_count':2 if p=='english' else 3,
          'destination_key':'discord_webhook' if p=='english' else 'discord_webhook_arabic',
          'can_release':False,'story_count':2,
          'translation_verified':False,'coverage_gaps':['gcc'] if p=='arabic' else []}
          for p in ('english','arabic')}
    weekly={p:{'days_with_real_daily_snapshots':1,'complete_seven_day_history':False,
               'pdf_rendered':False} for p in ('english','arabic')}
    four={'schema':'aggregateit-v2-b47-four-product-held/1','daily':daily,
          'weekly':weekly,'can_release':False,'discord_sent':False}
    production={'schema':'aggregateit-v2-b41-readonly-preflight/1','baseline_main_sha':'a'*40,
        'preflight_findings':['production_source_floor_below_two_somalia',
             'production_audit_can_advance_main_during_canary']}
    durable={'schema':'aggregateit-v2-b39-no-send-durable-rehearsal/1',
             'ambiguous_survived_reopen':True,'blind_retry_refused':True,'retry_allowed':False}
    return four,production,durable

class OperationalTests(unittest.TestCase):
    def test_partial_week_and_source_floor_generate_real_alerts(self):
        r=evaluate_operations(*fixture(),observed_at=AT)
        codes={a['code'] for a in r['alerts']}
        self.assertIn('production_source_floor_below_two_somalia',codes)
        self.assertIn('weekly_window_not_full',codes)
        self.assertIn('arabic_geographic_gaps',codes)
        self.assertIn('b45_live_translation_not_authenticated',codes)
        self.assertFalse(r['can_release'])
    def test_unknown_d1_headroom_refuses_all_optional_writes(self):
        r=evaluate_operations(*fixture(),observed_at=AT)
        self.assertEqual(r['optional_telemetry_action'],'hold_unverified_account_headroom')
        self.assertEqual(r['telemetry_records_written_to_db'],0)
        self.assertFalse(r['backup_verified'])
    def test_crash_marker_missing_is_error(self):
        args=list(fixture());args[2]['ambiguous_survived_reopen']=False
        with self.assertRaisesRegex(ValueError,'unreliable_crash_state'):
            evaluate_operations(*args,observed_at=AT)
    def test_sender_or_destinations_forged_are_rejected(self):
        args=list(fixture());args[0]['daily']['arabic']['destination_key']='discord_webhook'
        with self.assertRaises(ValueError):
            evaluate_operations(*args,observed_at=AT)
    def test_forged_7day_history_rejected(self):
        args=list(fixture());args[0]['weekly']['english']['complete_seven_day_history']=True
        with self.assertRaisesRegex(ValueError,'forged_full_week_status'):
            evaluate_operations(*args,observed_at=AT)
    def test_claim_of_live_translation_not_accepted(self):
        args=list(fixture());args[0]['daily']['arabic']['translation_verified']=True
        with self.assertRaises(ValueError):
            evaluate_operations(*args,observed_at=AT)
if __name__=='__main__':unittest.main()
