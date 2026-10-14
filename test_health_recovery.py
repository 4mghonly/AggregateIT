"""Regression cases from production failures; all API calls are mocked."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import requests
import llm
import arabic_live_v2 as arabic
from llm_response import response_text
from runtime_health import arabic_health, overdue_runs


def reply(content,finish="stop"):
    class Response:
        status_code=200
        text=""
        def json(self): return {"choices":[{"message":{"content":content},"finish_reason":finish}]}
        def raise_for_status(self): pass
    return Response()


ANALYSIS={"situation_ar":"تطور أمني بحسب المصدر", "implications_ar":"تستمر متابعة التطورات",
          "developing_ar":["متابعة البيانات الرسمية"],"watch_ar":["البيانات الجديدة"]}


class EnglishRecovery(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        config={"API_KEY":"key","BASE_URL":"https://primary.invalid/v1","MODEL":"primary",
                "FALLBACK_API_KEY":"key2","FALLBACK_BASE_URL":"https://fallback.invalid/v1","FALLBACK_MODEL":"fallback",
                "_CONFIG_ERROR":"","_calls":0,"_force_fallback":False,"MAX_CALLS":10,
                "REQUEST_OPTIONS":{},"FALLBACK_REQUEST_OPTIONS":{},
                "LEDGER_FILE":str(Path(self.tmp.name)/"ledger.json"),"USAGE_FILE":str(Path(self.tmp.name)/"usage.json")}
        for name,value in config.items():
            p=patch.object(llm,name,value);p.start();self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_invalid_200_uses_fallback_and_never_caches_bad_output(self):
        sent=[]
        def post(url,**kwargs):
            sent.append(url)
            return reply(None if "primary" in url else '{"valid":true}')
        with patch.object(llm.requests,"post",side_effect=post):
            self.assertEqual(llm.chat_json([{"role":"user","content":"JSON"}]),{"valid":True})
        self.assertEqual(len(sent),2)
        self.assertIn("fallback",sent[-1])
        ledger=json.loads(Path(llm.LEDGER_FILE).read_text())
        self.assertEqual(next(iter(ledger.values()))["response"],'{"valid":true}')

    def test_schema_invalid_200_fails_over(self):
        def validate(obj):
            if not obj.get("valid"): raise ValueError("required_field")
        def post(url,**kwargs): return reply('{}' if "primary" in url else '{"valid":true}')
        with patch.object(llm.requests,"post",side_effect=post):
            self.assertTrue(llm.chat_json([],validator=validate)["valid"])

    def test_timeout_fails_over(self):
        def post(url,**kwargs):
            if "primary" in url: raise requests.ReadTimeout()
            return reply('{"ok":true}')
        with patch.object(llm.requests,"post",side_effect=post): self.assertTrue(llm.chat_json([])["ok"])

    def test_request_budget_counts_repairs(self):
        with patch.object(llm,"MAX_CALLS",2),patch.object(llm.requests,"post",return_value=reply(None)) as post:
            with self.assertRaises(llm.BudgetExceeded): llm.chat_json([])
            self.assertEqual(post.call_count,2)

    def test_invalid_cached_response_is_revalidated(self):
        key=llm._ledger_key("primary",[])
        Path(llm.LEDGER_FILE).write_text(json.dumps({key:{"status":"success","response":"bad"}}))
        with patch.object(llm.requests,"post",return_value=reply('{"ok":true}')) as post:
            self.assertTrue(llm.chat_json([])["ok"]);self.assertEqual(post.call_count,1)

    def test_truncated_response_is_rejected(self):
        with self.assertRaises(ValueError): response_text(reply('{"ok":true}',"length").json())


class ArabicRecovery(unittest.TestCase):
    def test_missing_publication_date_is_not_fresh_news(self):
        from bs4 import BeautifulSoup
        self.assertEqual(arabic.published_ts(object()),0)
        self.assertEqual(arabic.html_published_ts(BeautifulSoup('<h1>news</h1>','html.parser')),0)
        soup=BeautifulSoup('<script type="application/ld+json">{"@graph":[{"datePublished":"2026-10-08T08:00:00Z"}]}</script>','html.parser')
        self.assertEqual(arabic.html_published_ts(soup),datetime(2026,10,8,8,tzinfo=timezone.utc).timestamp())
    def test_analysis_schema_failure_retries_compact_then_fallback(self):
        routes={"model":"synthetic","base":"https://example.invalid","chat":"/chat/completions","headers":{},"options":{}}
        with patch.object(arabic,"_route",return_value=routes),patch.object(arabic,"_route_call",side_effect=[{}, {}, ANALYSIS]) as call:
            result,health,route=arabic.llm_analysis_with_failover([])
        self.assertEqual(route,"fallback");self.assertEqual(call.call_count,3)
        self.assertFalse(health[0]["ok"]);self.assertEqual(result["watch_ar"],ANALYSIS["watch_ar"])

    def test_partial_translation_falls_back_for_missing_rows_only(self):
        rows=[{"title":"security update","summary":"border security","language":"en"} for _ in range(4)]
        calls=[]
        def translate(route,system,payload,**kwargs):
            calls.append(len(payload["items"]))
            count=0 if len(calls)==1 else len(payload["items"])
            return {"items":[{"index":i,"title_ar":"تطور أمني","summary_ar":"متابعة أمن الحدود"} for i in range(count)]}
        with patch.object(arabic,"_route",return_value={"model":"synthetic"}),patch.object(arabic,"_route_call",side_effect=translate):
            out,health,route=arabic.translate_items_with_failover(rows)
        self.assertEqual(len(out),4);self.assertEqual(calls,[1,1,1,1,1]);self.assertEqual(route,"mixed")

    def test_partial_translation_is_degraded(self):
        rows=[{"title":"security","summary":"border","language":"en","source":"test","source_id":str(i),"country":"IQ","region":"iraq","url":str(i),"published":0} for i in range(2)]
        with patch.object(arabic,"translate_items_with_failover",return_value=([dict(rows[0],title_ar="أمن",summary_ar="حدود")],[],"primary")):
            _,health=arabic.prepare_selected(rows,2,False)
        self.assertEqual(health["status"],"degraded")

    def test_timeout_moves_to_other_route_without_double_wait(self):
        route={"model":"synthetic","base":"https://example.invalid","chat":"/chat/completions","headers":{},"options":{}}
        with patch.object(arabic.requests,"post",side_effect=requests.ReadTimeout()) as post:
            with self.assertRaisesRegex(RuntimeError,"ReadTimeout"): arabic._route_call(route,"system",{})
        self.assertEqual(post.call_count,1)

    def test_health_preserves_translation_failure_after_analysis_success(self):
        brief={"events":[{}],"llm_health":{"status":"ok","translation":{"status":"degraded"}}}
        health=arabic_health(brief,[{"country":"AE"}])
        self.assertEqual(health["status"],"degraded");self.assertIn("translation incomplete",health["issues"])
        self.assertFalse(health["delivery"]["confirmed"])

    def test_number_invention_is_rejected(self):
        self.assertFalse(arabic._normalize_translations({"items":[{"index":0,"title_ar":"وقوع 9 حوادث","summary_ar":"رصد 9 حوادث"}]},[{"title":"3 incidents","summary":"3 incidents"}]))


class CadenceRecovery(unittest.TestCase):
    def test_stale_success_and_recent_failure_do_not_hide_overdue_engine(self):
        now=datetime.now(timezone.utc)
        runs=[{"name":"News Intelligence Engine","status":"completed","conclusion":"success","created_at":(now-timedelta(hours=3)).isoformat()},
              {"name":"News Intelligence Engine","status":"completed","conclusion":"failure","created_at":now.isoformat()}]
        self.assertIn("News Intelligence Engine: overdue or no successful run",overdue_runs(runs,now))

    def test_only_engine_saves_canonical_cache(self):
        import yaml
        workflows={p.name:yaml.safe_load(p.read_text()) for p in Path('.github/workflows').glob('*.yml')}
        groups=[workflows[x]["concurrency"]["group"] for x in ('engine.yml','slide.yml','tv_refresh.yml')]
        self.assertEqual(len(set(groups)),3)
        for name in ('slide.yml','backup.yml','history.yml','calibration.yml','search.yml'):
            steps=next(iter(workflows[name]["jobs"].values()))['steps']
            for step in steps:
                if step.get('with',{}).get('path','').rstrip('/')=='data':
                    self.assertEqual(step['uses'],'actions/cache/restore@v5',name)



class October14Recovery(unittest.TestCase):
    setUp=EnglishRecovery.setUp
    def test_last_two_calls_reserve_a_fallback_attempt(self):
        with patch.object(llm,'MAX_CALLS',2),patch.object(llm.requests,'post',side_effect=[reply(None),reply('{"ok":true}')]) as post:
            self.assertTrue(llm.chat_json([])['ok'])
            self.assertIn('fallback',post.call_args_list[-1].args[0])

    def test_truncation_repair_increases_output_allowance(self):
        with patch.object(llm,'_route_complete',side_effect=lambda f=False:not f),patch.object(llm.requests,'post',side_effect=[reply('{}','length'),reply('{"ok":true}')]) as post:
            self.assertTrue(llm.chat_json([],max_tokens=2200)['ok'])
            self.assertGreater(post.call_args_list[1].kwargs['json']['max_tokens'],2200)

    def test_runtime_options_cannot_override_input_or_output_budget(self):
        with patch.object(llm,'REQUEST_OPTIONS',{'max_tokens':1,'messages':[],'model':'other'}),patch.object(llm.requests,'post',return_value=reply('{"ok":true}')) as post:
            llm.chat_json([{'role':'user','content':'test'}],max_tokens=4096)
        body=post.call_args.kwargs['json']
        self.assertEqual(body['max_tokens'],4096);self.assertEqual(body['model'],'primary')
        self.assertEqual(body['messages'][0]['content'],'test')

    def test_http_cooldown_persists_and_expires(self):
        import http_backoff
        with patch.object(http_backoff,'STATE',Path(self.tmp.name)/'cooldown.json'),patch.object(http_backoff.time,'time',return_value=1000):
            http_backoff.observe('https://example.test/feed',429,{'Retry-After':'60'})
            self.assertTrue(http_backoff.blocked('https://example.test/other'))
            self.assertFalse(http_backoff.blocked('https://other.test/feed'))
        with patch.object(http_backoff,'STATE',Path(self.tmp.name)/'cooldown.json'),patch.object(http_backoff.time,'time',return_value=2000):
            self.assertFalse(http_backoff.blocked('https://example.test/feed'))

    def test_uae_context_remains_dated_and_is_never_older_than_one_day(self):
        now=datetime.now(timezone.utc).timestamp()
        rows=[{'title':'Fresh','summary':'News','country':'IQ','published':now-10},
              {'title':'UAE context','summary':'News','country':'AE','published':now-12*3600},
              {'title':'Old UAE','summary':'News','country':'AE','published':now-25*3600}]
        with patch.object(arabic,'load_sources',return_value=[{}]),patch.object(arabic,'fetch_source',return_value=(rows,{})):
            items,_=arabic.collect(6)
        self.assertEqual(len(items),2)
        context=next(x for x in items if x.get('context_only'))
        self.assertEqual(context['published'],rows[1]['published'])
        self.assertIn('24',context['summary'])

if __name__=="__main__": unittest.main()
