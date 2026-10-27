"""B38 isolated real-byte V1/V2 parser and headline-view comparison. NO DELIVERY.

Each public feed is fetched once; actual V1 and V2 parsing use the identical
in-memory buffer. Only counts/digests, never titles, bodies or feed XML, enter
the JSON artifact. Models, native editions and delivery are NOT compared.
"""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from urllib.error import HTTPError
from v2_b31_same_input_shadow import compare_exact_input
from v2_b37_mobile_headlines import render_source_watch_html
from v2_feed_items import extract_candidates
from v2_feed_probe import _date, _url_safe
from v2_secure_transport import pinned_https_fetch

SOURCES = (
    ('english','bbc-world','https://feeds.bbci.co.uk/news/world/rss.xml'),
    ('arabic','aljazeera-ar','https://www.aljazeera.net/aljazeerarss/ar/all.xml'),
)
MAX_BYTES = 1_000_000

def compare_captured_headlines(raw: bytes, *, product: str, feed_url: str,
                               observed_at: str) -> dict:
    if product not in ('english','arabic') or not isinstance(raw,bytes) or not 1<=len(raw)<=MAX_BYTES:
        raise ValueError('invalid_exact_capture')
    _url_safe(feed_url)
    if _date(observed_at) is None:
        raise ValueError('invalid_observation_time')
    v1v2=compare_exact_input(raw,feed_url=feed_url,observed_at=observed_at,product=product)
    v2=extract_candidates(raw,feed_url=feed_url,observed_at=observed_at,
                          max_items=(5 if product=='english' else 35),
                          max_age_hours=72,max_bytes=MAX_BYTES)
    view=render_source_watch_html(product,v2['items'],observed_at)
    return {'schema':'aggregateit-v2-b38-exact-input/1','product':product,
            'input_sha256':sha256(raw).hexdigest(),'input_bytes':len(raw),
            'observed_at':observed_at,'same_exact_input':True,
            'v1_reference_blob_verified':v1v2['v1_parser_blob_verified'],
            'v1_eligible':v1v2['v1_window_eligible'],
            'v2_eligible':v1v2['v2_window_eligible'],
            'matching_items':v1v2['matching_items'],
            'v1_only_count':len(v1v2['v1_only']),
            'v2_only_count':len(v1v2['v2_only']),
            'parser_status':'MATCH' if v1v2['parser_alignment'] else 'HOLD_MISMATCH',
            'mobile_cards':view['shown'],'native_language_gate_filtered':view['script_filtered'],
            'headline_preview_generated':True,'full_edition_comparable':False,
            'model_or_translation_compared':False,'rendered_native_png_compared':False,
            'authenticated_delivery_compared':False,'discord_sent':False,
            'can_publish':False,'raw_bytes_retained':False}

def _failure_code(exc: Exception) -> str:
    if isinstance(exc,HTTPError):return 'http_'+str(exc.code)
    if isinstance(exc,TimeoutError):return 'timeout'
    if isinstance(exc,ValueError):return 'invalid_source_or_parsing'
    if isinstance(exc,OSError):return 'network_io_failure'
    return 'comparison_runtime_failure'

def run_live_pairs() -> dict:
    observed_at=datetime.now(timezone.utc).isoformat()
    results=[]
    for product,label,url in SOURCES:
        row={'product':product,'source_label':label,'status':'HOLD','feed_url':url}
        try:
            packet=pinned_https_fetch(url,timeout=9,max_bytes=MAX_BYTES,max_redirects=1,
                         headers={'Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml'})
            finding=compare_captured_headlines(packet['body'],product=product,
                           feed_url=packet['final_url'],observed_at=observed_at)
            row.update(finding)
            row['status']=('COMPARED' if finding['parser_status']=='MATCH' and finding['v2_eligible']>0
                           else 'PARSER_MISMATCH' if finding['parser_status']!='MATCH'
                           else 'NO_ELIGIBLE_HEADLINES')
            row['http_status']=packet['status']
        except Exception as exc:
            row['failure_class']=_failure_code(exc)
        results.append(row)
    parity=all(r['status']=='COMPARED' for r in results)
    return {'schema':'aggregateit-v2-b38-live-parser-pair/1',
            'status':'COMPARED' if parity else 'HOLD',
            'observed_at':observed_at,'source_count':len(results),'results':results,
            'parity_all':parity,'full_v1_v2_editorial_delivery_accepted':False,
            'news_factual_accuracy_measured':False,'raw_source_bytes_persisted':False,
            'discord_sent':False,'can_release':False}

def main() -> int:
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True)
    ns=ap.parse_args()
    result=run_live_pairs()
    dest=Path(ns.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(json.dumps({'schema':result['schema'],'status':result['status'],
                      'results':[{'source_label':r['source_label'],'status':r['status'],
                                  'failure_class':r.get('failure_class'),
                                  'v1_eligible':r.get('v1_eligible'),
                                  'v2_eligible':r.get('v2_eligible')} for r in result['results']]},ensure_ascii=False))
    return 0

if __name__=='__main__':raise SystemExit(main())
