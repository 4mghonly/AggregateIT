"""B33 integrity and no-send contract for future authentic byte import."""
import hashlib
import unittest

from v2_b33_capture_comparison import compare_imported_capture
from test_v2_b31_exact_input_shadow import EN, AR, OBSERVED, URL


def receipt(raw, product):
    return {'schema': 'aggregateit-v2-b33-import/1', 'product': product,
            'feed_url': URL, 'observed_at': OBSERVED,
            'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw),
            'capture_kind': 'synthetic_fixture'}


class ImportComparisonTests(unittest.TestCase):
    def test_english_import_round_trip(self):
        r = compare_imported_capture(EN, receipt=receipt(EN, 'english'))
        self.assertTrue(r['import_integrity_verified'])
        self.assertTrue(r['stdlib_feedparser']['parity_passed'])
        self.assertTrue(r['v1_v2_same_input']['parser_alignment'])
        self.assertFalse(r['external_provenance_authenticated'])
        self.assertFalse(r['can_publish'])

    def test_arabic_import_round_trip(self):
        r = compare_imported_capture(AR, receipt=receipt(AR, 'arabic'))
        self.assertEqual(r['v1_v2_same_input']['matching_items'], 1)
        self.assertFalse(r['discord_sent'])

    def test_tampered_capture_refused(self):
        with self.assertRaisesRegex(ValueError, 'capture_integrity_mismatch'):
            compare_imported_capture(EN + b'change', receipt=receipt(EN, 'english'))

    def test_unsupported_provenance_refused(self):
        r = receipt(EN, 'english'); r['capture_kind'] = 'publisher_authenticated'
        with self.assertRaisesRegex(ValueError, 'invalid_capture_kind'):
            compare_imported_capture(EN, receipt=r)

    def test_non_https_feed_refused(self):
        r = receipt(EN, 'english'); r['feed_url'] = 'http://localhost/rss'
        with self.assertRaises(ValueError):
            compare_imported_capture(EN, receipt=r)


if __name__ == '__main__':
    unittest.main()
