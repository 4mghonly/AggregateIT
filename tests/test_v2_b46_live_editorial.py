"""B46 real article-byte -> B3 evidence -> B4 held newsroom, fail-closed."""
import unittest
from datetime import datetime,timedelta,timezone
from v2_b46_live_editorial import compile_captured_articles, _verify_source_candidate

NOW="2026-10-27T08:00:00+00:00"
SLOT="2026-10-27T12:00:00+04:00"
EN_TITLE="Somalia security officials outline latest measures"
AR_TITLE="مباحثات دبلوماسية في الصومال بشأن العلاقات الإقليمية"
EN_TEXT=("Officials in Somalia said their security teams met with regional representatives "
         "to discuss the security situation and review public statements about the measures.")
AR_TEXT=("أكد مسؤولون في الصومال عقد مباحثات دبلوماسية مع ممثلين إقليميين "
         "لبحث التطورات السياسية ومناقشة بيانات الاجتماع المتعلق بالعلاقات الإقليمية.")
def en():
    return {'product':'english','source_id':'en-001',
       'article_url':'https://www.bbc.com/news/articles/c123-example',
       'title':EN_TITLE,'published_at':'2026-10-27T07:00:00+00:00',
       'html_bytes':('<article><p>'+EN_TEXT+'</p><p>'+EN_TEXT+
                     '</p></article>').encode('utf8')}
def ar():
    return {'product':'arabic','source_id':'ar-s003',
       'article_url':'https://www.aljazeera.net/news/2026/10/27/example',
       'title':AR_TITLE,'published_at':'2026-10-27T07:00:00+00:00',
       'html_bytes':('<div class="wysiwyg--all-content"><p>'+AR_TEXT+
                     '</p><p>'+AR_TEXT+'</p></div>').encode('utf8')}

class B46LiveEditorialTests(unittest.TestCase):
    def test_genuine_article_bytes_pass_through_existing_evidence_and_editorial(self):
        r=compile_captured_articles([en(),ar()],as_of=NOW,slot_id=SLOT)
        self.assertEqual(r['admitted_articles'],2)
        self.assertEqual(r['products']['english']['story_count'],1)
        self.assertEqual(r['products']['arabic']['story_count'],1)
        self.assertEqual(r['products']['english']['newsroom']['stories'][0]['topic'],'security')
        self.assertEqual(r['products']['arabic']['newsroom']['stories'][0]['topic'],'diplomacy')
        self.assertEqual(r['products']['english']['newsroom']['market_data_status'],'unavailable')
        self.assertEqual(r['products']['arabic']['newsroom']['market_data_status'],'not_applicable')
        self.assertEqual(r['products']['arabic']['newsroom']['naysayer_status'],'insufficient_evidence')
        self.assertNotEqual(r['products']['english']['newsroom']['stories'][0]['excerpt_id'],'')
        self.assertFalse(r['can_send'])
        self.assertFalse(r['semantic_cross_language_event_merge_verified'])
        self.assertFalse(r['live_model_translation_verified'])
    def test_source_identity_and_article_host_attestation_checked(self):
        item=en();item['source_id']='ar-s003'
        with self.assertRaisesRegex(ValueError,'source_identity'):
            compile_captured_articles([item],as_of=NOW,slot_id=SLOT)
        item=en();item['article_url']='https://evil.example.org/read'
        with self.assertRaises(ValueError):
            compile_captured_articles([item],as_of=NOW,slot_id=SLOT)
    def test_article_body_cannot_be_a_headline_only_feed(self):
        item=en();item['html_bytes']=b'<rss><item><title>Somalia</title></item></rss>'
        r=compile_captured_articles([item],as_of=NOW,slot_id=SLOT)
        self.assertEqual(r['admitted_articles'],0)
        self.assertEqual(r['products']['english']['story_count'],0)
        self.assertEqual(r['held_reasons']['article_body_container_missing'],1)
    def test_identical_url_not_double_counted(self):
        r=compile_captured_articles([en(),en()],as_of=NOW,slot_id=SLOT)
        self.assertEqual(r['admitted_articles'],1)
        self.assertEqual(r['held_reasons']['repeated_canonical_article_url'],1)
    def test_tracking_query_alias_does_not_double_count(self):
        one=en();two=en()
        two['article_url']=one['article_url']+'?utm_source=mail'
        r=compile_captured_articles([one,two],as_of=NOW,slot_id=SLOT)
        self.assertEqual(r['admitted_articles'],1)
        self.assertEqual(r['held_reasons']['repeated_canonical_article_url'],1)

    def test_missing_prior_baseline_stays_unknown_not_new(self):
        r=compile_captured_articles([en()],as_of=NOW,slot_id=SLOT)
        s=r['products']['english']['newsroom']['stories'][0]
        self.assertEqual(s['change'],'unknown_no_baseline')
        r2=compile_captured_articles([en()],as_of=NOW,slot_id=SLOT,previous_versions={})
        self.assertEqual(r2['products']['english']['newsroom']['stories'][0]['change'],'unknown_no_baseline')
        self.assertTrue(r2['unattested_previous_versions_ignored'])
        self.assertFalse(r2['prior_baseline_authenticated'])
    def test_stale_article_is_withheld(self):
        item=en();item['published_at']='2026-10-20T07:00:00+00:00'
        r=compile_captured_articles([item],as_of=NOW,slot_id=SLOT)
        self.assertEqual(r['admitted_articles'],0)
        self.assertEqual(r['held_reasons']['stale_or_future_article'],1)
    def test_bad_utc_or_invalid_item_fails_closed(self):
        with self.assertRaises(ValueError):compile_captured_articles([en()],as_of='2026-10-27T08:00:00',slot_id=SLOT)
        with self.assertRaises(ValueError):compile_captured_articles([en()],as_of=NOW,slot_id='2026-10-27T12:00:00')
        with self.assertRaises(ValueError):compile_captured_articles([en()]*21,as_of=NOW,slot_id=SLOT)
    def test_explicit_wrong_topic_or_financial_in_arabic_cannot_enter(self):
        r=compile_captured_articles([ar()],as_of=NOW,slot_id=SLOT)
        self.assertTrue(all(s['topic']!='markets' for s in r['products']['arabic']['newsroom']['stories']))
        self.assertEqual(r['products']['arabic']['newsroom']['market_observations'],[])
    def test_metadata_output_does_not_persist_publisher_body(self):
        r=compile_captured_articles([en()],as_of=NOW,slot_id=SLOT)
        from v2_b46_live_editorial import metrics_only
        sanitized=metrics_only(r)
        self.assertNotIn('Officials in Somalia',str(sanitized))
        self.assertNotIn('quote',str(sanitized))
        self.assertFalse(sanitized['model_called'])
        self.assertFalse(sanitized['discord_sent'])
if __name__=='__main__':unittest.main()
