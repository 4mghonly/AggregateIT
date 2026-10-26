"""Reconstruction-specific offline acceptance for the missing V2 work packages."""
import unittest

from v2_b14_admission import admit_candidates
from v2_b15_source_watch import summarize_source_watch
from v2_b16_replay_contract import build_replay_manifest, verify_replay_manifest
from v2_b17_release_gate import evaluate_release_readiness
from v2_b18_private_digest import make_private_digest, digest_fingerprint
from v2_b20_private_mobile import render_private_mobile
from v2_b21_private_snapshots import capture_private_snapshot, verify_private_snapshot
from v2_b22_private_packets import rehearse_private_packets
from v2_b23_compact_mobile import audit_compact_markup
from v2_b24_editorial_diversity import coverage_diagnostic
from v2_b25_recovery import plan_private_recovery
from v2_b26_parser_shadow import compare_parser_outputs
from v2_b27_private_acceptance import evaluate_private_acceptance
from v2_b28_canary_rehearsal import rehearse_canary_rollback


SLOT = '2026-10-25T06:00:00+04:00'
FEED = 'https://news.example.org/rss'
ARTICLE = 'https://news.example.org/story/1'
RSS = (b'<?xml version="1.0"?><rss version="2.0"><channel><title>Sample</title>'
       b'<item><title>Gulf energy briefing</title><link>https://news.example.org/story/1</link>'
       b'<pubDate>Sun, 25 Oct 2026 02:00:00 GMT</pubDate></item></channel></rss>')


def roster():
    return {'schema': 'aggregateit-v2-feed-candidates/1', 'can_publish': False, 'items': [
        {'candidate_id': 'fc_1', 'article_url': ARTICLE, 'source_feed_url': FEED,
         'title': 'Gulf energy briefing', 'observed_at': SLOT, 'published_at': SLOT}]}


def captures():
    return [{'article_url': ARTICLE, 'source_feed_url': FEED,
             'title': 'Gulf energy briefing', 'excerpt_id': 'excerpt-1',
             'original_language': 'en', 'verified_claims': 1, 'captured_at': SLOT}]


def story(product):
    lang = 'ar' if product == 'arabic' else 'en'
    return {'candidate_id': 'fc_1', 'excerpt_id': 'excerpt-1', 'source_id': 'source-1',
            'article_url': ARTICLE, 'title': 'عنوان الخبر الإقليمي' if lang == 'ar' else 'Gulf energy briefing',
            'quote': 'بيانات صادرة عن المصدر' if lang == 'ar' else 'Publisher attributed statement.',
            'region': 'gcc', 'original_language': lang,
            'topic': 'security' if lang == 'ar' else 'finance'}


def digest(product):
    return make_private_digest(product=product, slot_id=SLOT,
                               stories=[story(product)], missing_regions=['yemen'])


def packet(product):
    return {'schema': 'aggregateit-v2-discord-preview/1', 'product': product,
            'destination_key': 'discord_webhook_arabic' if product == 'arabic' else 'discord_webhook',
            'slot_id': SLOT, 'message_count': 1, 'can_send': False, 'synthetic': True,
            'webhook_url': None, 'attachments': [{'sha256': 'a' * 64, 'size_bytes': 500}]}


def tabletop():
    return rehearse_canary_rollback(baseline_sha='a' * 40, candidate_sha='b' * 40,
                                   incident='delivery_ambiguity',
                                   receipts=[{'product': 'arabic', 'status': 'ambiguous'}])


class AdmissionTests(unittest.TestCase):
    def test_admits_attributed_capture_privately(self):
        result = admit_candidates(roster(), captures())
        self.assertEqual(len(result['admitted']), 1)
        self.assertFalse(result['can_publish'])

    def test_holds_missing_evidence(self):
        self.assertEqual(admit_candidates(roster(), [])['rejected'][0]['reason'],
                         'article_evidence_missing')

    def test_holds_title_mismatch(self):
        c = captures(); c[0]['title'] = 'Unrelated'
        self.assertEqual(admit_candidates(roster(), c)['rejected'][0]['reason'], 'title_mismatch')

    def test_holds_language_unverified(self):
        c = captures(); c[0]['original_language'] = 'und'
        self.assertEqual(admit_candidates(roster(), c)['rejected'][0]['reason'], 'language_unverified')

    def test_duplicate_capture_refused(self):
        with self.assertRaisesRegex(ValueError, 'duplicate_capture'):
            admit_candidates(roster(), captures() * 2)

    def test_forced_sendable_roster_refused(self):
        r = roster(); r['can_publish'] = True
        with self.assertRaises(ValueError):
            admit_candidates(r, captures())


