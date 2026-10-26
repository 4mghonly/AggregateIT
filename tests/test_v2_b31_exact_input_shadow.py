"""B31 actual V1 parser functions vs V2 using identical synthetic RSS bytes."""
import unittest
from unittest.mock import patch

from v2_b31_same_input_shadow import compare_exact_input, _verified_v1_code


OBSERVED = '2026-10-26T06:00:00+00:00'
URL = 'https://example.org/feed.xml'
EN = (b'<?xml version="1.0"?><rss version="2.0"><channel><title>Fixture</title>'
      b'<item><title>Regional Policy Update</title><link>https://example.org/articles/1</link>'
      b'<pubDate>Sun, 25 Oct 2026 05:00:00 GMT</pubDate>'
      b'<description>Observed source statement.</description></item></channel></rss>')
AR = ('<?xml version="1.0"?><rss version="2.0"><channel><title>عينة</title>'
      '<item><title>تطورات أمنية في المنطقة</title><link>https://example.org/articles/2</link>'
      '<pubDate>Sun, 25 Oct 2026 05:00:00 GMT</pubDate>'
      '<description>بيان صادر عن المصدر.</description></item></channel></rss>').encode('utf8')
STALE = (b'<?xml version="1.0"?><rss version="2.0"><channel><title>Fixture</title>'
         b'<item><title>Old regional headline</title><link>https://example.org/articles/3</link>'
         b'<pubDate>Wed, 01 Oct 2025 05:00:00 GMT</pubDate></item></channel></rss>')


class V1V2SameBytes(unittest.TestCase):
    def test_v1_code_matches_pinned_original(self):
        self.assertTrue(_verified_v1_code())

    def test_english_same_input_parser_alignment(self):
        r = compare_exact_input(EN, feed_url=URL, observed_at=OBSERVED, product='english')
        self.assertTrue(r['v1_parser_blob_verified'])
        self.assertTrue(r['parser_alignment'], r)
        self.assertEqual(r['matching_items'], 1)
        self.assertFalse(r['genuine_source_capture_proven'])
        self.assertFalse(r['model_or_delivery_comparable'])

    def test_arabic_same_input_parser_alignment(self):
        r = compare_exact_input(AR, feed_url=URL, observed_at=OBSERVED, product='arabic')
        self.assertTrue(r['parser_alignment'], r)
        self.assertEqual(r['matching_items'], 1)

    def test_v1_stale_is_excluded_from_shared_window(self):
        r = compare_exact_input(STALE, feed_url=URL, observed_at=OBSERVED, product='english')
        self.assertEqual(r['v1_extracted_count'], 1)
        self.assertEqual(r['v1_excluded']['outside_window'], 1)
        self.assertEqual(r['v2_window_eligible'], 0)
        self.assertTrue(r['parser_alignment'])

    def test_invalid_source_url_refused(self):
        with self.assertRaises(ValueError):
            compare_exact_input(EN, feed_url='http://127.0.0.1/feed',
                                observed_at=OBSERVED, product='english')

    def test_empty_bytes_refused(self):
        with self.assertRaises(ValueError):
            compare_exact_input(b'', feed_url=URL, observed_at=OBSERVED, product='english')

    def test_wrong_product_refused(self):
        with self.assertRaises(ValueError):
            compare_exact_input(EN, feed_url=URL, observed_at=OBSERVED, product='finance')

    def test_parser_source_drift_refused(self):
        with patch('v2_b31_same_input_shadow._verified_v1_code', return_value=False):
            with self.assertRaisesRegex(ValueError, 'v1_parser_code_drift'):
                compare_exact_input(EN, feed_url=URL, observed_at=OBSERVED, product='english')

    def test_no_network_during_english_or_arabic_run(self):
        with (patch('socket.create_connection', side_effect=AssertionError('network called')),
              patch('requests.get', side_effect=AssertionError('network called'))):
            self.assertTrue(compare_exact_input(EN, feed_url=URL,
                                                observed_at=OBSERVED, product='english')['parser_alignment'])
            self.assertTrue(compare_exact_input(AR, feed_url=URL,
                                                observed_at=OBSERVED, product='arabic')['parser_alignment'])


if __name__ == '__main__':
    unittest.main()
