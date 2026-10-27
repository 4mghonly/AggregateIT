"""B46 one-pass genuine publisher HTML evidence -> B3/B4 -> held no-post metrics.

Only BBC World and Al Jazeera Arabic as established in V2; bounded feed and
article attempts. No title, body, translation or HTML is persisted in artifacts.
"""
import json
from datetime import datetime,timezone
from pathlib import Path
from v2_feed_items import extract_candidates
from v2_secure_transport import pinned_https_fetch
from v2_b46_live_editorial import compile_captured_articles,metrics_only,ALLOWED

FEEDS=(
    ('english','https://feeds.bbci.co.uk/news/world/rss.xml'),
    ('arabic','https://www.aljazeera.net/aljazeerarss/ar/all.xml'),
)
def run():
    at=datetime.now(timezone.utc)
    slot=at.isoformat()
    observed=at.isoformat()
    captures=[];reasons={};count={}
    for product,feed in FEEDS:
        count[product]={'feed_attempted':True,'feed_ok':False,'article_attempts':0,
                        'article_http_ok':0,'capture_successes':0}
        try:
            response=pinned_https_fetch(feed,timeout=8,max_bytes=1_000_000,max_redirects=1,
                headers={'Accept':'application/rss+xml, application/xml, text/xml'})
            parsed=extract_candidates(response['body'],feed_url=response['final_url'],
                   observed_at=observed,max_items=30,max_bytes=1_000_000)
            count[product]['feed_ok']=True
        except Exception as exc:
            reasons[product+'-feed']=type(exc).__name__;continue
        # Use at most 6 attempts per publisher; bounded one pass and no retries.
        for candidate in parsed['items'][:6]:
            if count[product]['capture_successes']>=3:break
            url=candidate['article_url']
            from urllib.parse import urlsplit
            if urlsplit(url).hostname not in ALLOWED[product]['hosts']:
                continue
            count[product]['article_attempts']+=1
            try:
                page=pinned_https_fetch(url,timeout=8,max_bytes=850000,max_redirects=1,
                     headers={'Accept':'text/html'})
                count[product]['article_http_ok']+=1
                captures.append({'product':product,
                      'source_id':ALLOWED[product]['source_id'],
                      'article_url':url,'title':candidate['title'],
                      'published_at':candidate['published_at'],'html_bytes':page['body']})
                count[product]['capture_successes']+=1
            except Exception as exc:
                reasons[product+'-article-'+str(count[product]['article_attempts'])]=type(exc).__name__
    # Independent pre-admission failures should not be interpreted as factual reliability.
    result=compile_captured_articles(captures,as_of=observed,slot_id=slot)
    receipt=metrics_only(result)
    return {'schema':'aggregateit-v2-b46-live-chain/1',
        'observed_at':observed,'source_attempts':count,
        'transport_failures':reasons,'editorial':receipt,
        'b45_provider_fallback_connectivity':'NOT_RUN_NO_CREDENTIALS',
        'b45_english_to_arabic_semantic_test':'NOT_RUN',
        'b45_somali_to_arabic_semantic_test':'NOT_RUN',
        'tradingview_live_market_data':'NOT_RUN',
        'naysayer_generation':'WITHHELD_INSUFFICIENT_EVIDENCE',
        'publisher_bytes_persisted':False,'discord_sent':False,
        'can_release':False}
if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);args=a.parse_args()
    result=run()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'source_attempts':result['source_attempts'],
                      'admitted':result['editorial']['admitted_articles'],
                      'products':{p:r['story_count'] for p,r in result['editorial']['products'].items()},
                      'can_release':False},ensure_ascii=False))
