"""B46 stage-2 canonical replay and untrusted baseline guard.

TDD target: no caller-supplied previous-version map can generate a false
'new since previous' claim without independently authenticated prior state.
"""
import unittest
from v2_b46_live_editorial import compile_captured_articles
from tests.test_v2_b46_live_editorial import en,NOW,SLOT

class BaselineAndUrlTests(unittest.TestCase):
    def test_untrusted_previously_seen_versions_never_promote_new_status(self):
        result=compile_captured_articles([en()],as_of=NOW,slot_id=SLOT,
                                         previous_versions={'evt_untrusted':'v0'})
        self.assertEqual(result['products']['english']['newsroom']['stories'][0]['change'],
                         'unknown_no_baseline')
        self.assertTrue(result['unattested_previous_versions_ignored'])
        self.assertFalse(result['prior_baseline_authenticated'])
    def test_tracking_duplicate_is_held_under_article_identity(self):
        original=en();mirror=en()
        mirror['article_url']+='?utm_source=internal'
        result=compile_captured_articles([original,mirror],as_of=NOW,slot_id=SLOT)
        self.assertEqual(result['admitted_articles'],1)
        self.assertEqual(result['held_reasons']['repeated_canonical_article_url'],1)
        self.assertFalse(result['can_send'])
if __name__=='__main__':unittest.main()
