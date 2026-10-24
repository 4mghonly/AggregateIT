"""Fail-closed evidence and critic admission at the final publication compiler."""
import unittest
from v2_product_compiler import compile_daily

SLOT = '2026-10-24T06:00:00+04:00'

def plan(product):
    return {
        'schema': 'aggregateit-editorial-plan/1', 'delivery_authorized': False,
        'slot_id': SLOT, 'product': product, 'language': 'en',
        'items': [{
            'event_id':'evt_test','region':'gcc','topic':'geopolitics',
            'reporting_status':'publisher_attributed_not_independently_verified',
            'evidence': {'excerpt_id':'exc1','source_id':'s1',
                         'quote':'A synthetic test item',
                         'source_url':'https://example.org/item',
                         'original_language':'en'},
        }]
    }

class PublicationAdmissionTests(unittest.TestCase):
    def test_forged_successful_naysayer_status_cannot_bypass_quality_gate(self):
        candidate = {
            'schema': 'aggregateit-naysayer-report/1',
            'delivery_authorized': False, 'product': 'english',
            'cadence': 'daily', 'slot_id': SLOT,
            'quality_gate_passed': False,
            'sections': [{'review_status': 'supported_challenge',
                          'cited_evidence': []}]
        }
        with self.assertRaisesRegex(ValueError, 'unverified_critical_review'):
            compile_daily(editorial_plan=plan('english'), critic_report=candidate)

    def test_successful_critic_requires_evidence_references(self):
        candidate = {
            'schema': 'aggregateit-naysayer-report/1',
            'delivery_authorized': False, 'product': 'english',
            'cadence': 'daily', 'slot_id': SLOT,
            'quality_gate_passed': True,
            'sections': [{'review_status': 'supported_challenge',
                          'cited_evidence': []}]
        }
        with self.assertRaisesRegex(ValueError, 'unverified_critical_review'):
            compile_daily(editorial_plan=plan('english'), critic_report=candidate)

    def test_degraded_critic_stays_visible_without_quality_promotion(self):
        candidate = {
            'schema': 'aggregateit-naysayer-report/1',
            'delivery_authorized': False, 'product': 'english',
            'cadence': 'daily', 'slot_id': SLOT,
            'quality_gate_passed': False,
            'sections': [{'review_status': 'insufficient_evidence',
                          'cited_evidence': []}]
        }
        edition = compile_daily(editorial_plan=plan('english'), critic_report=candidate)
        self.assertEqual(edition['naysayer_status'], 'insufficient_evidence')
        self.assertFalse(edition['delivery_authorized'])
