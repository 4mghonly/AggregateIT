"""Replacement integration acceptance: actual secondary article bytes reach the editorial product."""
import unittest
from v2_b46_live_editorial_runner import run, FEEDS
from v2_b46_live_editorial import _verify_source_candidate

AT="2026-10-29T09:00:00+00:00"
EMPTY=b'<rss version="2.0"><channel><title>Empty</title></channel></rss>'
EN_URL="https://www.dw.com/en/somalia-security-update/a-123456"
AR_URL="https://www.france24.com/ar/20261029-somalia-security-update"
EN_TITLE="Somalia security officials outline latest measures"
AR_TITLE="مباحثات دبلوماسية في الصومال بشأن العلاقات الإقليمية"
EN_BODY=("Officials in Somalia said their security teams met with regional representatives "
         "to discuss the security situation and review public statements about the measures.")
AR_BODY=("أكد مسؤولون في الصومال عقد مباحثات دبلوماسية مع ممثلين إقليميين "
         "لبحث التطورات السياسية ومناقشة بيانات الاجتماع المتعلق بالعلاقات الإقليمية.")
def snapshots():
 return {p:{"feed_url":url,"body":EMPTY} for p,url in FEEDS}
def feed(title,url):
 return ('<rss version="2.0"><channel><title>News</title><item><title>'+title+
         '</title><link>'+url+'</link><pubDate>Thu, 29 Oct 2026 08:00:00 GMT</pubDate>'+
         '</item></channel></rss>').encode("utf8")
def fake_fetch(url,**kwargs):
 if url=="https://rss.dw.com/rdf/rss-en-world":body=feed(EN_TITLE,EN_URL)
 elif url=="https://www.france24.com/ar/rss":body=feed(AR_TITLE,AR_URL)
 elif url==EN_URL:body=('<article><p>'+EN_BODY+'</p><p>'+EN_BODY+'</p></article>').encode()
 elif url==AR_URL:body=('<article><p>'+AR_BODY+'</p><p>'+AR_BODY+'</p></article>').encode()
 else:raise AssertionError("unexpected_fetch:"+url)
 return {"body":body,"status":200,"final_url":url,"content_type":"text/html"}

class ReplacementPipelineTests(unittest.TestCase):
 def test_primary_blackout_recovers_two_real_source_identities_into_editorial(self):
  result=run(rss_snapshots=snapshots(),observed_at=AT,fetch=fake_fetch)
  self.assertEqual(result["editorial"]["admitted_articles"],2)
  self.assertEqual({x["source_id"] for x in result["editorial"]["evidence_hashes"]},{"en-018","ar-s004"})
  for p,secondary in (("english","dw-en"),("arabic","ar-s004")):
   self.assertEqual(result["source_recovery"][p]["selected_publisher"],secondary)
   self.assertTrue(result["source_recovery"][p]["fallback_used"])
   self.assertEqual(result["editorial"]["products"][p]["story_count"],1)
  self.assertFalse(result["can_release"])
  self.assertFalse(result["discord_sent"])
 def test_arabic_article_body_is_detected_without_matching_english(self):
  from v2_article_body_gate import extract_body
  content=('<article><p>'+AR_BODY+'</p><p>'+AR_BODY+'</p></article>').encode("utf8")
  body=extract_body(content,source_url=AR_URL,language="ar")
  self.assertIn("الصومال",body["original_text"])
  with self.assertRaisesRegex(ValueError,"body_script_mismatch"):
   extract_body(content,source_url=AR_URL,language="en")
 def test_unregistered_publisher_still_refused(self):
  with self.assertRaisesRegex(ValueError,"source_identity_mismatch"):
   _verify_source_candidate({"product":"english","source_id":"en-unknown",
                            "article_url":EN_URL,"title":EN_TITLE})
 def test_secondary_identity_cannot_use_primary_host(self):
  with self.assertRaisesRegex(ValueError,"wrong_article_publisher"):
   _verify_source_candidate({"product":"english","source_id":"en-018",
                            "article_url":"https://www.bbc.com/news/articles/foo","title":EN_TITLE})
if __name__=="__main__":unittest.main()
