"""B46 one-pass genuine publisher HTML evidence -> B3/B4 -> held no-post metrics.

Only BBC World and Al Jazeera Arabic as established in V2; bounded feed and
article attempts. No title, body, translation or HTML is persisted in artifacts.
"""
import json
from hashlib import sha256
from datetime import datetime,timezone
from pathlib import Path
from v2_feed_items import extract_candidates
from v2_secure_transport import pinned_https_fetch
from v2_b46_live_editorial import compile_captured_articles,metrics_only,ALLOWED,SOURCE_CATALOG
from v2_article_body_gate import extract_body, article_evidence, headline_geography_candidates

FEEDS=(
    ('english','https://feeds.bbci.co.uk/news/world/rss.xml'),
    ('arabic','https://www.aljazeera.net/aljazeerarss/ar/all.xml'),
)
def run(*,render_native=False,render_four_products=False,
        rss_snapshots=None,observed_at=None,visual_archive_dir=None,fetch=None,
        market_snapshot=None,compare_same_capture=False):
    if rss_snapshots is not None:
        if not isinstance(rss_snapshots,dict) or set(rss_snapshots)!={'english','arabic'}:
            raise ValueError('incomplete_shared_rss_snapshots')
        for product,feed in FEEDS:
            row=rss_snapshots[product]
            if (not isinstance(row,dict) or row.get('feed_url')!=feed
                or not isinstance(row.get('body'),bytes) or not 1<=len(row['body'])<=1_000_000):
                raise ValueError('unsafe_shared_rss_snapshot')
    if observed_at is not None:
        from v2_evidence import _time
        observed=_time(observed_at)
    else:
        observed=datetime.now(timezone.utc).isoformat()
    slot=observed
    captures=[];reasons={};count={};feed_digests={};source_recovery={}
    frozen_feeds=[];frozen_pages=[]
    fetcher=fetch or pinned_https_fetch
    for product,primary_feed in FEEDS:
        primary=SOURCE_CATALOG[product][0]
        if primary["feed_url"]!=primary_feed:
            raise ValueError("primary_feed_contract_mismatch")
        count[product]={'feed_attempted':True,'feed_ok':False,'article_attempts':0,
                        'article_http_ok':0,'capture_successes':0,
                        'headlines_with_one_supported_country':0,'headline_country_unclassified':0,
                        'article_evidence_eligible':0,
                        'editorial_relevance_precheck_rejections':0,
                        'body_gate_rejections':{}}
        recovery={'primary_publisher':primary['publisher_id'],'selected_publisher':None,
                  'fallback_attempted':False,'fallback_used':False,'attempts':[]}
        source_recovery[product]=recovery
        for position,source in enumerate(SOURCE_CATALOG[product]):
            if position>0 and (count[product]['article_evidence_eligible']>0
                               or (rss_snapshots is not None and fetch is None)):
                # Snapshots without an injected fetch are fully offline.
                break
            if position>0:recovery['fallback_attempted']=True
            row={'publisher_id':source['publisher_id'],'feed_ok':False,
                 'article_attempts':0,'eligible_articles':0}
            recovery['attempts'].append(row)
            feed=source['feed_url']
            try:
                if position==0 and rss_snapshots is not None:
                    raw=rss_snapshots[product]['body']
                    resolved_url=feed
                else:
                    response=fetcher(feed,timeout=8,max_bytes=1_000_000,max_redirects=1,
                        headers={'Accept':'application/rss+xml, application/xml, text/xml'})
                    raw=response['body']
                    resolved_url=response['final_url']
                feed_digests[product if position==0 else product+':'+source['publisher_id']]=sha256(raw).hexdigest()
                parsed=extract_candidates(raw,feed_url=resolved_url,
                    observed_at=observed,max_age_hours=48,max_items=30,max_bytes=1_000_000)
                if compare_same_capture:
                    frozen_feeds.append({'product':product,'source_id':source['source_id'],'body':bytes(raw)})
                row['feed_ok']=True
                count[product]['feed_ok']=True
            except Exception as exc:
                reasons[product+'-'+source['publisher_id']+'-feed']=type(exc).__name__
                continue
            eligible_headlines=[]
            geography_deferred=[]
            for item in parsed['items']:
                matches=headline_geography_candidates(item['title'],language=source['language'])
                if len(matches)==1:
                    eligible_headlines.append(item)
                    count[product]['headlines_with_one_supported_country']+=1
                else:
                    count[product]['headline_country_unclassified']+=1
                    # Headlines may omit a country while the attributed article
                    # identifies one. Defer only a bounded sample to body evidence.
                    if product=='arabic' and len(matches)==0 and len(geography_deferred)<3:
                        geography_deferred.append(item)
            if product=='arabic':
                eligible_headlines.extend(geography_deferred)
                count[product]['deferred_geography_article_candidates']=len(geography_deferred)
            for candidate in eligible_headlines:
                if row['article_attempts']>=6 or row['eligible_articles']>=3:
                    break
                url=candidate['article_url']
                from urllib.parse import urlsplit
                try:
                    if urlsplit(url).hostname not in source['hosts']:
                        continue
                except ValueError:
                    continue
                row['article_attempts']+=1
                count[product]['article_attempts']+=1
                try:
                    page=fetcher(url,timeout=8,max_bytes=850000,max_redirects=1,
                                 headers={'Accept':'text/html'})
                    count[product]['article_http_ok']+=1
                    capture={'product':product,'source_id':source['source_id'],
                        'article_url':url,'title':candidate['title'],
                        'published_at':candidate['published_at'],'html_bytes':page['body']}
                    if compare_same_capture:
                        frozen_pages.append(dict(capture))
                    try:
                        body=extract_body(page['body'],source_url=url,language=source['language'])
                        source_quote=article_evidence(body,headline=candidate['title'],
                                                      published_at=candidate['published_at'])
                    except ValueError as exc:
                        code=str(exc)[:80]
                        rejected=count[product]['body_gate_rejections']
                        rejected[code]=rejected.get(code,0)+1
                        continue
                    # Evaluate the same Arabic relevance decision used by the
                    # compiler BEFORE declaring the publisher a successful
                    # recovery. Otherwise a rejected article masks fallback.
                    if product=='arabic':
                        from v2_event_intelligence import arabic_filter
                        relevance=arabic_filter(candidate['title']+' '+body['original_text'][:500],
                                                region=source_quote['region'],
                                                headline=candidate['title'],
                                                lead=body['original_text'][:1200])
                        if not relevance['admit']:
                            count[product]['editorial_relevance_precheck_rejections']+=1
                            rejected=count[product]['body_gate_rejections']
                            key='editorial_'+relevance['reason']
                            rejected[key]=rejected.get(key,0)+1
                            continue
                    # The primary preserves the existing independently tested
                    # source filter. Secondary is checked here AND rechecked by
                    # the publisher-aware editorial compiler.
                    if position==0:
                        from v2_b98_source_fallback import choose_eligible
                        fallback=choose_eligible(product,[capture],max_attempts=1)
                        if fallback['status']!='ELIGIBLE_SOURCE_BACKED_CANDIDATE':
                            rejected=count[product]['body_gate_rejections']
                            rejected['primary_fallback_not_eligible']=rejected.get('primary_fallback_not_eligible',0)+1
                            continue
                    captures.append(capture)
                    row['eligible_articles']+=1
                    count[product]['capture_successes']+=1
                    count[product]['article_evidence_eligible']+=1
                except Exception as exc:
                    reasons[product+'-'+source['publisher_id']+'-article-'+str(row['article_attempts'])]=type(exc).__name__
            if row['eligible_articles']:
                recovery['selected_publisher']=source['publisher_id']
                recovery['fallback_used']=position>0
                break
    # Independent pre-admission failures should not be interpreted as factual reliability.
    # Reuse V1 market cache when present; no new API request and no guessed
    # market figures. Stale/invalid inputs are withheld by the bridge.
    from market import load_market_pulse,load_macro_pulse
    if market_snapshot is None:
        market_snapshot=load_market_pulse()
    macro_snapshot=load_macro_pulse()
    from v2_market_bridge import convert_v1_market_pulse
    markets=convert_v1_market_pulse(market_snapshot,as_of=observed)
    result=compile_captured_articles(captures,as_of=observed,slot_id=slot,
                                     market_observations=markets)
    receipt=metrics_only(result)
    paired={'status':'NOT_REQUESTED'}
    if compare_same_capture:
        from v2_b115_same_capture import compare_same_capture as compare_frozen
        paired=compare_frozen(frozen_feeds,frozen_pages,observed_at=observed)
    native={"status":"NOT_REQUESTED"}
    if render_native:
        if all(result["products"][p]["story_count"]>0 for p in ("english","arabic")):
            try:
                from tempfile import TemporaryDirectory
                from v2_b46_native_held import render_genuine_held
                with TemporaryDirectory(prefix="v2-b46-source-native-") as temp:
                    native=render_genuine_held(result,output_dir=Path(temp)/"native",
                                               pulse_snapshot=market_snapshot,
                                               macro_snapshot=macro_snapshot)
            except Exception as exc:
                native={"status":"HOLD_NATIVE_RENDER_ERROR","error_class":type(exc).__name__}
        else:
            native={"status":"HOLD_MISSING_SOURCE_BACKED_LANGUAGE"}

    four_products={"status":"NOT_REQUESTED"}
    if render_four_products:
        if all(result["products"][p]["story_count"]>0 for p in ("english","arabic")):
            try:
                from tempfile import TemporaryDirectory
                from v2_b47_four_product_held import compose_held_products
                with TemporaryDirectory(prefix="v2-b47-four-products-") as temp:
                    output=Path(visual_archive_dir) if visual_archive_dir is not None else Path(temp)/"native"
                    four_products=compose_held_products(result,output_dir=output,as_of=observed,
                                                        pulse_snapshot=market_snapshot,
                                                        macro_snapshot=macro_snapshot)
                    if visual_archive_dir is not None:
                        from v2_b86_visual_archive import validate_page_archive
                        four_products['visual_archive']=validate_page_archive(output)
            except Exception as exc:
                four_products={"status":"HOLD_FOUR_PRODUCT_INTEGRATION","error_class":type(exc).__name__}
        else:
            four_products={"status":"HOLD_MISSING_GENUINE_BILINGUAL_EVIDENCE"}
    arabic_count=count['arabic']
    arabic_stories=receipt['products']['arabic']['story_count']
    arabic_zero_diagnosis={
        'status':'HOLD_NO_ELIGIBLE_ARABIC_STORIES' if arabic_stories==0 else 'ARABIC_STORIES_SELECTED',
        'counts':dict(arabic_count),
        'publisher_attempts':source_recovery['arabic']['attempts'],
        'editorial_held_reasons':receipt['products']['arabic']['held_reasons'],
        'article_admission_held_reasons':receipt['held_reasons'],
        'inference_only':True,
        'full_v1_arabic_parity_verified':False}
    return {'schema':'aggregateit-v2-b46-live-chain/1',
        'observed_at':observed,'source_attempts':count,'source_recovery':source_recovery,
        'arabic_zero_story_diagnosis':arabic_zero_diagnosis,
        'v1_market_context_observation_count':len(markets),
        'rss_feed_sha256':feed_digests,
        'b115_same_capture':paired,
        'rss_shared_snapshot_supplied':rss_snapshots is not None,
        'transport_failures':reasons,'editorial':receipt,'native':native,'four_products':four_products,
        'b45_provider_fallback_connectivity':'NOT_RUN_NO_CREDENTIALS',
        'b45_english_to_arabic_semantic_test':'NOT_RUN',
        'b45_somali_to_arabic_semantic_test':'NOT_RUN',
        'tradingview_live_market_data':'NOT_RUN',
        'naysayer_generation':'WITHHELD_INSUFFICIENT_EVIDENCE',
        'publisher_bytes_persisted':False,'discord_sent':False,
        'can_release':False}
