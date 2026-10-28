import unittest
from datetime import datetime,timezone
from audit import _rss_freshness

class RSSFreshnessTests(unittest.TestCase):
    def test_fresh_stale_undated_are_separate(self):
        xml='''<rss version="2.0"><channel><title>Example</title>
        <item><title>fresh</title><pubDate>Wed, 28 Oct 2026 12:00:00 GMT</pubDate></item>
        <item><title>stale</title><pubDate>Mon, 19 Oct 2026 12:00:00 GMT</pubDate></item>
        <item><title>undated</title></item>
        </channel></rss>'''
        now=datetime(2026,10,28,16,tzinfo=timezone.utc).timestamp()
        r=_rss_freshness(xml,now=now)
        self.assertEqual((r["dated_items"],r["fresh_48h_items"],r["undated_items"]),(2,1,1))
    def test_future_dated_is_not_fresh(self):
        xml='''<rss version="2.0"><channel><title>Example</title>
        <item><title>future</title><pubDate>Thu, 29 Oct 2026 12:00:00 GMT</pubDate></item>
        </channel></rss>'''
        now=datetime(2026,10,28,16,tzinfo=timezone.utc).timestamp()
        self.assertEqual(_rss_freshness(xml,now=now)["fresh_48h_items"],0)
if __name__=="__main__":unittest.main()
