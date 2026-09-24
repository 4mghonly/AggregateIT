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
from .core import State, canonical, clean, edition_window, live_window, scheduled_window, preliminary_relevant, uae_secondary_relevant, REGIONS
from .collect import entry_time, social_links, article_path_candidate, source_relevant, production_sources
from .editor import Client, validate_events, headline_summary_aligned, numbers, quote_supported, synthesize, EditorialError, is_arabic, _message_json, _event_envelope, _review_envelope, _bounded_articles
from .delivery import send, webhook_url, webhook_info, DeliveryError
from .render import render
from arabic_layout.render_pages import page2_region_plan, layout_plan
from .sample import fixture
from bs4 import BeautifulSoup

class CoreTests(unittest.TestCase):
    def test_six_hour_windows_at_uae_boundary(self):
        start,end=edition_window(datetime.fromisoformat('2026-09-18T02:00:00+00:00'))
        self.assertEqual(end.isoformat(),'2026-09-18T06:00:00+04:00')
        self.assertEqual((end-start).total_seconds(),21600)
        _,before=edition_window(datetime.fromisoformat('2026-09-18T01:59:59+00:00'))
        self.assertEqual(before.hour,0)
    def test_early_scheduler_waits_for_intended_edition(self):
        with patch('arabic_newsletter.core.time.sleep') as sleep:
            _,end=live_window(datetime.fromisoformat('2026-09-18T01:59:00+00:00'))
            self.assertEqual(end.isoformat(),'2026-09-18T06:00:00+04:00')
            self.assertEqual(sum(c.args[0] for c in sleep.call_args_list),60)

    def test_midnight_rollover(self):
        _,end=edition_window(datetime.fromisoformat('2026-09-18T01:00:00+04:00'))
        self.assertEqual(end.isoformat(),'2026-09-18T00:00:00+04:00')

    def test_three_minute_early_midnight_wake_targets_midnight(self):
        _,end=scheduled_window(datetime.fromisoformat('2026-09-20T19:57:00+00:00'))
        self.assertEqual(end.isoformat(),'2026-09-21T00:00:00+04:00')
        _,older=scheduled_window(datetime.fromisoformat('2026-09-20T19:49:00+00:00'))
        self.assertEqual(older.isoformat(),'2026-09-20T18:00:00+04:00')
    def test_finance_removed_security_exception(self):
        self.assertFalse(preliminary_relevant('Bitcoin rallies as stock market earnings rise'))
        self.assertTrue(preliminary_relevant('Military sanctions on arms exports'))
        self.assertTrue(preliminary_relevant('هجمات على البنية التحتية قرب الحدود','ar'))
        self.assertFalse(preliminary_relevant('ارتفاع سعر الذهب وأرباح الشركات','ar'))
    def test_non_english_arabic_languages_are_not_keyword_gated(self):
        self.assertTrue(preliminary_relevant('Actualité régionale sans mot-clé anglais','fr'))
        self.assertTrue(preliminary_relevant('Bölgesel gelişmeler hakkında açıklama','tr'))
        self.assertTrue(preliminary_relevant('تحولات إقليمية','fa'))
        self.assertFalse(preliminary_relevant('Bitcoin market rally and earnings','fr'))
    def test_uae_secondary_threshold_is_controlled(self):
        self.assertTrue(uae_secondary_relevant('UAE civil defence updates emergency readiness at Dubai airport'))
        self.assertFalse(uae_secondary_relevant('UAE hotel launches luxury brunch and investment offer'))

    def test_tracking_url_deduplication(self):
        self.assertEqual(canonical('https://site.test/a/?utm_source=x&id=2#top'),'https://site.test/a?id=2')
    def test_invalid_decode_markers_are_removed(self):
        self.assertEqual(clean('خبر\ufffd مهم\u200f'),'خبر مهم')
    def test_atom_updated_timestamp_is_accepted_without_inventing_retrieval_time(self):
        self.assertIsNotNone(entry_time({'updated_parsed':(2026,9,18,0,0,0,0,0,0)}))
        self.assertIsNone(entry_time({}))
    def test_publisher_linked_social_excludes_share_buttons(self):
        soup=BeautifulSoup('<a href="https://t.me/OfficialExample">Telegram</a><a href="https://x.com/intent/tweet">share</a>','html.parser')
        links=social_links(soup,'https://example.com')
        self.assertEqual(len(links),1); self.assertEqual(links[0]['verified_via'],'https://example.com')

    def test_wordpress_single_slug_article_path_is_accepted(self):
        self.assertTrue(article_path_candidate('/afghanistan-condemns-mosque-attack-in-khyber-pakhtunkhwa/'))
        self.assertFalse(article_path_candidate('/latest-news/'))

    def test_page_fallback_uses_uae_secondary_threshold(self):
        source={'country':'AE','language':'en'}
        self.assertTrue(source_relevant(source,'UAE civil defence updates emergency readiness at Dubai airport'))
        self.assertFalse(source_relevant(source,'Dubai hotel launches luxury brunch'))

    def test_failed_source_audits_are_rotated_back_into_production(self):
        end=datetime.fromisoformat('2026-09-21T00:00:00+04:00')
        sources=[{'id':'live','enabled':True,'language':'ar','verification_status':'active'}]
        sources += [{'id':f'en{i:02}','enabled':False,'language':'en','verification_status':'failed','retired_reason':'failed_source_audit_2026-09-19'} for i in range(25)]
        sources += [{'id':f'ar{i:02}','enabled':False,'language':'ar','verification_status':'failed','retired_reason':'failed_source_audit_2026-09-19'} for i in range(10)]
        sources += [{'id':'recovered','enabled':False,'language':'en','verification_status':'active','retired_reason':'failed_source_audit_2026-09-19'}]
        selected=production_sources(sources,end)
        ids={s['id'] for s in selected}
        self.assertIn('live',ids); self.assertIn('recovered',ids)
        self.assertEqual(sum(s['id'].startswith('en') for s in selected),18)
        self.assertEqual(sum(s['id'].startswith('ar') for s in selected),6)

    def test_egypt_and_oman_sources_are_first_class_regions(self):
        root=Path(__file__).resolve().parent
        sources=json.loads((root/'sources.json').read_text(encoding='utf-8'))
        self.assertTrue(any(s.get('country')=='EG' for s in sources))
        self.assertTrue(any(s.get('country')=='OM' for s in sources))
        self.assertTrue(all(s.get('region')=='egypt' for s in sources if s.get('country')=='EG'))
        self.assertTrue(all(s.get('region')=='oman' for s in sources if s.get('country')=='OM'))

