"""Authentic-web excerpt handover -> B3 ledger -> B4/B publication contracts.

Fixtures use invented publishers; no public source text is fabricated for the live sample.
"""
import json
import unittest
from pathlib import Path
from v2_external_capture import compile_web_captures

REGISTRY=json.loads((Path(__file__).resolve().parents[1]/'config/v2/source_registry.json').read_text(encoding='utf8'))
SLOT='2026-10-24T06:00:00+04:00'
OBS='2026-10-24T06:22:00+04:00'

def article(stream='english'):
    en=stream=='english'
    return {
        'source_id':'en-107' if en else 'ar-s116',
        'article_url':('https://www.mediaoffice.abudhabi/en/government-affairs/tested-article'
                      if en else 'https://www.mediaoffice.abudhabi/ar/government-affairs/tested-article'),
        'verbatim_excerpt':('The two parties discussed cooperation between their countries.' if en
                            else 'ناقش الطرفان العلاقات الثنائية وسبل تعزيز التعاون بين البلدين.'),
        'original_language':'en' if en else 'ar',
        'published_date':'2026-10-23',
        'capture_method':'public_web_page_read_manual_transfer',
        'explicit_event_key':'diplomatic-test-event-23oct26',
        'region':'gcc','subject_country':'AE',
        'topic':'geopolitics' if en else 'diplomacy','priority':80,
    }

class WebCaptureChainTests(unittest.TestCase):
    def run_chain(self, inputs):
        return compile_web_captures(inputs,registry=REGISTRY,observed_at=OBS,
                                    slot_id=SLOT)
    def test_two_languages_reach_valid_excerpt_and_compiler_without_publish(self):
        r=self.run_chain([article('english'),article('arabic')])
        self.assertEqual(r['capture_count'],2)
        self.assertEqual(r['products']['english']['stories'][0]['source_id'],'en-107')
        self.assertEqual(r['products']['arabic']['stories'][0]['source_id'],'ar-s116')
        self.assertEqual(r['products']['arabic']['market_data_status'],'not_applicable')
        self.assertEqual(r['products']['english']['market_data_status'],'unavailable')
        self.assertTrue(r['products']['english']['stories'][0]['excerpt_id'].startswith('exc_'))
        self.assertEqual(r['products']['arabic']['stories'][0]['quote'],article('arabic')['verbatim_excerpt'])
        self.assertEqual(r['source_provenance_status'],'web_text_excerpt_observed_not_independently_verified')
        self.assertFalse(r['web_collector_ran'])
        self.assertFalse(r['discord_sent'])
        self.assertFalse(r['llm_called'])
        self.assertFalse(r['delivery_authorized'])
    def test_registered_source_host_must_match_exact_verified_registry_identity(self):
        a=article();a['article_url']='https://impostor.example.com/article'
        with self.assertRaisesRegex(ValueError,'publisher_host_mismatch'):
            self.run_chain([a])
    def test_unregistered_source_id_refused(self):
        a=article();a['source_id']='en-999'
        with self.assertRaisesRegex(ValueError,'unregistered_source'):
            self.run_chain([a])
    def test_no_guessing_precise_publication_hour(self):
        r=self.run_chain([article()]);self.assertIsNone(r['capture_receipts'][0]['published_at'])
        self.assertEqual(r['capture_receipts'][0]['published_date'],'2026-10-23')
    def test_wrong_product_topic_refused(self):
        a=article('arabic');a['topic']='finance'
        with self.assertRaises(ValueError):self.run_chain([a])
    def test_future_or_stale_day_refused(self):
        for day in ('2026-10-25','2026-10-11'):
            with self.subTest(day=day):
                a=article();a['published_date']=day
                with self.assertRaises(ValueError):self.run_chain([a])
    def test_unqualified_source_text_cannot_auto_become_a_published_story(self):
        a=article();a['capture_method']='crawler_verified_full_article'
        with self.assertRaises(ValueError):self.run_chain([a])
    def test_truncated_or_oversized_snippet_refused(self):
        for txt in ('x', 'news '*60):
            with self.subTest(txt=txt[:10]):
                a=article();a['verbatim_excerpt']=txt
                with self.assertRaises(ValueError):self.run_chain([a])
    def test_web_excerpt_from_wrong_script_is_withheld(self):
        a=article('arabic');a['verbatim_excerpt']='English-only words with no Arabic script anywhere.'
        r=self.run_chain([a]);self.assertEqual(r['products']['arabic']['stories'],[])
        self.assertFalse(r['delivery_authorized'])
    def test_different_external_annotation_same_event_must_refuse_conflict(self):
        a=article();b=article('arabic');b['region']='levant'
        with self.assertRaisesRegex(ValueError,'conflicting_event_annotation'):
            self.run_chain([a,b])

if __name__=='__main__':unittest.main()
