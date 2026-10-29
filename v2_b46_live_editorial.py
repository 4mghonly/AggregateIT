"""B46 source-backed article -> B3 ledger -> B4 independent editor -> daily compiler.

The existing article-body gate requires actual publisher HTML structure and
verbatim quotations. This is attributed publisher evidence, not proven truth,
automatic cross-language entity resolution, financial data or LLM translation.
Everything is held and never sent. Live retrieval is a separate bounded runner.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime,timezone
from hashlib import sha256
from urllib.parse import urlsplit
from v2_article_body_gate import extract_body,article_evidence
from v2_b87_topic_bridge import editorial_topic
from v2_evidence import _time,make_article,make_excerpt,make_claim,make_event,canonical_article_url
from v2_evidence_ledger import EvidenceLedger
from v2_editorial import plan_edition
from v2_product_compiler import compile_daily
from v2_naysayer import build_report
from v2_b46_delta_identity import versions_from_signed_journal,review_only_cross_language_pairs

ALLOWED={
    "english":{"source_id":"en-001","hosts":frozenset({"www.bbc.com","www.bbc.co.uk"}),"language":"en"},
    "arabic":{"source_id":"ar-s003","hosts":frozenset({"www.aljazeera.net"}),"language":"ar"}
}
# Independent source identities shared by the live collector and evidence compiler.
# Fallback is activated only after the original publisher fails to yield a usable article.
SOURCE_CATALOG={
    "english":(
        {"publisher_id":"bbc-en","source_id":"en-001",
         "feed_url":"https://feeds.bbci.co.uk/news/world/rss.xml",
         "hosts":frozenset({"www.bbc.com","www.bbc.co.uk"}),"language":"en"},
        {"publisher_id":"dw-en","source_id":"en-002",
         "feed_url":"https://rss.dw.com/rdf/rss-en-world",
         "hosts":frozenset({"www.dw.com"}),"language":"en"},
    ),
    "arabic":(
        {"publisher_id":"aljazeera-ar","source_id":"ar-s003",
         "feed_url":"https://www.aljazeera.net/aljazeerarss/ar/all.xml",
         "hosts":frozenset({"www.aljazeera.net"}),"language":"ar"},
        {"publisher_id":"bbc-ar","source_id":"ar-s004",
         "feed_url":"https://feeds.bbci.co.uk/arabic/rss.xml",
         "hosts":frozenset({"www.bbc.com","www.bbc.co.uk"}),"language":"ar"},
    ),
}

def _stamp(text):
    return datetime.fromisoformat(_time(text)).astimezone(timezone.utc)

def _verify_source_candidate(item):
    if not isinstance(item,dict) or item.get('product') not in ALLOWED:
        raise ValueError('unsupported_source_product')
    allowed=next((source for source in SOURCE_CATALOG[item['product']]
                  if source['source_id']==item.get('source_id')),None)
    if allowed is None:
        raise ValueError('source_identity_mismatch')
    url=item.get('article_url')
    if not isinstance(url,str):raise ValueError('invalid_source_article')
    try:p=urlsplit(url)
    except ValueError as exc:raise ValueError('invalid_source_article') from exc
    if p.scheme!='https' or p.hostname not in allowed['hosts'] or p.username or p.password or p.port not in (None,443):
        raise ValueError('wrong_article_publisher')
    text=item.get('title')
    if not isinstance(text,str) or not 8<=len(text)<=300:raise ValueError('invalid_source_headline')
    if not isinstance(item.get('html_bytes'),bytes) or len(item['html_bytes'])>850000:
        raise ValueError('invalid_article_capture_bytes')
    return allowed

def compile_captured_articles(captures:list[dict],*,as_of:str,slot_id:str,
                              previous_versions:dict|None=None, prior_snapshot:dict|None=None,
                              market_observations:list[dict]|None=None)->dict:
    now=_stamp(as_of);_stamp(slot_id)
    if not isinstance(captures,list) or len(captures)>20:
        raise ValueError('invalid_article_capture_batch')
    if previous_versions is not None and not isinstance(previous_versions,dict):
        raise ValueError('invalid_previous_versions')
    if market_observations is not None and (not isinstance(market_observations,list)
                                            or len(market_observations)>12):
        raise ValueError('invalid_v1_market_context')
    operator_prior=versions_from_signed_journal(prior_snapshot,as_of=as_of) if prior_snapshot is not None else None
    ledger=EvidenceLedger(max_observations=25)
    annotations={'english':[],'arabic':[]}
    accepted=[];held=Counter();seen=set()
    for item in captures:
        config=_verify_source_candidate(item)
        url=item['article_url']
        # Different tracking links must not masquerade as independent stories.
        canonical=canonical_article_url(url)
        if canonical in seen:
            held['repeated_canonical_article_url']+=1;continue
        seen.add(canonical)
        pub=_stamp(item['published_at'])
        if not -300<=(now-pub).total_seconds()<=48*3600:
            held['stale_or_future_article']+=1;continue
        try:
            body=extract_body(item['html_bytes'],source_url=url,language=config['language'])
            source_quote=article_evidence(body,headline=item['title'],published_at=item['published_at'])
        except ValueError as exc:
            held[str(exc)[:80]]+=1;continue
        original=make_article(source_id=item['source_id'],url=url,
                    original_text=body['original_text'],original_language=config['language'],
                    retrieved_at=as_of,published_at=item['published_at'])
        quote=source_quote['quote']
        at=original['original_text'].find(quote)
        if at<0:held['quote_not_in_captured_article']+=1;continue
        excerpt=make_excerpt(original,at,at+len(quote))
        claim=make_claim(statement=quote,excerpts=[excerpt],kind='publisher_assertion')
        ledger.observe(original)
        ledger.attach_excerpt(excerpt)
        ledger.attach_claim(claim)
        # Different publishers are intentionally never auto-merged by similarity.
        explicit='article-'+original['article_id'][4:]
        event=make_event(key=explicit,claims=[claim])
        ledger.upsert_event(event)
        annotations[item['product']].append({
            'event_id':event['event_id'],'region':source_quote['region'],
            'subject_country':source_quote['subject_country'],
            'topic':editorial_topic(item['product'],source_quote['topic_english' if item['product']=='english' else 'topic_arabic']),
            'priority':50
        })
        accepted.append({'source_id':item['source_id'],'product':item['product'],
            'article_id':original['article_id'],'revision_id':original['revision_id'],
            'excerpt_id':excerpt['excerpt_id'],'event_id':event['event_id'],
            'original_body_sha256':body['body_sha256'],
            'publisher_attributed_only':True})
    products={}
    for product in ('english','arabic'):
        plan=plan_edition(ledger=ledger,annotations=annotations[product],product=product,
                 slot_id=slot_id,as_of=as_of,previous_versions=operator_prior['versions'] if operator_prior is not None else None,
                 max_items=6)
        critic=build_report([],ledger=ledger,as_of=as_of,verified_families={},
                    verified_languages={},product=product,cadence='daily',slot_id=slot_id)
        daily=compile_daily(editorial_plan=plan,critic_report=critic,
                            market_observations=(market_observations or []) if product=='english' else [])
        products[product]={'story_count':len(daily['stories']),'held_reasons':plan['held_reasons'],
            'represented_regions':plan['represented_regions'],
            'newsroom':daily,'critique':critic,'editorial_plan':plan,'no_publication_authority':True}
    cross_language=review_only_cross_language_pairs(products)
    return {'schema':'aggregateit-v2-b46-article-editorial/1','captured_article_count':len(captures),
            'admitted_articles':len(accepted),'receipts':accepted,'held_reasons':dict(held),
            'ledger_counters':ledger.counters(),'products':products,
            'previous_versions_present':previous_versions is not None,
            'unattested_previous_versions_ignored':previous_versions is not None,
            'prior_baseline_authenticated':operator_prior is not None,
            'operator_baseline_hmac_verified':operator_prior is not None,
            'prior_baseline_off_host_retention_verified':False,
            'baseline_anchor_sha256':operator_prior['prior_anchor_sha256'] if operator_prior else None,
            'cross_language_review':cross_language,
            'headline_semantic_alignment_verified':False,
            'publisher_independence_verified':False,
            'source_story_factual_accuracy_verified':False,
            'semantic_cross_language_event_merge_verified':False,
            'live_model_translation_verified':False,
            'market_data_live_verified':False,'can_send':False,
            'discord_sent':False,'production_modified':False}

def metrics_only(result):
    if result.get('schema')!='aggregateit-v2-b46-article-editorial/1' or result.get('can_send') is not False:
        raise ValueError('untrusted_editorial_receipt')
    return {'schema':'aggregateit-v2-b46-metrics-only/1',
            'captured_articles':result['captured_article_count'],
            'admitted_articles':result['admitted_articles'],
            'held_reasons':result['held_reasons'],
            'ledger_counters':result['ledger_counters'],
            'evidence_hashes':[{'source_id':x['source_id'],'product':x['product'],
                 'article_id':x['article_id'],'excerpt_id':x['excerpt_id'],
                 'event_id':x['event_id'],'body_sha256':x['original_body_sha256']}
                 for x in result['receipts']],
            'products':{product:{'held_reasons':r['held_reasons'],
                'story_count':r['story_count'],'represented_regions':r['represented_regions'],
                'market_status':r['newsroom']['market_data_status'],
                'naysayer_status':r['newsroom']['naysayer_status']}
                for product,r in result['products'].items()},
            'operator_baseline_hmac_verified':result['operator_baseline_hmac_verified'],
            'prior_baseline_off_host_retention_verified':False,
            'cross_language_review_candidate_count':result['cross_language_review']['candidate_count'],
            'cross_language_automatic_merges':0,
            'real_model_translation_pending':True,
            'model_called':False,'discord_sent':False,'can_release':False}
