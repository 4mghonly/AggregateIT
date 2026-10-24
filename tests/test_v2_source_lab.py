"""Dry-run first, one bounded source observation per request, never publishing."""
import unittest
from urllib.error import HTTPError

from v2_source_lab import probe_source_batch

NOW='2026-10-24T06:00:00+04:00'
RSS=(b'<rss><channel><item><title>Test regional headline for observations</title>'
     b'<link>https://publisher.example.com/story/1</link>'
     b'<pubDate>Fri, 23 Oct 2026 23:00:00 GMT</pubDate></item></channel></rss>')

class SourceLabTests(unittest.TestCase):
    def test_requires_explicit_permission_before_any_network(self):
        with self.assertRaisesRegex(ValueError, 'network_opt_in_required'):
            probe_source_batch([{'source_id':'s1','url':'https://publisher.example.com/rss'}],now=NOW)

    def test_one_fetch_produces_metadata_only_with_held_candidates(self):
        seen=[]
        def fetcher(url, *, timeout):
            seen.append((url,timeout))
            return RSS
        result=probe_source_batch([{'source_id':'s1','url':'https://publisher.example.com/rss'}],now=NOW,fetcher=fetcher)
        self.assertEqual(len(seen),1)
        self.assertEqual(result['sources'][0]['status'],'usable_dated_feed')
        self.assertEqual(result['sources'][0]['candidate_count'],1)
        self.assertFalse(result['sources'][0]['publishable'])
        self.assertFalse(result['source_independence_verified'])
        self.assertFalse(result['production_promoted'])
        self.assertNotIn('body',str(result))

    def test_403_is_downgraded_without_failed_batch(self):
        def fetcher(url, *, timeout):
            raise HTTPError(url,403,'Forbidden',{},None)
        out=probe_source_batch([{'source_id':'s1','url':'https://publisher.example.com/feed'}],now=NOW,fetcher=fetcher)
        self.assertEqual(out['sources'][0]['status'],'http_403')
        self.assertEqual(out['sources'][0]['candidate_count'],0)

    def test_html_is_not_mislabeled_rss(self):
        out=probe_source_batch([{'source_id':'s1','url':'https://publisher.example.com/home'}],now=NOW,fetcher=lambda url,timeout:b'<html><body>Hello</body></html>')
        self.assertEqual(out['sources'][0]['status'],'not_a_feed')
        self.assertEqual(out['sources'][0]['candidate_count'],0)

    def test_rejects_ssrf_before_calling_fetcher(self):
        calls=[]
        out=probe_source_batch([{'source_id':'s1','url':'https://127.1/feed'}],now=NOW,fetcher=lambda *a,**kw:calls.append(True))
        self.assertEqual(calls,[])
        self.assertEqual(out['sources'][0]['status'],'unsafe_source_url')

    def test_batch_cap(self):
        src=[{'source_id':f's{i}','url':f'https://host{i}.example.com/feed'} for i in range(14)]
        with self.assertRaisesRegex(ValueError,'source_budget_exceeded'):
            probe_source_batch(src,now=NOW,fetcher=lambda *a,**kw:RSS)

    def test_duplicates_not_counted_twice_as_independent(self):
        src=[{'source_id':'a','url':'https://publisher.example.com/feed'},
             {'source_id':'b','url':'https://publisher.example.com/feed'}]
        count=[]
        out=probe_source_batch(src,now=NOW,fetcher=lambda *a,**kw: (count.append(1) or RSS))
        self.assertEqual(len(count),1)
        self.assertEqual(out['sources'][1]['status'],'duplicate_url_not_probed')
        self.assertFalse(out['source_independence_verified'])

if __name__=='__main__':unittest.main()

class SourceLabCliTests(unittest.TestCase):
    def test_cli_without_live_is_manifest_only(self):
        import subprocess, sys
        cmd=[sys.executable,'-B','-m','v2_source_lab','--source','bbc=https://feeds.bbci.co.uk/news/world/rss.xml']
        r=subprocess.run(cmd,text=True,capture_output=True,timeout=7)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('"live_http_performed": false',r.stdout)
        self.assertIn('"status": "dry_run_only"',r.stdout)
