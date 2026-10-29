import unittest
from v2_b97_live_source_probe import probe
class SourceProbeTests(unittest.TestCase):
 def test_failed_feed_does_not_admit_publisher(self):
  def broken(url,**kwargs):raise TimeoutError("offline")
  r=probe([{"publisher_id":"dw-en","language":"english","feed_url":"https://rss.dw.com/rdf/rss-en-world","article_hosts":["www.dw.com"]}],fetch=broken)
  self.assertEqual(r["sources"][0]["status"],"HOLD_FEED_FETCH_FAILED")
  self.assertFalse(r["can_release"])
 def test_live_feed_alone_cannot_admit_article_publisher(self):
  def feed(url,**kwargs):return {"status":200,"body":b'<rss><channel><title>Test</title><item><title>Jordan update</title><link>https://www.dw.com/en/story/a-123</link></item></channel></rss>',"final_url":url,"content_type":"application/rss+xml"}
  r=probe([{"publisher_id":"dw-en","language":"english","feed_url":"https://rss.dw.com/rdf/rss-en-world","article_hosts":["www.dw.com"]}],fetch=feed)
  self.assertEqual(r["sources"][0]["status"],"HOLD_ARTICLE_BODY_GATE_NOT_VALIDATED")
  self.assertFalse(r["sources"][0]["onboarded"])
 def test_reject_private_feed(self):
  with self.assertRaises(ValueError):probe([{"publisher_id":"x","language":"english","feed_url":"http://127.0.0.1/rss","article_hosts":["localhost"]}])
if __name__=="__main__":unittest.main()