if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);a.add_argument('--render-held',action='store_true');a.add_argument('--four-products',action='store_true');a.add_argument('--same-capture',action='store_true');a.add_argument('--visual-archive-dir',type=Path);args=a.parse_args()
    result=run(render_native=args.render_held,render_four_products=args.four_products,visual_archive_dir=args.visual_archive_dir,compare_same_capture=args.same_capture)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'source_attempts':result['source_attempts'],
                      'source_recovery':result['source_recovery'],
                      'v1_market_context_observation_count':result['v1_market_context_observation_count'],
                      'admitted':result['editorial']['admitted_articles'],
                      'held_reasons':result['editorial']['held_reasons'],
                      'editorial_held':{p:r['held_reasons'] for p,r in result['editorial']['products'].items()},
                      'products':{p:r['story_count'] for p,r in result['editorial']['products'].items()},
                      'native_status':result['native']['status'],
                      'native_pages':len(result['native'].get('native_pages',[])),
                      'four_products':result['four_products'].get('schema',result['four_products'].get('status')),
                      'four_product_error_class':result['four_products'].get('error_class'),
                      'weekly_days':{k:v['days_with_real_daily_snapshots'] for k,v in result['four_products'].get('weekly',{}).items()},
                      'can_release':False},ensure_ascii=False))
