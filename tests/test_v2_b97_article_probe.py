import unittest
from v2_b97_article_probe import probe_articles
class ArticleProbeTests(unittest.TestCase):
 def test_non_article_html_is_held(self):
  def fetch(url,**kw):return {"body":b"<html><body>empty</body></html>","status":200,"final_url":url}
  p={"publisher_id":"dw-en","language":"english","article_hosts":["www.dw.com"],"article_urls":["https://www.dw.com/en/story/a-1"]}
  r=probe_articles([p],fetch=fetch)
  self.assertEqual(r["sources"][0]["status"],"HOLD_NO_VALIDATED_ARTICLE_BODY")
  self.assertFalse(r["can_release"])
 def test_reject_host_mismatch(self):
  p={"publisher_id":"dw-en","language":"english","article_hosts":["www.dw.com"],"article_urls":["https://other.example/article"]}
  with self.assertRaises(ValueError):probe_articles([p])
 def test_empty_urls_held(self):
  p={"publisher_id":"bbc-ar","language":"arabic","article_hosts":["www.bbc.com"],"article_urls":[]}
  self.assertEqual(probe_articles([p])["sources"][0]["status"],"HOLD_NO_ARTICLE_URLS")
if __name__=="__main__":unittest.main()
