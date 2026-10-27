"""B38 proof: original V1 and V2 receive identical buffer, failure is not retried."""
import unittest
from unittest.mock import patch
import v2_b38_live_pair as b38

OBSERVED='2026-10-27T06:00:00+00:00'
SAMPLE=(b'<?xml version="1.0"?><rss version="2.0"><channel><title>Controlled</title>'
        b'<item><title>Regional Policy Update</title><link>https://example.org/article/1</link>'
        b'<pubDate>Tue, 27 Oct 2026 05:00:00 GMT</pubDate></item></channel></rss>')

class SameByteTests(unittest.TestCase):
    def test_exact_same_buffer_passed_to_both_parsers(self):
        with (patch.object(b38,'compare_exact_input',return_value={
              'parser_alignment':True,'v1_window_eligible':1,'v2_window_eligible':1,
              'matching_items':1,'v1_only':[],'v2_only':[],'v1_parser_blob_verified':True}) as v1,
              patch.object(b38,'extract_candidates',return_value={
              'candidate_count':1,'items':[{'title':'Regional Policy Update','article_url':'https://example.org/article/1',
              'source_feed_url':'https://example.org/rss','published_at':OBSERVED}]}) as v2):
            result=b38.compare_captured_headlines(SAMPLE,product='english',feed_url='https://example.org/rss',observed_at=OBSERVED)
        self.assertEqual(v1.call_args.args[0],SAMPLE)
        self.assertEqual(v2.call_args.args[0],SAMPLE)
        self.assertEqual(result['mobile_cards'],1)
        self.assertTrue(result['same_exact_input'])
        self.assertFalse(result['full_edition_comparable'])
        self.assertFalse(result['discord_sent'])
        self.assertNotIn('Regional Policy Update',repr(result))

    def test_drift_requires_hold(self):
        with (patch.object(b38,'compare_exact_input',return_value={
              'parser_alignment':False,'v1_window_eligible':2,'v2_window_eligible':1,
              'matching_items':1,'v1_only':['a'*64],'v2_only':[],'v1_parser_blob_verified':True}),
              patch.object(b38,'extract_candidates',return_value={'candidate_count':1,'items':[]})):
            result=b38.compare_captured_headlines(SAMPLE,product='arabic',feed_url='https://example.org/rss',observed_at=OBSERVED)
        self.assertEqual(result['parser_status'],'HOLD_MISMATCH')
        self.assertEqual(result['v1_only_count'],1)

    def test_one_attempt_per_feed_if_transport_unavailable(self):
        with patch.object(b38,'pinned_https_fetch',side_effect=TimeoutError('offline')) as fetch:
            outcome=b38.run_live_pairs()
        self.assertEqual(fetch.call_count,len(b38.SOURCES))
        self.assertEqual(outcome['status'],'HOLD')
        self.assertFalse(outcome['discord_sent'])

    def test_invalid_input_and_insecure_url_refused(self):
        for raw,product,url in [(b'','english','https://example.org/rss'),
                                (SAMPLE,'other','https://example.org/rss'),
                                (SAMPLE,'english','http://example.org/rss')]:
            with self.assertRaises(ValueError):
                b38.compare_captured_headlines(raw,product=product,feed_url=url,observed_at=OBSERVED)

    def test_registered_sources_are_two_languages_without_france24(self):
        self.assertEqual({p for p,_,_ in b38.SOURCES},{'english','arabic'})
        self.assertTrue(all('france24' not in url for _,_,url in b38.SOURCES))
