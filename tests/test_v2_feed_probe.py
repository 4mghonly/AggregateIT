"""Offline RSS/Atom feed-compatibility probes and URL safety tests."""
import unittest
from v2_feed_probe import inspect_feed_bytes,bounded_fetch
NOW='2026-10-24T10:00:00+04:00'
class FeedProbeTests(unittest.TestCase):
    def test_recent_rss(self):
        raw=b'<?xml version="1.0"?><rss version="2.0"><channel><title>Example</title><item><title>A</title><pubDate>Sat, 24 Oct 2026 03:00:00 GMT</pubDate></item></channel></rss>'
        r=inspect_feed_bytes(raw,now=NOW)
        self.assertEqual(r['status'],'usable_dated_feed')
        self.assertEqual(r['recent_count'],1)
        self.assertFalse(r['article_bodies_retained'])
    def test_stale_is_not_fresh(self):
        r=inspect_feed_bytes(b'<rss><channel><item><pubDate>Mon, 14 Sep 2026 03:00:00 GMT</pubDate></item></channel></rss>',now=NOW)
        self.assertEqual(r['status'],'stale_feed')
    def test_html_is_not_feed(self):
        self.assertEqual(inspect_feed_bytes(b'<html></html>',now=NOW)['status'],'not_a_feed')
    def test_bad_xml(self):
        self.assertEqual(inspect_feed_bytes(b'<rss><broken',now=NOW)['status'],'invalid_xml')
    def test_atom_date(self):
        r=inspect_feed_bytes(b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><updated>2026-10-24T03:00:00Z</updated></entry></feed>',now=NOW)
        self.assertEqual(r['status'],'usable_dated_feed')
    def test_undated_is_not_recent(self):
        self.assertEqual(inspect_feed_bytes(b'<rss><channel><item/></channel></rss>',now=NOW)['status'],'undated_feed')
    def test_oversized_body_refused(self):
        self.assertEqual(inspect_feed_bytes(b'a'*250000,now=NOW)['status'],'oversized_body')
    def test_private_http_and_non_http_refused_before_request(self):
        for u in ('http://127.0.0.1/rss','https://localhost/rss','https://169.254.169.254/latest','file:///etc/passwd'):
            with self.assertRaises(ValueError):bounded_fetch(u)

if __name__=='__main__':unittest.main()