class EditorialTests(unittest.TestCase):
    def setUp(self):
        self.article=dict(id='a',region='iraq',country='IQ',language='en',title='Officials report a border attack in Iraq',text='Officials report a border attack with 12 injuries.',
          source='Example',url='https://example.com/a',published=1,affiliation='publisher',kind='news')
        self.event=dict(region='iraq',topic='security',title_ar='تقرير عن هجوم قرب الحدود في العراق',summary_ar='أفاد المصدر بوقوع هجوم قرب الحدود وإصابة 12 شخصاً.',
          assessment_ar='لا تكفي المعلومات لتحديد تداعيات الهجوم.',watch_ar='متابعة تحديثات المصدر.',severity='high',source_ids=['a'],
          evidence=[{'id':'a','quote':'Officials report a border attack with 12 injuries.'}])
    def validate(self,event=None): return validate_events({'events':[event or self.event]},[self.article])
    def test_full_chat_endpoint_is_not_duplicated(self):
        self.assertEqual(Client._endpoint_url('https://openrouter.ai/api/v1/chat/completions','/chat/completions'),'https://openrouter.ai/api/v1/chat/completions')
        self.assertEqual(Client._endpoint_url('https://openrouter.ai/api/v1','/chat/completions'),'https://openrouter.ai/api/v1/chat/completions')

    def test_empty_auth_scheme_defaults_to_bearer(self):
        with tempfile.TemporaryDirectory() as d:
            state=State(d)
            env={
                'ARABIC_LLM_API_KEY':'primary-key',
                'ARABIC_LLM_BASE_URL':'https://primary.example/v1',
                'ARABIC_LLM_MODEL':'primary-model',
                'ARABIC_LLM_AUTH_SCHEME':'',
                'ARABIC_LLM_FALLBACK_API_KEY':'fallback-key',
                'ARABIC_LLM_FALLBACK_BASE_URL':'https://fallback.example/v1',
                'ARABIC_LLM_FALLBACK_MODEL':'fallback-model',
                'ARABIC_LLM_FALLBACK_AUTH_SCHEME':''
            }
            with patch.dict(os.environ,env,clear=True):
                client=Client(state)
                self.assertEqual(client._headers('primary-key',False)['Authorization'],'Bearer primary-key')
                self.assertEqual(client._headers('fallback-key',True)['Authorization'],'Bearer fallback-key')
            state.close()

    def test_live_llm_latency_budget_is_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            state=State(d)
            env={
                'ARABIC_LLM_API_KEY':'primary-key',
                'ARABIC_LLM_BASE_URL':'https://primary.example/v1',
                'ARABIC_LLM_MODEL':'primary-model'
            }
            with patch.dict(os.environ,env,clear=True):
                client=Client(state,max_calls=6,read_timeout=90,wall_budget_s=600)
                self.assertEqual(client.max_calls,6)
                self.assertEqual(client.read_timeout,90)
                self.assertIsNotNone(client.deadline)
            state.close()

    def test_primary_and_fallback_routes_are_independent(self):
        with tempfile.TemporaryDirectory() as d:
            state=State(d)
            primary_env={
                'ARABIC_LLM_API_KEY':'primary-key',
                'ARABIC_LLM_BASE_URL':'https://primary.example/v1',
                'ARABIC_LLM_MODEL':'primary-model',
                'ARABIC_LLM_FALLBACK_API_KEY':'',
                'ARABIC_LLM_FALLBACK_BASE_URL':'',
                'ARABIC_LLM_FALLBACK_MODEL':'',
                'ARABIC_LLM_FALLBACK_MODELS':'fallback-alt'
            }
            with patch.dict(os.environ,primary_env,clear=True):
                client=Client(state)
                self.assertEqual(client._endpoint()[:3],('https://primary.example/v1','primary-key','primary-model'))
                self.assertFalse(client.fallback_base)
                self.assertFalse(client.fallback_model)
                self.assertNotIn('fallback-alt',client.primary_models)
            fallback_env={
                'ARABIC_LLM_API_KEY':'',
                'ARABIC_LLM_BASE_URL':'',
                'ARABIC_LLM_MODEL':'',
                'ARABIC_LLM_FALLBACK_API_KEY':'fallback-key',
                'ARABIC_LLM_FALLBACK_BASE_URL':'https://fallback.example/v1',
                'ARABIC_LLM_FALLBACK_MODEL':'fallback-model'
            }
            with patch.dict(os.environ,fallback_env,clear=True):
                client=Client(state)
                self.assertTrue(client.force_fallback_credential)
                self.assertEqual(client._endpoint()[:3],('https://fallback.example/v1','fallback-key','fallback-model'))
            state.close()

    def test_invalid_primary_json_stays_on_primary_for_compact_repair(self):
        with tempfile.TemporaryDirectory() as d:
            state=State(d)
            env={
                'ARABIC_LLM_API_KEY':'primary-key',
                'ARABIC_LLM_BASE_URL':'https://primary.example/v1',
                'ARABIC_LLM_MODEL':'primary-model',
                'ARABIC_LLM_FALLBACK_API_KEY':'fallback-key',
                'ARABIC_LLM_FALLBACK_BASE_URL':'https://fallback.example/v1',
                'ARABIC_LLM_FALLBACK_MODEL':'fallback-model'
            }
            bad=Mock(status_code=200)
            bad.json.return_value={'choices':[{'finish_reason':'stop','message':{'content':'not-json'}}],'usage':{}}
            with patch.dict(os.environ,env,clear=True):
                client=Client(state)
                with patch('arabic_newsletter.editor.requests.post',side_effect=[bad,bad]) as post:
                    with self.assertRaisesRegex(EditorialError,'Invalid or truncated'):
                        client.chat('Return JSON only.',{'text':'hello'},80,use_cache=False)
                    self.assertEqual(post.call_count,2)
                    self.assertFalse(client.force_fallback_credential)
            state.close()

    def test_text_probe_accepts_plain_arabic_without_json(self):
        with tempfile.TemporaryDirectory() as d:
            state=State(d)
            env={
                'ARABIC_LLM_API_KEY':'primary-key',
                'ARABIC_LLM_BASE_URL':'https://primary.example/v1',
                'ARABIC_LLM_MODEL':'primary-model'
            }
            response=Mock(status_code=200)
            response.json.return_value={'choices':[{'message':{'content':'يظل التنسيق الأمني الإقليمي قيد المراجعة.'}}]}
            with patch.dict(os.environ,env,clear=True):
                client=Client(state)
                with patch('arabic_newsletter.editor.requests.post',return_value=response):
                    self.assertTrue(is_arabic(client.probe_text('translate this')))
            state.close()

    def test_message_json_accepts_fences_and_text_blocks(self):
        self.assertEqual(_message_json({'content':'\x60\x60\x60json\n{"ok":true}\n\x60\x60\x60'}),{'ok':True})
        self.assertEqual(_message_json({'content':[{'type':'text','text':'prefix {"ok": true} suffix'}]}),{'ok':True})

    def test_single_event_schema_is_normalized(self):
        event=copy.deepcopy(self.event)
        self.assertEqual(_event_envelope(event),{'events':[event]})
        self.assertEqual(_event_envelope({'event':event}),{'events':[event]})

    def test_review_schema_normalizes_string_indexes(self):
        self.assertEqual(_review_envelope({'review':{'approved':['0'],'reasons':{}}},1)['approved'],[0])
        with self.assertRaises(EditorialError): _review_envelope({'approved':[True]},1)

    def test_bounded_articles_preserve_language_diversity(self):
        articles=[]
        for i in range(6):
            articles.append(dict(self.article,id=f'ar{i}',source_id='arabic',language='ar',region='iraq',text='x'*800))
        articles.append(dict(self.article,id='en1',source_id='english',language='en',region='iraq',text='y'*800))
        bounded=_bounded_articles(articles,char_limit=3500,text_limit=800)
        self.assertIn('en',{a['language'] for a in bounded})

    def test_compact_recovery_after_unparseable_full_synthesis(self):
        with tempfile.TemporaryDirectory() as d:
            state=State(d)
            with patch('arabic_newsletter.editor.Client') as client:
                client.return_value.chat.side_effect=[
                    EditorialError('Invalid or truncated model JSON after retry'),
                    {'events':[copy.deepcopy(self.event)]},
                    {'approved':[0]}
                ]
                events,_=synthesize([self.article],state)
                self.assertEqual(len(events),1)
                self.assertEqual(client.return_value.chat.call_count,3)
                recovery_call=client.return_value.chat.call_args_list[1]
                self.assertLessEqual(len(recovery_call.args[1]['articles'][0]['text']),850)
                self.assertFalse(recovery_call.kwargs.get('use_cache',True))
            state.close()

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

    def test_headline_summary_alignment_gate(self):
        good=dict(self.event)
        self.assertTrue(headline_summary_aligned(good['title_ar'],good['summary_ar'],good['region']))
        bad=dict(good)
        bad['title_ar']='إيران تعلن إغلاق مضيق هرمز'
        self.assertFalse(headline_summary_aligned(bad['title_ar'],good['summary_ar'],good['region']))

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
    def test_expected_channel_guard(self):
        response=Mock(status_code=200)
        response.json.return_value={'id':'123','channel_id':'wrong','name':'Agentic Bot'}
        env={
            'DISCORD_WEBHOOK_ARABIC':'https://discord.com/api/webhooks/123/fake',
            'DISCORD_ARABIC_EXPECTED_CHANNEL_ID':'expected'
        }
        with patch.dict(os.environ,env,clear=True), patch('arabic_newsletter.delivery.requests.get',return_value=response):
            with self.assertRaisesRegex(DeliveryError,'expected'):
                webhook_info()

    def test_no_old_webhook_fallback(self):
        with patch.dict(os.environ,{'DISCORD_WEBHOOK_ARABIC':'','DISCORD_WEBHOOK':'https://discord.com/api/webhooks/123/token'}):
            with self.assertRaises(DeliveryError): webhook_url()

    def test_main_is_authoritative_arabic_production(self):
        root=Path(__file__).resolve().parents[1]
        workflow=(root/'.github'/'workflows'/'arabic-scheduler.yml').read_text(encoding='utf-8')
        self.assertIn('ref: main',workflow)
        self.assertNotIn('Arabic-production',workflow)
        self.assertIn('DISCORD_WEBHOOK_ARABIC',workflow)
        self.assertIn('0 2,8,14,20 * * *',workflow)
    def test_success_then_duplicate_suppression(self):
        with tempfile.TemporaryDirectory() as d:
            state=State(Path(d)/'state'); path=Path(d)/'slide.png'; path.write_bytes(b'png')
            response=Mock(status_code=200); response.json.return_value={'id':'123'}
            with patch('arabic_newsletter.delivery.webhook_url',return_value='https://discord.com/api/webhooks/1/fake'),patch('arabic_newsletter.delivery.requests.post',return_value=response) as post:
                self.assertEqual(send(state,'edition',[path]),'["123"]'); self.assertEqual(send(state,'edition',[path]),'["123"]')
                self.assertEqual(post.call_count,1)
            state.close()
    def test_confirmed_failed_delivery_can_retry(self):
        with tempfile.TemporaryDirectory() as d:
            state=State(Path(d)/'state'); path=Path(d)/'slide.png'; path.write_bytes(b'png')
            failed=Mock(status_code=400)
            success=Mock(status_code=200); success.json.return_value={'id':'456','channel_id':'789'}
            with patch('arabic_newsletter.delivery.webhook_url',return_value='https://discord.com/api/webhooks/1/fake'),patch('arabic_newsletter.delivery.requests.post',side_effect=[failed,success]) as post:
                with self.assertRaises(DeliveryError): send(state,'edition',[path])
                self.assertEqual(send(state,'edition',[path]),'["456"]')
                self.assertEqual(post.call_count,2)
            state.close()

    def test_timeout_retries_then_records_failed_for_resumable_workflow_retry(self):
        with tempfile.TemporaryDirectory() as d:
            state=State(Path(d)/'state'); path=Path(d)/'slide.png'; path.write_bytes(b'png')
            with patch('arabic_newsletter.delivery.webhook_url',return_value='https://discord.com/api/webhooks/1/fake'),patch('arabic_newsletter.delivery.requests.post',side_effect=requests.Timeout) as post,patch('arabic_newsletter.delivery.time.sleep'):
                with self.assertRaises(DeliveryError): send(state,'edition',[path])
                self.assertEqual(post.call_count,3)
                self.assertEqual(state.delivery('edition')[0],'failed')
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
                paths,clipped=render(brief,Path(d)/str(i))
                self.assertEqual(len(paths),3)
                if i==2: self.assertLessEqual(clipped,90)
                for path in paths:
                    with Image.open(path) as image: self.assertEqual(image.size,(3840,2160))
    def test_layout_slots_never_repeat_news_events(self):
        brief=fixture()
        leads,secondary,uae=layout_plan(brief)
        key=lambda e:e.get('fingerprint') or e.get('title_ar')
        lead_keys={key(e) for e in leads}
        secondary_keys={key(e) for e in secondary}
        uae_keys={key(e) for e in uae}
        self.assertTrue(lead_keys.isdisjoint(secondary_keys))
        self.assertTrue(lead_keys.isdisjoint(uae_keys))
        self.assertTrue(secondary_keys.isdisjoint(uae_keys))
        self.assertLessEqual(len(leads),3)
        self.assertLessEqual(len(secondary),3)
        self.assertLessEqual(len(uae),4)

    def test_page2_uses_only_active_region_cards_and_preserves_full_monitoring_list(self):
        brief=fixture()
        limited=copy.deepcopy(brief)
        limited['events']=[e for e in limited['events'] if e['region'] in ('iran','iraq','somalia','pakistan','levant')]
        active,quiet,first=page2_region_plan(limited['events'])
        self.assertEqual(set(active),{'iran','iraq','somalia','pakistan','levant'})
        self.assertEqual(len(active)+len(quiet),len(REGIONS))
        self.assertTrue(set(active).isdisjoint(quiet))
        self.assertEqual(set(first),set(active))

    def test_sample_covers_every_region(self):
        brief=fixture()
        self.assertIn('somalia',REGIONS)
        self.assertIn('egypt',REGIONS)
        self.assertIn('oman',REGIONS)
        self.assertEqual(len(REGIONS),17)
        self.assertEqual(set(REGIONS),{e['region'] for e in brief['events']})
        self.assertGreaterEqual(sum(any(s.get('country')=='AE' for s in e['sources']) for e in brief['events']),3)

    def test_sample_never_financial(self):
        text=json.dumps(fixture(),ensure_ascii=False)
        for word in ('NASDAQ','Bitcoin','بورصة','استثمار'): self.assertNotIn(word,text)

if __name__=='__main__': unittest.main()
