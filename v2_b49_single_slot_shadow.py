"""B49 genuine SAME-RSS-byte V1/V2 parsers and V2 held newsroom replay.

The full V1 newsroom/model/render/Discord equivalent is not present.
This proof can authenticate a source-byte join within the runner, NOT
production factual quality or a same-edition V1/V2 quality score.
"""
from __future__ import annotations
from datetime import datetime,timezone
from hashlib import sha256
from v2_b38_live_pair import SOURCES,MAX_BYTES,compare_captured_headlines
from v2_b40_shared_preview import compare_previews
from v2_secure_transport import pinned_https_fetch
from v2_b46_live_editorial_runner import run

def evaluate_shared_shadow(parser:dict, preview:dict, newsroom:dict, *,
                           expected_source_sha256:str,product:str)->dict:
    if product not in ('english','arabic'):
        raise ValueError('invalid_shadow_product')
    if not isinstance(expected_source_sha256,str) or len(expected_source_sha256)!=64:
        raise ValueError('invalid_source_digest')
    if (not isinstance(parser,dict) or parser.get('schema')!='aggregateit-v2-b38-exact-input/1'
        or parser.get('product')!=product
        or not isinstance(preview,dict) or preview.get('schema')!='aggregateit-v2-b40-shared-input-headline-preview/1'
        or preview.get('product')!=product
        or not isinstance(newsroom,dict) or newsroom.get('schema')!='aggregateit-v2-b46-live-chain/1'):
        raise ValueError('untrusted_shadow_evidence')
    if (parser.get('input_sha256')!=expected_source_sha256 or
        preview.get('capture_sha256')!=expected_source_sha256 or
        newsroom.get('rss_feed_sha256',{}).get(product)!=expected_source_sha256 or
        newsroom.get('rss_shared_snapshot_supplied') is not True):
        raise ValueError('not_exact_same_source_bytes')
    if parser.get('can_publish') is not False or preview.get('can_send') is not False or newsroom.get('can_release') is not False:
        raise ValueError('forged_shadow_authority')
    if parser.get('v1_reference_blob_verified') is not True:
        raise ValueError('unverified_legacy_reference_blob')
    counts=newsroom.get('editorial',{}).get('products',{}).get(product)
    if not isinstance(counts,dict) or type(counts.get('story_count')) is not int:
        raise ValueError('missing_v2_editorial_counts')
    parser_equal=parser.get('parser_status')=='MATCH'
    preview_equal=preview.get('identity_parity') is True
    return {'schema':'aggregateit-v2-b49-source-joined/1',
            'product':product,'source_sha256':expected_source_sha256,
            'v1_v2_parser_parity':parser_equal,
            'v1_v2_headline_identity_parity':preview_equal,
            'v1_only':parser.get('v1_only_count'),'v2_only':parser.get('v2_only_count'),
            'v2_source_linked_daily_stories':counts['story_count'],
            'v2_four_product_held':newsroom.get('four_products',{}).get('schema')=='aggregateit-v2-b47-four-product-held/1',
            'actual_v1_full_editorial_executed':False,
            'actual_v1_full_native_rendered':False,
            'v1_v2_model_translation_quality_compared':False,
            'authenticated_real_discord_receipts_compared':False,
            'full_same_slot_comparison_status':'HOLD_MISSING_V1_FULL_SYSTEM_EVIDENCE',
            'independent_publisher_factuality_verified':False,
            'owner_cutover_authorized':False,'can_release':False}

def run_one_slot(*,production_baseline=None,candidate_root=None):
    if (production_baseline is None)!=(candidate_root is None):
        raise ValueError('both_production_and_candidate_roots_required')
    at=datetime.now(timezone.utc).isoformat()
    packets={}; parser={}; previews={};failures={}
    for product,label,url in SOURCES:
        try:
            response=pinned_https_fetch(url,timeout=9,max_bytes=MAX_BYTES,max_redirects=1,
                headers={'Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml'})
            raw=response['body']
            packets[product]={'feed_url':url,'body':raw}
            parser[product]=compare_captured_headlines(raw,product=product,
                                     feed_url=url,observed_at=at)
            previews[product]=compare_previews(raw,product=product,
                                     feed_url=url,observed_at=at)
        except Exception as exc:
            failures[label]=type(exc).__name__
    if len(packets)!=2:
        return {'schema':'aggregateit-v2-b49-single-slot-preflight/1',
                'status':'HOLD_SOURCE_CAPTURE_FAILED',
                'failures':failures,
                'source_count':len(packets),'can_release':False,
                'discord_sent':False}
    newsroom=run(render_four_products=True,rss_snapshots=packets,observed_at=at)
    rows=[]
    for product,_,_ in SOURCES:
        digest=sha256(packets[product]['body']).hexdigest()
        rows.append(evaluate_shared_shadow(parser[product],previews[product],newsroom,
                  expected_source_sha256=digest,product=product))
    operational=None
    if production_baseline is not None:
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from v2_b41_production_preflight import inspect_workflows
        from v2_b39_rollback_rehearsal import exercise_durable_no_send
        from v2_b48_operations_readiness import evaluate_operations
        production=inspect_workflows(baseline_root=Path(production_baseline),
                                     candidate_root=Path(candidate_root))
        with TemporaryDirectory(prefix='aggregateit-b49-opslab-') as tmp:
            durable=exercise_durable_no_send(Path(tmp),slot_id=at)
        if newsroom.get('four_products',{}).get('schema')!='aggregateit-v2-b47-four-product-held/1':
            raise ValueError('cannot_operationally_assess_missing_four_products')
        operational=evaluate_operations(newsroom['four_products'],production,durable,observed_at=at)
        if operational.get('can_release') is not False:
            raise ValueError('ops_preflight_cannot_grant_release')
    return {'schema':'aggregateit-v2-b49-single-slot-preflight/1',
            'status':'HOLD_NO_FULL_V1_EDITORIAL_BASELINE',
            'rows':rows,'observed_at':at,
            'operational_preflight':operational,
            'same_live_capture_used_for_b47_b48_b49':production_baseline is not None,
            'unique_feed_network_requests':2,
            'rss_capture_join_verified':True,
            'same_slot_v2_editorial_no_post':True,
            'v1_v2_full_editorial_model_render_delivery_matched':False,
            'all_parser_parity':all(r['v1_v2_parser_parity'] for r in rows),
            'all_source_headline_parity':all(r['v1_v2_headline_identity_parity'] for r in rows),
            'v2_four_products_held':all(r['v2_four_product_held'] for r in rows),
            'production_operational_evidence_accepted':False,
            'raw_publisher_bytes_persisted':False,
            'llm_api_called':False,'discord_sent':False,
            'can_release':False}
