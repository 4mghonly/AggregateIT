"""B42 offline TDD: production-audit parity, freshness and publisher separation."""
import unittest
from v2_b42_somalia_feed_probe import assess_feed,probe_one,roster_summary,CANDIDATES

OBSERVED='2026-10-27T06:00:00+00:00'

def xml(pub='Tue, 27 Oct 2026 04:00:00 GMT', num=4):
    items="".join(
      '<item><title>Somalia regional report '+str(i)+'</title>'
      '<link>https://example.org/story/'+str(i)+'</link>'
      '<pubDate>'+pub+'</pubDate></item>' for i in range(num))
    return ('<?xml version="1.0"?><rss version="2.0"><channel><title>Regional</title>'
            +items+'</channel></rss>').encode("utf8")

class SomaliaCandidateTests(unittest.TestCase):
    def test_recent_rss_genuine_articles_qualify(self):
        r=assess_feed(xml(),observed_at=OBSERVED)
        self.assertEqual(r['feed_entries'],4)
        self.assertEqual(r['recent_72h'],4)
        self.assertEqual(r['distinct_https_article_links'],4)
        self.assertTrue(r['recent_feed_candidate'])
    def test_old_feed_not_candidate_despite_production_audit_compatible(self):
        r=assess_feed(xml(pub='Tue, 20 Oct 2026 04:00:00 GMT'),observed_at=OBSERVED)
        self.assertTrue(r['production_audit_compatible'])
        self.assertFalse(r['recent_feed_candidate'])
    def test_empty_and_html_not_compatible(self):
        for raw in [b'<html><body>Not feed</body></html>',b'<rss><channel/></rss>']:
            r=assess_feed(raw,observed_at=OBSERVED)
            self.assertFalse(r['production_audit_compatible'])
    def test_bounded_transport_and_no_raw_headlines_in_receipt(self):
        info=CANDIDATES[3]
        class Fetch:
            def __init__(self):self.calls=0
            def __call__(self,*args,**kwargs):
                self.calls+=1
                self.kw=kwargs
                return {'status':200,'content_type':'application/rss+xml',
                        'final_url':args[0],'body':xml()}
        fetch=Fetch()
        row=probe_one(info,observed_at=OBSERVED,transport=fetch)
        self.assertEqual(fetch.calls,1)
        self.assertTrue(row['recent_feed_candidate'])
        self.assertEqual(row['status'],'RECENT_CANDIDATE')
        self.assertEqual(fetch.kw['max_bytes'],1_000_000)
        self.assertNotIn('Somalia regional report',str(row))
    def test_fail_closed_on_404(self):
        from urllib.error import HTTPError
        def failed(*args,**kwargs):
            raise HTTPError(args[0],404,'gone',{},None)
        row=probe_one(CANDIDATES[2],observed_at=OBSERVED,transport=failed)
        self.assertEqual(row['status'],'HOLD')
        self.assertEqual(row['failure_class'],'http_404')
    def test_count_unique_publishers_not_urls(self):
        rows=[{'candidate_id':item[0],'publisher_family':item[2],
               'name':item[1],'feed_url':item[4],'status':'HOLD',
               'production_audit_compatible':False,'recent_feed_candidate':False}
              for item in CANDIDATES]
        for label in ('sonna-ar-retry','sonna-en'):
            row=next(r for r in rows if r['candidate_id']==label)
            row.update(status='RECENT_CANDIDATE',production_audit_compatible=True,
                       recent_feed_candidate=True,recent_72h=6,feed_entries=9)
        r=roster_summary(rows)
        self.assertEqual(r['distinct_recent_publisher_families'],1)
        self.assertFalse(r['source_registered'])
        self.assertFalse(r['can_release'])
    def test_invalid_time_fails_closed(self):
        with self.assertRaises(ValueError):
            assess_feed(xml(),observed_at='2026-10-27T06:00:00')
if __name__=='__main__':unittest.main()
