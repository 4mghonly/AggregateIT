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

    def test_editorial_capture_capacity_matches_frozen_comparison_boundary(self):
        from v2_b46_live_editorial import compile_captured_articles
        from unittest.mock import patch
        # Boundary is checked before parsing any captured HTML.
        with patch('v2_b46_live_editorial._stamp', return_value=None):
            with self.assertRaisesRegex(ValueError, 'invalid_article_capture_batch'):
                compile_captured_articles([{}] * 65, as_of=AT, slot_id=AT)
        # Verify the 64-item batch gets past the batch-size guard.
        with self.assertRaisesRegex(ValueError, 'unsupported_source_product'):
            compile_captured_articles([{}] * 64, as_of=AT, slot_id=AT)

    def test_simultaneous_native_four_product_archive_has_no_directory_collision(self):
        import tempfile
        from pathlib import Path
        from v2_b86_visual_archive import validate_page_archive
        with tempfile.TemporaryDirectory() as td:
            archive = Path(td) / 'five-native-pages'
            output = run(rss_snapshots=snapshots(), observed_at=AT,
                         fetch=fake_fetch, market_snapshot={}, render_native=True,
                         render_four_products=True, visual_archive_dir=archive)
            self.assertEqual(output['native']['status'], 'HELD_VALID_NATIVE_PAGES')
            self.assertEqual(output['four_products']['schema'], 'aggregateit-v2-b47-four-product-held/1')
            self.assertEqual(len(validate_page_archive(archive)['pages']), 5)
            self.assertFalse(output['four_products']['can_release'])
            self.assertFalse(output['discord_sent'])

    def test_no_post_banner_preserves_top_and_bottom_content(self):
        from io import BytesIO
        from PIL import Image
        from v2_native_evidence_render import _stamp
        original = Image.new('RGB', (3840, 2160), 'white')
        original.paste((10, 180, 20), (0, 0, 3840, 90))
        original.paste((20, 40, 180), (0, 2090, 3840, 2160))
        buffer = BytesIO()
        original.save(buffer, format='PNG')
        with Image.open(BytesIO(_stamp(buffer.getvalue()))) as checked:
            self.assertEqual(checked.size, (3840, 2160))
            self.assertEqual(checked.getpixel((1900, 135)), (10, 180, 20))
            self.assertEqual(checked.getpixel((1900, 2130)), (20, 40, 180))

    def test_b115_per_article_selection_diagnostics_are_sanitized(self):
        receipt = run(rss_snapshots=snapshots(), observed_at=AT, fetch=fake_fetch,
                      compare_same_capture=True, market_snapshot={})['b115_same_capture']
        for product in ('english', 'arabic'):
            rows = receipt['products'][product]['per_article']
            self.assertTrue(rows)
            self.assertEqual(rows[0]['v2_decision_stage'], 'selected')
            self.assertIsNone(rows[0]['v2_decision_reason'])
            self.assertGreaterEqual(rows[0]['v2_preselection_rank'], 1)
        serialized = json.dumps(receipt, ensure_ascii=False)
        self.assertNotIn('Somalia security officials', serialized)
        self.assertNotIn('مباحثات دبلوماسية', serialized)

    def test_compiler_reports_exact_safe_body_rejection_for_a_capture(self):
        from v2_b46_live_editorial import compile_captured_articles
        bad = {'product': 'english', 'source_id': 'en-001',
               'article_url': 'https://www.bbc.com/news/articles/b115-broken',
               'title': 'Somalia officials discuss regional security',
               'published_at': AT, 'html_bytes': b'<html><body>Unstructured sample</body></html>'}
        report = compile_captured_articles([bad], as_of=AT, slot_id=AT,
                                           diagnose_capture=True)
        self.assertEqual(len(report['capture_decisions']), 1)
        self.assertEqual(report['capture_decisions'][0]['stage'], 'rejected_body_or_evidence')
        self.assertTrue(report['capture_decisions'][0]['reason'].replace('_', '').isalnum())
        self.assertNotIn('Unstructured sample', json.dumps(report['capture_decisions']))

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
