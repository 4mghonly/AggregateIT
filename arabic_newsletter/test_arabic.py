"""Offline behavioral tests for evidence, isolation, time windows, rendering and delivery."""
import copy
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
import requests
from PIL import Image
from .core import State, canonical, edition_window, live_window, preliminary_relevant
from .collect import entry_time, social_links
from .editor import validate_events, numbers, quote_supported, synthesize, EditorialError
from .delivery import send, webhook_url, DeliveryError
from .render import render
from .sample import fixture
from bs4 import BeautifulSoup

class CoreTests(unittest.TestCase):
    def test_six_hour_windows_at_uae_boundary(self):
        start,end=edition_window(datetime.fromisoformat('2026-09-18T11:30:00+00:00'))
        self.assertEqual(end.isoformat(),'2026-09-18T15:30:00+04:00')
        self.assertEqual((end-start).total_seconds(),21600)
        _,before=edition_window(datetime.fromisoformat('2026-09-18T11:29:59+00:00'))
        self.assertEqual(before.hour,9)
    def test_early_scheduler_waits_for_intended_edition(self):
        with patch('arabic_newsletter.core.time.sleep') as sleep:
            _,end=live_window(datetime.fromisoformat('2026-09-18T11:29:00+00:00'))
            self.assertEqual(end.isoformat(),'2026-09-18T15:30:00+04:00')
            self.assertEqual(sum(c.args[0] for c in sleep.call_args_list),60)

    def test_midnight_rollover(self):
        _,end=edition_window(datetime.fromisoformat('2026-09-18T01:00:00+04:00'))
        self.assertEqual(end.isoformat(),'2026-09-17T21:30:00+04:00')
    def test_finance_removed_security_exception(self):
        self.assertFalse(preliminary_relevant('Bitcoin rallies as stock market earnings rise'))
        self.assertTrue(preliminary_relevant('Military sanctions on arms exports'))
        self.assertTrue(preliminary_relevant('هجمات على البنية التحتية قرب الحدود','ar'))
        self.assertFalse(preliminary_relevant('ارتفاع سعر الذهب وأرباح الشركات','ar'))
    def test_tracking_url_deduplication(self):
        self.assertEqual(canonical('https://site.test/a/?utm_source=x&id=2#top'),'https://site.test/a?id=2')
    def test_missing_publication_never_becomes_now(self):
        self.assertIsNone(entry_time({'updated_parsed':(2026,9,18,0,0,0,0,0,0)}))
    def test_publisher_linked_social_excludes_share_buttons(self):
        soup=BeautifulSoup('<a href="https://t.me/OfficialExample">Telegram</a><a href="https://x.com/intent/tweet">share</a>','html.parser')
        links=social_links(soup,'https://example.com')
        self.assertEqual(len(links),1); self.assertEqual(links[0]['verified_via'],'https://example.com')

class EditorialTests(unittest.TestCase):
    def setUp(self):
        self.article=dict(id='a',region='iraq',country='IQ',language='en',title='Officials report a border attack in Iraq',text='Officials report a border attack with 12 injuries.',
          source='Example',url='https://example.com/a',published=1,affiliation='publisher',kind='news')
        self.event=dict(region='iraq',topic='security',title_ar='تقرير عن هجوم قرب الحدود في العراق',summary_ar='أفاد المصدر بوقوع هجوم قرب الحدود وإصابة 12 شخصاً.',
          assessment_ar='لا تكفي المعلومات لتحديد تداعيات الهجوم.',watch_ar='متابعة تحديثات المصدر.',severity='high',source_ids=['a'],
          evidence=[{'id':'a','quote':'Officials report a border attack with 12 injuries.'}])
    def validate(self,event=None): return validate_events({'events':[event or self.event]},[self.article])
    def test_one_correction_then_same_review_gate(self):
        with tempfile.TemporaryDirectory() as d:
            state=State(d)
            with patch('arabic_newsletter.editor.Client') as client:
                client.return_value.chat.side_effect=[{'events':[copy.deepcopy(self.event)]},{'approved':[],'reasons':{'0':'Clarify attribution'}},{'events':[copy.deepcopy(self.event)]},{'approved':[0]}]
                events,_=synthesize([self.article],state)
                self.assertEqual(len(events),1); self.assertEqual(client.return_value.chat.call_count,4)
            state.close()
    def test_repair_cannot_bypass_rejection_or_loop(self):
        with tempfile.TemporaryDirectory() as d:
            state=State(d)
            with patch('arabic_newsletter.editor.Client') as client:
                client.return_value.chat.side_effect=[{'events':[copy.deepcopy(self.event)]},{'approved':[]},{'events':[copy.deepcopy(self.event)]},{'approved':[]}]
                with self.assertRaises(EditorialError): synthesize([self.article],state)
                self.assertEqual(client.return_value.chat.call_count,4)
                self.assertEqual(len(state.get('last_editorial_review')),2)
            state.close()

    def test_attributed_not_verified(self):
        events,rejected=self.validate(); self.assertEqual(len(events),1); self.assertFalse(rejected)
        self.assertEqual(events[0]['status_ar'],'تقرير منسوب')
    def test_evidence_typography_only_normalization(self):
        self.assertTrue(quote_supported('Officials said: “12 injured”.','Officials said: "12 injured".'))
        self.assertFalse(quote_supported('Officials said 120 injured','Officials said 12 injured'))
        self.assertFalse(quote_supported('Officials said not injured','Officials said injured'))

    def test_publisher_country_does_not_define_event_region(self):
        self.event.update(region='turkey',title_ar='هجوم في جنوب لبنان',summary_ar='أفاد المصدر بهجوم في لبنان.')
        self.assertEqual(self.validate()[1][0]['reason'],'event_geography')
        self.event['region']='levant'; self.assertTrue(self.validate()[0])
    def test_outside_region_incident_is_rejected(self):
        self.event.update(region='north_africa',title_ar='هجوم على محطة روسية',summary_ar='أفاد المصدر بهجوم على محطة في روسيا.')
        self.assertEqual(self.validate()[1][0]['reason'],'event_geography')

    def test_hallucinated_citation_rejected(self):
        self.event['source_ids']=['invented']; self.assertFalse(self.validate()[0])
    def test_hallucinated_evidence_rejected(self):
        self.event['evidence'][0]['quote']='A statement that does not exist'; self.assertFalse(self.validate()[0])
    def test_altered_casualty_number_rejected(self):
        self.event['summary_ar']='أفاد المصدر بإصابة 120 شخصاً.'; self.assertFalse(self.validate()[0])
    def test_arabic_indic_number_supported(self):
        self.event['summary_ar']='أفاد المصدر بإصابة ١٢ شخصاً.'; self.assertTrue(self.validate()[0])
    def test_scaled_quantities_preserve_exact_total(self):
        self.assertEqual(numbers('۵۲۲ هزار و ۲۰۰'),numbers('522 ألف و200'))
        self.assertNotEqual(numbers('۵۲۲ هزار و ۲۰۰'),numbers('522 ألف'))
        self.assertEqual(numbers('۴۳۹ هزار'),numbers('439000'))
        self.assertNotEqual(numbers('12 مليون'),numbers('12'))
    def test_ellipsis_requires_ordered_real_fragments(self):
        self.assertTrue(quote_supported('Officials reported a border attack...Police confirmed 12 injuries','Officials reported a border attack on Friday. Police confirmed 12 injuries.'))
        self.assertFalse(quote_supported('Officials reported a border attack...Police confirmed 120 injuries','Officials reported a border attack. Police confirmed 12 injuries.'))
        self.assertFalse(quote_supported('Officials stated...there was an attack','Officials stated no evidence that there was an attack'))
    def test_currency_amount_is_not_security_output(self):
        self.article['text']+=' The project costs 12 million dollars.'
        self.event['summary_ar']='أفاد المصدر بتمويل بقيمة 12 مليون دولار.'
        self.assertFalse(self.validate()[0])

    def test_non_arabic_rejected(self):
        self.event['summary_ar']='The officials reported a border attack.'; self.assertFalse(self.validate()[0])
    def test_financial_and_out_of_scope_rejected(self):
        self.event['topic']='stocks'; self.assertFalse(self.validate()[0])
    def test_social_claim_not_confirmed(self):
        self.article['kind']='social'; events,_=self.validate(); self.assertEqual(events[0]['status_ar'],'تصريح منسوب')

