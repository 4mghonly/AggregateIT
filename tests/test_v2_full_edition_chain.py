"""Authentic V2 call-chain test: synthetic fixture -> evidence -> product compiler.

No network, model, credentials, database, file output, or Discord delivery.
"""
import json
import unittest
from pathlib import Path
from v2_arabic_application_rehearsal import arabic_synthetic_fixture
from v2_english_application_rehearsal import synthetic_fixture
from v2_offline_rehearsal import run_offline_rehearsal
from v2_product_compiler import compile_daily

REGISTRY_PATH = Path(__file__).resolve().parents[1] / 'config/v2/source_registry.json'


class RealEvidenceToProductTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))

    def test_native_english_daily_chain(self):
        report = run_offline_rehearsal(synthetic_fixture(), self.registry)
        plan = report['products']['english']['plan']
        edition = compile_daily(editorial_plan=plan)
        self.assertGreaterEqual(len(edition['stories']), 2)
        self.assertEqual(edition['product'], 'english')
        self.assertEqual(edition['market_data_status'], 'unavailable')
        self.assertEqual(edition['naysayer_status'], 'insufficient_evidence')
        self.assertFalse(edition['delivery_authorized'])
        self.assertFalse(report['discord_sent'])
        self.assertFalse(report['live_source_fetched'])
        self.assertTrue(all(item['excerpt_id'] for item in edition['stories']))

    def test_native_arabic_daily_chain_rejects_finance(self):
        report = run_offline_rehearsal(arabic_synthetic_fixture(), self.registry)
        edition = compile_daily(editorial_plan=report['products']['arabic']['plan'])
        self.assertEqual(edition['product'], 'arabic')
        self.assertGreaterEqual(len(edition['stories']), 2)
        self.assertEqual(edition['market_data_status'], 'not_applicable')
        self.assertEqual(edition['market_observations'], [])
        self.assertFalse(edition['delivery_authorized'])
        self.assertTrue(all(item['excerpt_id'] for item in edition['stories']))


if __name__ == '__main__':
    unittest.main()
