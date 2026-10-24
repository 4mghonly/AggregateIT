"""Synthetic, feed-metadata-only item normalization tests."""
import unittest
from v2_feed_items import extract_candidates
NOW='2026-10-24T03:30:00+04:00'
F='https://news.example.org/rss'

class FeedItemTests(unittest.TestCase):
    def rss(self,items):
        return ('<rss><channel>'+items+'</channel></rss>').encode()
    def test_rss_yields_recent_candidates_not_facts(self):
        b=self.rss('<item><title>Testing simulated regional news</title><link>https://publisher.example.org/news/1</link><pubDate>Fri, 23 Oct 2026 23:00:00 GMT</pubDate></item>')
        r=extract_candidates(b,feed_url=F,observed_at=NOW)
        self.assertEqual(r['candidate_count'],1)
        self.assertFalse(r['can_publish'])
        self.assertFalse(r['items'][0]['article_body_observed'])
        self.assertEqual(r['items'][0]['editorial_admission'],'held_pending_article_evidence')
    def test_atom_with_alternate_link(self):
        b=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Testing synthetic atom story</title><link rel="alternate" href="https://publisher.example.org/story"/><updated>2026-10-23T23:00:00+00:00</updated></entry></feed>'
        self.assertEqual(extract_candidates(b,feed_url=F,observed_at=NOW)['candidate_count'],1)
    def test_duplicate_links_within_feed_are_not_independent(self):
        row='<item><title>Same test observation headline</title><link>https://publisher.example.org/a</link><pubDate>Fri, 23 Oct 2026 23:00:00 GMT</pubDate></item>'
        r=extract_candidates(self.rss(row*2),feed_url=F,observed_at=NOW)
        self.assertEqual(r['candidate_count'],1)
        self.assertEqual(r['rejected']['duplicate_link'],1)
    def test_stale_and_undated_are_held(self):
        row='<item><title>Stale synthetic test story</title><link>https://publisher.example.org/a</link><pubDate>Fri, 16 Oct 2026 23:00:00 GMT</pubDate></item>'
        r=extract_candidates(self.rss(row),feed_url=F,observed_at=NOW)
        self.assertEqual(r['candidate_count'],0)
        self.assertEqual(r['rejected']['missing_or_stale_date'],1)
    def test_unsafe_article_link_rejected(self):
        row='<item><title>Testing simulated local URL</title><link>https://localhost/admin</link><pubDate>Fri, 23 Oct 2026 23:00:00 GMT</pubDate></item>'
        self.assertEqual(extract_candidates(self.rss(row),feed_url=F,observed_at=NOW)['rejected']['invalid_link'],1)
    def test_budget_bounded(self):
        rows=''.join(f'<item><title>Simulated news item number {i}</title><link>https://publisher.example.org/{i}</link><pubDate>Fri, 23 Oct 2026 23:00:00 GMT</pubDate></item>' for i in range(5))
        r=extract_candidates(self.rss(rows),feed_url=F,observed_at=NOW,max_items=2)
        self.assertEqual(r['candidate_count'],2)
        self.assertEqual(r['rejected']['over_budget'],3)
    def test_invalid_xml_and_feed_url_refused(self):
        with self.assertRaises(ValueError):extract_candidates(b'<html>',feed_url=F,observed_at=NOW)
        with self.assertRaises(ValueError):extract_candidates(b'',feed_url='https://127.0.0.1/rss',observed_at=NOW)

if __name__=='__main__':unittest.main()
