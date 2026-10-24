"""B10 red/green: opt-in registered large RSS parser; no Arabic language leakage."""
import unittest
from datetime import datetime
from v2_feed_probe import inspect_feed_bytes, MAX_BYTES
from v2_feed_items import extract_candidates
from v2_large_feed_adapter import probe_regional_source, profile_for

NOW='2026-10-24T12:00:00+04:00'
def rss(lang='ar', n=1, padding=220001):
    title='عنوان أمني عن العراق والمنطقة' if lang=='ar' else 'Security developments in the region'
    entry=('<item><title>'+title+'</title><link>https://shafaq.com/ar/story-'+str(n)+
           '</link><pubDate>Sat, 24 Oct 2026 06:00:00 GMT</pubDate><description>'+
           ('x'*padding)+'</description></item>')
    return ('<rss><channel>'+entry+'</channel></rss>').encode('utf8')

class RegisteredLargeFeeds(unittest.TestCase):
    def test_default_probe_still_refuses_more_than_200kb(self):
        out=inspect_feed_bytes(rss(),now=NOW)
        self.assertEqual(out['status'],'oversized_body')
    def test_explicit_profile_allows_roughly_400kb(self):
        raw=rss(padding=385000)
        out=inspect_feed_bytes(raw,now=NOW,max_bytes=1000000)
        self.assertEqual(out['status'],'usable_dated_feed')
        candidates=extract_candidates(raw,feed_url='https://shafaq.com/ar?rss=1',observed_at=NOW,max_bytes=1000000)
        self.assertEqual(candidates['candidate_count'],1)
    def test_extended_parse_bounded_to_1mb(self):
        with self.assertRaises(ValueError):
            inspect_feed_bytes(rss(),now=NOW,max_bytes=1000001)
    def test_shafaq_uses_direct_https_feed_not_redirecting_legacy_page(self):
        # Legacy /ar?rss=1 redirects through HTTP, which must stay blocked.
        self.assertEqual(profile_for('ar-s026')['url'], 'https://shafaq.com/rss/ar')

    def test_regional_adapter_refuses_network_without_opt_in(self):
        with self.assertRaisesRegex(ValueError,'network_opt_in_required'):
            probe_regional_source('ar-s026',now=NOW)
    def test_known_large_source_is_metadata_only_and_not_publishable(self):
        out=probe_regional_source('ar-s026',now=NOW,fetcher=lambda url,timeout: rss(padding=385000))
        self.assertEqual(out['status'],'usable_dated_feed')
        self.assertEqual(out['source_id'],'ar-s026')
        self.assertEqual(out['language'],'ar')
        self.assertEqual(out['candidate_count'],1)
        self.assertTrue(out['arabic_original_language_candidate'])
        self.assertFalse(out['delivery_authorized'])
        self.assertFalse(out['live_http_performed'])
    def test_english_registered_arabic_stream_is_not_native_arabic(self):
        out=probe_regional_source('ar-s017',now=NOW,fetcher=lambda url,timeout: rss(lang='en',padding=350000))
        self.assertEqual(out['language'],'en')
        self.assertFalse(out['arabic_original_language_candidate'])
        self.assertFalse(out['delivery_authorized'])
    def test_arabic_script_does_not_override_explicit_persian_language(self):
        profile=profile_for('ar-s019')
        self.assertEqual(profile['language'],'fa')
        self.assertFalse(profile['arabic_native'])
    def test_english_feed_masquerading_arabic_is_not_admitted(self):
        out=probe_regional_source('ar-s081',now=NOW,fetcher=lambda url,timeout: rss(lang='en',padding=230000))
        self.assertEqual(out['status'],'script_mismatch')
        self.assertFalse(out['arabic_original_language_candidate'])
    def test_unknown_source_refused(self):
        with self.assertRaisesRegex(ValueError,'source_not_allowlisted'):
            probe_regional_source('ar-s999',now=NOW,fetcher=lambda url,timeout: b'')
    def test_oversized_response_not_accepted(self):
        out=probe_regional_source('ar-s026',now=NOW,fetcher=lambda url,timeout: rss(padding=1000100))
        self.assertEqual(out['status'],'oversized_body')
        self.assertEqual(out['candidate_count'],0)

if __name__=='__main__':unittest.main()
