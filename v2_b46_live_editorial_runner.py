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
from v2_article_body_gate import extract_body, article_evidence, headline_geography_candidates

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
                        'article_http_ok':0,'capture_successes':0,
                        'headlines_with_one_supported_country':0,'headline_country_unclassified':0,
                        'article_evidence_eligible':0,'body_gate_rejections':{}}
        try:
            response=pinned_https_fetch(feed,timeout=8,max_bytes=1_000_000,max_redirects=1,
                headers={'Accept':'application/rss+xml, application/xml, text/xml'})
            parsed=extract_candidates(response['body'],feed_url=response['final_url'],
                   observed_at=observed,max_items=30,max_bytes=1_000_000)
            count[product]['feed_ok']=True
        except Exception as exc:
            reasons[product+'-feed']=type(exc).__name__;continue
        # Target explicitly named regions instead of blindly choosing the first
        # three global stories. The same headline + article-body gate still
        # makes the final decision; unsupported or multiple countries HOLD.
        eligible_headlines=[]
        for item in parsed['items']:
            country_matches=headline_geography_candidates(item['title'],language=ALLOWED[product]['language'])
            if len(country_matches)==1:
                eligible_headlines.append(item)
                count[product]['headlines_with_one_supported_country']+=1
            else:
                count[product]['headline_country_unclassified']+=1
        for candidate in eligible_headlines:
            if count[product]['article_attempts']>=6 or count[product]['article_evidence_eligible']>=3:
                break
            url=candidate['article_url']
            from urllib.parse import urlsplit
            if urlsplit(url).hostname not in ALLOWED[product]['hosts']:
                continue
            count[product]['article_attempts']+=1
            try:
                page=pinned_https_fetch(url,timeout=8,max_bytes=850000,max_redirects=1,
                     headers={'Accept':'text/html'})
                count[product]['article_http_ok']+=1
                capture={'product':product,
                      'source_id':ALLOWED[product]['source_id'],
                      'article_url':url,'title':candidate['title'],
                      'published_at':candidate['published_at'],'html_bytes':page['body']}
                try:
                    body=extract_body(page['body'],source_url=url,language=ALLOWED[product]['language'])
                    article_evidence(body,headline=candidate['title'],published_at=candidate['published_at'])
                except ValueError as exc:
                    code=str(exc)[:80]
                    count[product]['body_gate_rejections'][code]=count[product]['body_gate_rejections'].get(code,0)+1
                    continue
                captures.append(capture)
                count[product]['capture_successes']+=1
                count[product]['article_evidence_eligible']+=1
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
                      'held_reasons':result['editorial']['held_reasons'],
                      'editorial_held':{p:r['held_reasons'] for p,r in result['editorial']['products'].items()},
                      'products':{p:r['story_count'] for p,r in result['editorial']['products'].items()},
                      'can_release':False},ensure_ascii=False))