class SourceAndReplayTests(unittest.TestCase):
    def test_source_unknown_is_not_healthy(self):
        r = summarize_source_watch([{'source_id': 's1', 'status': 'network_error'}],
                                   expected_source_ids=['s1', 's2'])
        self.assertEqual(r['healthy_count'], 0)
        self.assertEqual(r['unknown_count'], 2)
        self.assertFalse(r['auto_replacement'])

    def test_source_health_is_read_only(self):
        r = summarize_source_watch([{'source_id': 's1', 'status': 'usable_dated_feed',
                                     'recent_count': 2}], expected_source_ids=['s1'])
        self.assertEqual(r['healthy_count'], 1)
        self.assertFalse(r['sources'][0]['can_promote'])

    def test_duplicate_health_observation_refused(self):
        with self.assertRaises(ValueError):
            summarize_source_watch([{'source_id': 's1', 'status': 'stale_feed'}] * 2,
                                   expected_source_ids=['s1'])

    def test_exact_replay(self):
        rows = [{'source_id': 's1', 'source_revision': 'r1', 'source_bytes': RSS}]
        receipt = build_replay_manifest(rows)
        self.assertTrue(verify_replay_manifest(receipt, rows))
        self.assertFalse(verify_replay_manifest(receipt, [{**rows[0], 'source_bytes': b'changed'}]))

    def test_replay_bytes_not_embedded(self):
        self.assertFalse(build_replay_manifest([{'source_id': 's', 'source_revision': 'r',
                                                'source_bytes': b'secret'}])['source_bytes_embedded'])

    def test_duplicate_replay_revision_refused(self):
        with self.assertRaises(ValueError):
            build_replay_manifest([{'source_id': 's', 'source_revision': 'r',
                                    'source_bytes': b'x'}] * 2)


class DigestAndMobileTests(unittest.TestCase):
    def test_english_digest_has_evidence_and_private_status(self):
        r = digest('english')
        self.assertEqual(len(r['stories']), 1)
        self.assertEqual(len(digest_fingerprint(r)), 64)
        self.assertFalse(r['delivery_authorized'])

    def test_arabic_digest_has_no_finance(self):
        bad = story('arabic'); bad['topic'] = 'finance'
        with self.assertRaisesRegex(ValueError, 'topic_not_allowed'):
            make_private_digest(product='arabic', slot_id=SLOT, stories=[bad])

    def test_cross_language_refused(self):
        with self.assertRaises(ValueError):
            make_private_digest(product='arabic', slot_id=SLOT, stories=[story('english')])

    def test_duplicate_story_refused(self):
        with self.assertRaises(ValueError):
            make_private_digest(product='english', slot_id=SLOT,
                                stories=[story('english')] * 2)

    def test_markup_language_direction_and_viewport(self):
        for product in ('english', 'arabic'):
            html = render_private_mobile(digest(product))
            audit = audit_compact_markup(html, product=product, expected_stories=1)
            self.assertTrue(audit['static_checks_passed'])
            self.assertFalse(audit['real_device_verified'])

    def test_markup_escapes_untrusted_title(self):
        r = digest('english'); r['stories'][0]['title'] = '<script>alert(1)</script>'
        rendered = render_private_mobile(r)
        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;script&gt;', rendered)

    def test_markup_cannot_become_deliverable(self):
        r = digest('english'); r['delivery_authorized'] = True
        with self.assertRaises(ValueError):
            render_private_mobile(r)

    def test_missing_viewport_fails_static_review(self):
        html = render_private_mobile(digest('english')).replace('width=device-width', 'width=1000')
        self.assertFalse(audit_compact_markup(html, product='english',
                                              expected_stories=1)['static_checks_passed'])


