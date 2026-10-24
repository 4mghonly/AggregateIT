"""Prevent interpreting missing V1 observations as evidence of V2 improvement."""
import unittest
from v2_a9_shadow_readiness import classify_shadow_pair

PERIOD = ('2026-10-24T06:00:00+04:00', '2026-10-24T12:00:00+04:00')


def run(product, revision):
    return {
        'product': product, 'window_start': PERIOD[0], 'window_end': PERIOD[1],
        'code_revision': revision, 'delivery_status': 'not_attempted',
        'metrics': {'sources_attempted': 2, 'sources_usable': 2,
                    'events_selected': 1, 'items_cited': 1,
                    'items_rendered': 1, 'translation_attempted': 0,
                    'translation_succeeded': 0, 'layout_omissions': 0,
                    'clipped_items': 0}, 'region_counts': {'jordan': 1},
    }


class ShadowReadinessTests(unittest.TestCase):
    def test_no_baseline_never_declares_improvement(self):
        result = classify_shadow_pair(None, run('english', 'b'*40))
        self.assertFalse(result['comparable'])
        self.assertEqual(result['reason'], 'v1_baseline_missing')
        self.assertFalse(result['delivery_authorized'])
        self.assertNotIn('metrics', result)

    def test_no_candidate_stays_blocked(self):
        result = classify_shadow_pair(run('arabic', 'a'*40), None)
        self.assertEqual(result['reason'], 'v2_candidate_missing')

    def test_same_window_still_requires_evidence_attestation(self):
        result = classify_shadow_pair(run('english', 'a'*40), run('english', 'b'*40))
        self.assertFalse(result['comparable'])
        self.assertEqual(result['reason'], 'unattested_run_metrics')

    def test_fully_attested_same_window_comparison_only(self):
        a = run('english', 'a'*40); b = run('english', 'b'*40)
        result = classify_shadow_pair(a,b,v1_attested=True,v2_attested=True)
        self.assertTrue(result['comparable'])
        self.assertEqual(result['status'], 'offline_comparison_only')
        self.assertFalse(result['delivery_authorized'])

    def test_different_product_is_not_comparable(self):
        result = classify_shadow_pair(run('english', 'a'*40), run('arabic', 'b'*40),v1_attested=True,v2_attested=True)
        self.assertEqual(result['reason'], 'different_product_or_window')

    def test_identical_revisions_are_not_v1_vs_v2(self):
        result = classify_shadow_pair(run('arabic', 'a'*40), run('arabic', 'a'*40),v1_attested=True,v2_attested=True)
        self.assertEqual(result['reason'], 'revisions_not_distinct')

    def test_attestation_cannot_override_invalid_metrics(self):
        a=run('english','a'*40);b=run('english','b'*40)
        b['metrics']['items_rendered']=99
        with self.assertRaises(ValueError): classify_shadow_pair(a,b,v1_attested=True,v2_attested=True)

if __name__=='__main__': unittest.main()