class DeliveryTests(unittest.TestCase):
    def test_no_old_webhook_fallback(self):
        with patch.dict(os.environ,{'DISCORD_WEBHOOK_ARABIC':'','DISCORD_WEBHOOK':'https://discord.com/api/webhooks/123/token'}):
            with self.assertRaises(DeliveryError): webhook_url()
    def test_success_then_duplicate_suppression(self):
        with tempfile.TemporaryDirectory() as d:
            state=State(Path(d)/'state'); path=Path(d)/'slide.png'; path.write_bytes(b'png')
            response=Mock(status_code=200); response.json.return_value={'id':'123'}
            with patch('arabic_newsletter.delivery.webhook_url',return_value='https://discord.com/api/webhooks/1/fake'),patch('arabic_newsletter.delivery.requests.post',return_value=response) as post:
                self.assertEqual(send(state,'edition',[path]),'123'); self.assertEqual(send(state,'edition',[path]),'123')
                self.assertEqual(post.call_count,1)
            state.close()
    def test_timeout_is_uncertain_and_not_retried(self):
        with tempfile.TemporaryDirectory() as d:
            state=State(Path(d)/'state'); path=Path(d)/'slide.png'; path.write_bytes(b'png')
            with patch('arabic_newsletter.delivery.webhook_url',return_value='https://discord.com/api/webhooks/1/fake'),patch('arabic_newsletter.delivery.requests.post',side_effect=requests.Timeout) as post:
                with self.assertRaises(DeliveryError): send(state,'edition',[path])
                with self.assertRaises(DeliveryError): send(state,'edition',[path])
                self.assertEqual(post.call_count,1); self.assertEqual(state.delivery('edition')[0],'uncertain')
            state.close()

    def test_only_png_slides_can_reach_arabic_webhook(self):
        with tempfile.TemporaryDirectory() as d:
            state=State(Path(d)/'state'); path=Path(d)/'sources-ar.txt'; path.write_text('مصادر')
            with patch('arabic_newsletter.delivery.webhook_url',return_value='https://discord.com/api/webhooks/1/fake'),patch('arabic_newsletter.delivery.requests.post') as post:
                with self.assertRaises(DeliveryError): send(state,'edition',[path])
                post.assert_not_called()
            state.close()

class RenderTests(unittest.TestCase):
    def test_full_empty_long_and_offline(self):
        with tempfile.TemporaryDirectory() as d,patch('socket.socket',side_effect=AssertionError('No network during rendering')):
            normal=fixture(); empty=copy.deepcopy(normal); empty['events']=[]; empty['health']=[]
            for i,brief in enumerate([normal,empty,fixture(True)]):
                paths,_=render(brief,Path(d)/str(i))
                for path in paths:
                    with Image.open(path) as image: self.assertEqual(image.size,(3840,2160))
    def test_sample_never_financial(self):
        text=json.dumps(fixture(),ensure_ascii=False)
        for word in ('NASDAQ','Bitcoin','بورصة','استثمار'): self.assertNotIn(word,text)

if __name__=='__main__': unittest.main()
