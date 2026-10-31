"""B115 frozen real-path RSS/HTML comparison and fail-closed integrity checks."""
import json
import unittest
from unittest.mock import patch

from test_v2_replacement_pipeline import AT, EMPTY, fake_fetch, snapshots
from v2_b46_live_editorial_runner import run
from v2_b115_same_capture import compare_same_capture


class B115SameCaptureTests(unittest.TestCase):
    def test_one_network_capture_both_real_deterministic_processors(self):
        called = []
        def counted(url, **kwargs):
            called.append(url)
            return fake_fetch(url, **kwargs)
        output = run(rss_snapshots=snapshots(), observed_at=AT,
                     fetch=counted, compare_same_capture=True, market_snapshot={})
        receipt = output['b115_same_capture']
        self.assertEqual(receipt['schema'], 'aggregateit-v2-b115-same-capture/1')
        self.assertEqual(receipt['utc_date'], '2026-10-29')
        self.assertTrue(receipt['v1_deterministic_functions_executed'])
        self.assertTrue(receipt['v2_actual_editorial_compiler_executed'])
        self.assertTrue(receipt['source_capture_identity_verified'])
        self.assertGreaterEqual(len(receipt['feeds']), 4)
        self.assertEqual(len(receipt['articles']), 2)
        self.assertGreaterEqual(len(called), 4)  # bounded source-diversity attempts may add feeds
        self.assertEqual(receipt['products']['english']['attempted_article_pages'], 1)
        self.assertEqual(receipt['products']['arabic']['attempted_article_pages'], 1)
        self.assertEqual(receipt['products']['english']['v2_selected'], 1)
        self.assertEqual(receipt['products']['arabic']['v2_selected'], 1)
        self.assertFalse(receipt['can_release'])
        self.assertFalse(output['discord_sent'])
        serialized = json.dumps(receipt, ensure_ascii=False)
        self.assertNotIn('Somalia security officials', serialized)
        self.assertNotIn('مباحثات دبلوماسية', serialized)
        self.assertNotIn('<article>', serialized)

    def test_excessive_feed_count_remains_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unbounded_same_capture'):
            compare_same_capture([{'product':'english','source_id':'en-001','body':EMPTY}]*17, [], observed_at=AT)

    def test_same_input_replay_is_deterministic_with_fixed_clock(self):
        first = run(rss_snapshots=snapshots(), observed_at=AT, fetch=fake_fetch,
                    compare_same_capture=True, market_snapshot={})['b115_same_capture']
        second = run(rss_snapshots=snapshots(), observed_at=AT, fetch=fake_fetch,
                     compare_same_capture=True, market_snapshot={})['b115_same_capture']
        self.assertEqual(first, second)

    def test_article_absent_from_frozen_rss_is_refused(self):
        feeds = [{'product': p, 'source_id': s,
                  'body': EMPTY} for p, s in [('english', 'en-001'), ('arabic', 'ar-s003')]]
        page = {'product': 'english', 'source_id': 'en-001',
                'article_url': 'https://www.bbc.com/news/articles/unknown',
                'title': 'Somalia security officials outline latest measures',
                'published_at': '2026-10-29T08:00:00+00:00',
                'html_bytes': b'<article><p>Somalia security action is reported.</p></article>'}
        with self.assertRaisesRegex(ValueError, 'article_not_in_frozen_feed'):
            compare_same_capture(feeds, [page], observed_at=AT)

    def test_wrong_v1_code_blob_is_refused(self):
        with patch('v2_b115_same_capture._git_blob', return_value='0' * 40):
            with self.assertRaisesRegex(ValueError, 'v1_editorial_code_drift'):
                compare_same_capture([], [], observed_at=AT)

    def test_older_runner_default_does_not_run_comparison(self):
        output = run(rss_snapshots=snapshots(), observed_at=AT, fetch=fake_fetch,
                     market_snapshot={})
        self.assertEqual(output['b115_same_capture'], {'status': 'NOT_REQUESTED'})


if __name__ == '__main__':
    unittest.main()
