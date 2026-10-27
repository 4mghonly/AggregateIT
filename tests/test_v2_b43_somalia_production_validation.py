"""B43: run actual unchanged production audit and production collector/translator/dedupe."""
import unittest
from datetime import datetime,timezone
from io import BytesIO
import requests
from v2_b43_somalia_production_validation import (
    _CANDIDATES,audit_one,collector_same_bytes,language_route,
    translation_contract,dedupe_stats,validate_candidate)

NOW="2026-10-27T06:00:00+00:00"
FEED=(b'<?xml version="1.0"?><rss><channel><title>Somalia</title>'
      b'<item><title>Somalia security updates issued in 2026</title>'
      b'<link>https://example.org/news/1</link>'
      b'<pubDate>Tue, 27 Oct 2026 05:00:00 GMT</pubDate>'
      b'<description>Authorities reported new steps in the region.</description>'
      b'</item></channel></rss>')
class Reply:
    def __init__(self,url,data,status=200):
        self.status_code=status;self.content=data;self.url=url;self.text=data.decode("utf8","replace")

class Tests(unittest.TestCase):
    def test_four_different_candidate_families(self):
        self.assertEqual(len(_CANDIDATES),4)
        self.assertEqual(len({x["family"] for x in _CANDIDATES}),4)
    def test_unchanged_real_validator_is_called_with_one_feed_and_website_request(self):
        calls=[]
        def get(url,*args,**kwargs):
            calls.append(url)
            if url.endswith("/feed/"):return Reply(url,FEED)
            return Reply(url,b'<html><title>Publisher</title></html>')
        record,raw,transport=audit_one({**_CANDIDATES[0],"enabled":False},request_get=get)
        self.assertTrue(record["production_compatible"])
        self.assertEqual(record["entries"],1)
        self.assertEqual(raw,FEED)
        self.assertEqual(calls.count(_CANDIDATES[0]["feed"]),1)
        self.assertEqual(transport["captured"],True)
    def test_collector_real_parse_against_original_feed_bytes(self):
        row={**_CANDIDATES[0],"enabled":False}
        items,health=collector_same_bytes(row,FEED)
        self.assertEqual(health["status"],"active")
        self.assertEqual(len(items),1)
        self.assertEqual(items[0]["language"],"so")
    def test_translation_route_is_foreign_without_model_call(self):
        items,_=collector_same_bytes({**_CANDIDATES[2],"enabled":False},FEED)
        route=language_route(items,declared_language="en")
        self.assertEqual(route["untranslated_items_requiring_arabic"],1)
        self.assertFalse(route["model_translation_performed"])
    def test_production_translator_contract_including_numerical_mutation(self):
        contract=translation_contract()
        self.assertTrue(contract["production_normalizer_accepts_valid_arabic_with_numbers"])
        self.assertTrue(contract["rejects_number_mutation"])
        self.assertTrue(contract["rejects_non_arabic_output"])
        self.assertFalse(contract["actual_model_called"])
    def test_duplicate_same_title_across_publishers(self):
        stamp=datetime.fromisoformat(NOW)
        rows={"shabelle":[{"published":stamp.timestamp(),"url":"https://example.org/1",
                           "title":"Same Somalia security bulletin today"}],
              "puntland_post":[{"published":stamp.timestamp(),"url":"https://different.example.org/2",
                           "title":"Same Somalia security bulletin today"}]}
        stats=dedupe_stats(rows,now=stamp)
        self.assertEqual(stats["cross_publisher_duplicate_pairs"],1)
        self.assertFalse(stats["semantic_event_equivalence_proven"])
    def test_distinct_articles_not_false_duplicate(self):
        now=datetime.fromisoformat(NOW)
        rows={"shabelle":[{"published":now.timestamp(),"url":"https://example.org/1","title":"Elections held in Somalia today"}],
              "puntland_post":[{"published":now.timestamp(),"url":"https://example.org/2","title":"Weather temperatures across the region"}]}
        self.assertEqual(dedupe_stats(rows,now=now)["duplicated_pairs"],0)
    def test_refuse_prod_enablement_and_insecure_url(self):
        with self.assertRaises(ValueError): validate_candidate({**_CANDIDATES[1],"enabled":True})
        with self.assertRaises(ValueError): validate_candidate({**_CANDIDATES[1],"feed":"http://example.org/feed/"})
    def test_real_translation_fallback_controlled_primary_failure(self):
        import arabic_live_v2 as live
        from unittest.mock import patch
        item={"language":"en","title":"Somalia officials met on 27 October",
              "summary":"The meeting involved 12 delegates.","source":"fixture"}
        response={"items":[{"index":0,"title_ar":"اجتمع مسؤولون صوماليون يوم 27 أكتوبر",
                          "summary_ar":"ضم الاجتماع 12 مندوباً."}]}
        calls=[]
        def call(route,*args,**kwargs):
            calls.append(route["model"])
            if route["model"]=="fixture-primary":
                raise RuntimeError("controlled_primary_failure")
            return response
        def lookup(prefix):
            return {"model":"fixture-primary" if prefix=="ARABIC_LLM_" else "fixture-fallback"}
        with (patch.object(live,"_route",side_effect=lookup),
              patch.object(live,"_route_call",side_effect=call)):
            translated,health,selected=live.translate_items_with_failover([item])
        self.assertEqual(calls,["fixture-primary","fixture-fallback"])
        self.assertEqual(selected,"fallback")
        self.assertEqual(len(translated),1)
        self.assertEqual(translated[0]["title_ar"],response["items"][0]["title_ar"])
        self.assertFalse(health[0]["ok"])
        self.assertTrue(health[-1]["ok"])

    def test_both_translation_routes_fail_closed_without_arabic_invention(self):
        import arabic_live_v2 as live
        from unittest.mock import patch
        item={"language":"so","title":"Wasiirka arrimaha dibadda",
              "summary":"Warbixin ku saabsan gobolka.","source":"fixture"}
        with (patch.object(live,"_route",side_effect=lambda prefix: {"model":prefix}),
              patch.object(live,"_route_call",side_effect=RuntimeError("no_model_result"))):
            with self.assertRaisesRegex(RuntimeError,"Both translation routes failed"):
                live.translate_items_with_failover([item])

if __name__=="__main__":unittest.main()