class SnapshotPacketDiversityTests(unittest.TestCase):
    def test_html_snapshot_immutable_receipt(self):
        page = render_private_mobile(digest('english')).encode()
        receipt = capture_private_snapshot(filename='en.html', content=page, product='english',
                                           media_type='text/html', observed_at=SLOT)
        self.assertTrue(verify_private_snapshot(receipt, page))
        self.assertFalse(verify_private_snapshot(receipt, page + b'x'))
        self.assertFalse(receipt['bytes_retained_in_receipt'])

    def test_snapshot_rejects_path_escape(self):
        with self.assertRaises(ValueError):
            capture_private_snapshot(filename='../lost.html', content=b'<!doctype html>',
                                     product='english', media_type='text/html', observed_at=SLOT)

    def test_rehearsal_separates_destinations(self):
        result = rehearse_private_packets(packet('english'), packet('arabic'))
        self.assertTrue(result['independent_destination_keys'])
        self.assertFalse(result['discord_sent'])

    def test_rehearsal_refuses_misrouting(self):
        ar = packet('arabic'); ar['destination_key'] = 'discord_webhook'
        with self.assertRaises(ValueError):
            rehearse_private_packets(packet('english'), ar)

    def test_balance_records_missing_regions(self):
        r = coverage_diagnostic(digest('english'), target_regions=['gcc', 'yemen'])
        self.assertEqual(r['missing_target_regions'], ['yemen'])
        self.assertEqual(r['max_source_share'], 1.0)
        self.assertTrue(r['source_concentration_warning'])

    def test_technical_gate_still_unsendable(self):
        ready = evaluate_release_readiness({k: True for k in ('dependency_suite_passed',
            'source_parser_parity_passed', 'bilingual_preview_passed',
            'destination_isolation_passed', 'rollback_rehearsal_passed',
            'live_same_window_measured')})
        self.assertTrue(ready['candidate_ready'])
        self.assertFalse(ready['can_send'])
        self.assertFalse(ready['rights_or_legal_review_in_scope'])

    def test_recovery_is_manual_and_bounded(self):
        r = plan_private_recovery(stage='source_fetch', failure_code='timeout', attempts=1)
        self.assertTrue(r['retry_eligible'])
        self.assertFalse(r['retry_automatically'])
        self.assertFalse(plan_private_recovery(stage='parse', failure_code='schema_error',
                                               attempts=0)['retry_eligible'])


class ShadowAndRollbackTests(unittest.TestCase):
    def test_parity_on_exact_synthetic_rss_bytes(self):
        r = compare_parser_outputs(RSS, feed_url=FEED, observed_at=SLOT)
        self.assertTrue(r['same_input_verified'])
        self.assertTrue(r['parity_passed'], (r['missing_from_feedparser'], r['extra_in_feedparser']))
        self.assertFalse(r['live_parser_parity_proven'])

    def test_shadow_rejects_inconsistent_provenance(self):
        with self.assertRaises(ValueError):
            compare_parser_outputs(RSS, feed_url=FEED, observed_at=SLOT,
                                   input_provenance='live' )

    def test_rollback_rehearsal_preserves_ambiguity(self):
        r = tabletop()
        self.assertEqual(r['ambiguous_receipts'], 1)
        self.assertIn('do_not_replay_ambiguous_delivery', r['plan'])
        self.assertFalse(r['routes_changed'])

    def test_same_ref_not_rollback(self):
        with self.assertRaises(ValueError):
            rehearse_canary_rollback(baseline_sha='a'*40, candidate_sha='a'*40,
                                    incident='source_integrity', receipts=[])

    def test_acceptance_is_partial_on_synthetic(self):
        ad = admit_candidates(roster(), captures())
        watch = summarize_source_watch([{'source_id':'source-1', 'status':'usable_dated_feed',
                                        'recent_count':1}], expected_source_ids=['source-1'])
        shadow = compare_parser_outputs(RSS, feed_url=FEED, observed_at=SLOT)
        mobile_en = audit_compact_markup(render_private_mobile(digest('english')),
                                         product='english', expected_stories=1)
        mobile_ar = audit_compact_markup(render_private_mobile(digest('arabic')),
                                         product='arabic', expected_stories=1)
        result = evaluate_private_acceptance(admission=ad, source_watch=watch,
                     parser_shadow=shadow, english_mobile=mobile_en, arabic_mobile=mobile_ar,
                     packet_rehearsal=rehearse_private_packets(packet('english'), packet('arabic')),
                     rollback=tabletop())
        self.assertEqual(result['status'], 'PARTIAL_OFFLINE')
        self.assertFalse(result['delivery_authorized'])


if __name__ == '__main__':
    unittest.main()
