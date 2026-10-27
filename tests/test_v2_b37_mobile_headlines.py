"""B37 genuine-headline-only mobile preview: strict language, provenance and no-send."""
import unittest
from v2_b37_mobile_headlines import render_source_watch_html

NOW='2026-10-27T06:00:00+00:00'

def row(title, url='https://example.org/story/1'):
    return {'title':title,'article_url':url,'source_feed_url':'https://example.org/rss',
            'published_at':NOW,'candidate_id':'candidate'}

class MobileWatchTests(unittest.TestCase):
    def test_english_valid_bounded_and_no_evidence_claim(self):
        result=render_source_watch_html('english',[row('Regional world headline')],NOW)
        self.assertEqual(result['shown'],1)
        self.assertIn('lang="en" dir="ltr"',result['html'])
        self.assertIn('width=device-width',result['html'])
        self.assertIn('Regional world headline',result['html'])
        self.assertNotIn('Article facts verified',result['html'])
        self.assertFalse(result['delivery_authorized'])

    def test_arabic_original_script(self):
        result=render_source_watch_html('arabic',[row('تطورات إقليمية جديدة'),row('English unrelated headline')],NOW)
        self.assertEqual(result['shown'],1)
        self.assertEqual(result['script_filtered'],1)
        self.assertIn('lang="ar" dir="rtl"',result['html'])
        self.assertNotIn('English unrelated headline',result['html'])

    def test_html_injection_escaped_and_bad_link_rejected(self):
        result=render_source_watch_html('english',[row('Breaking <script>alert(1)</script>')],NOW)
        self.assertNotIn('<script>',result['html'])
        self.assertIn('&lt;script&gt;',result['html'])
        with self.assertRaises(ValueError):
            render_source_watch_html('english',[row('Headline valid', 'http://example.org/x')],NOW)

    def test_sparse_feed_displays_gap_instead_of_invention(self):
        r=render_source_watch_html('arabic',[],NOW)
        self.assertEqual(r['shown'],0)
        self.assertIn('لا توجد عناوين',r['html'])
        self.assertFalse(r['can_publish'])

    def test_bounded_selection(self):
        r=render_source_watch_html('english',[row(f'Headline number {i}',f'https://example.org/story/{i}') for i in range(50)],NOW)
        self.assertEqual(r['shown'],6)
        self.assertEqual(r['excluded_over_budget'],44)

if __name__=='__main__': unittest.main()
