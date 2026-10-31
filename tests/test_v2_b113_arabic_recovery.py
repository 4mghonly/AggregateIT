"""B113 offline regressions for verified Arabic recovery defects."""
import unittest
from unittest.mock import patch
from v2_article_body_gate import classify_geography
from v2_b46_live_editorial_runner import run,FEEDS

AT="2026-10-29T09:00:00+00:00"
URL_PRIMARY="https://www.aljazeera.net/news/2026/10/29/example"
URL_FALLBACK="https://www.france24.com/ar/20261029-sudan-security-update"
PRIMARY_TITLE="قرار حكومي جديد بشأن الخدمات في السودان"
FALLBACK_TITLE="هجوم على منشأة حيوية"
PRIMARY_TEXT=("أعلنت إدارة السودان إصدار قرار حكومي جديد يتعلق بالخدمات العامة، "
              "وأوضحت تفاصيل الاجتماع الذي ناقش خطط التطوير المحلية.")
FALLBACK_TEXT=("أكدت السلطات في السودان وقوع هجوم على منشأة حيوية، "
               "وقالت إن الفرق المختصة بدأت التحقيق في ملابسات الهجوم.")
EMPTY=b'<rss version="2.0"><channel><title>Empty</title></channel></rss>'

def feed(title,url):
 return ('<rss version="2.0"><channel><title>News</title><item><title>'+title+
         '</title><link>'+url+'</link><pubDate>Thu, 29 Oct 2026 08:00:00 GMT</pubDate>'+
         '</item></channel></rss>').encode('utf8')

def fetch(url,**kw):
 if url=="https://rss.dw.com/rdf/rss-en-world":body=EMPTY
 elif url=="https://www.france24.com/ar/rss":body=feed(FALLBACK_TITLE,URL_FALLBACK)
 elif url==URL_PRIMARY:body=('<div class="wysiwyg--all-content"><p>'+PRIMARY_TEXT+'</p><p>'+PRIMARY_TEXT+'</p></div>').encode('utf8')
 elif url==URL_FALLBACK:body=('<article><p>'+FALLBACK_TEXT+'</p><p>'+FALLBACK_TEXT+'</p></article>').encode('utf8')
 else:raise AssertionError("Unexpected injected URL: "+url)
 return {"body":body,"status":200,"final_url":url,"content_type":"text/html"}

class ArabicRecoveryTests(unittest.TestCase):
 def test_one_grounded_country_in_lead_recovers_countryless_security_headline(self):
  result=classify_geography(FALLBACK_TITLE,FALLBACK_TEXT+"\n\n"+FALLBACK_TEXT,language="ar")
  self.assertEqual(result["subject_country"],"SD")
  self.assertEqual(result["classification_status"],"article_lead_single_explicit_country")
 def test_two_countries_in_lead_are_not_guessed(self):
  with self.assertRaisesRegex(ValueError,"ambiguous_geography"):
   classify_geography(FALLBACK_TITLE,"تقارير من السودان واليمن حول الوضع الأمني."*3,language="ar")
 def test_headline_country_still_requires_body_corroboration(self):
  with self.assertRaisesRegex(ValueError,"country_not_supported_by_article_body"):
   classify_geography("هجوم في اليمن","أكدت السلطات في السودان أن الحادث قيد التحقيق."*3,language="ar")
 def test_primary_non_security_does_not_block_security_fallback(self):
  snapshots={p:{"feed_url":url,"body":feed(PRIMARY_TITLE,URL_PRIMARY) if p=="arabic" else EMPTY}
             for p,url in FEEDS}
  with patch("market.load_market_pulse",return_value={}),patch("market.load_macro_pulse",return_value={}):
   result=run(rss_snapshots=snapshots,observed_at=AT,fetch=fetch)
  self.assertTrue(result["source_recovery"]["arabic"]["fallback_attempted"])
  self.assertEqual(result["source_recovery"]["arabic"]["selected_publisher"],"ar-s004")
  self.assertEqual(result["editorial"]["products"]["arabic"]["story_count"],1)
  self.assertGreaterEqual(result["source_attempts"]["arabic"]["editorial_relevance_precheck_rejections"],1)
  self.assertFalse(result["can_release"])
if __name__=="__main__":unittest.main()
