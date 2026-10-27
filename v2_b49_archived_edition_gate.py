"""B49 check original authenticated-run ZIP *content*, not same-slot equality.

No V1 raw feed snapshot or full English rendered package is assumed. A
reporting app's asserted Discord message is NOT an external Discord receipt.
The caller must independently verify the run/artifact provenance in GitHub.
"""
from __future__ import annotations
from datetime import datetime,timezone
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile,BadZipFile
import json
from PIL import Image

ARABIC_PAGES=frozenset({'arabic-p1.png','arabic-p2.png','arabic-p3.png'})

def _date(v):
    try:
        d=datetime.fromisoformat(v.replace('Z','+00:00'))
        if d.utcoffset() is None:raise ValueError('naive')
        return d.astimezone(timezone.utc).isoformat()
    except (AttributeError,TypeError,ValueError):
        raise ValueError('invalid_archived_timestamp') from None

def inspect_original_zip(raw:bytes,*,product:str,run_id:int)->dict:
    if product not in ('arabic','english') or type(run_id) is not int or run_id<100_000:
        raise ValueError('invalid_original_run')
    if not isinstance(raw,bytes) or not 100<=len(raw)<=2_500_000:
        raise ValueError('unbounded_original_artifact')
    try:z=ZipFile(BytesIO(raw))
    except BadZipFile:raise ValueError('corrupt_original_archive') from None
    with z:
        inf=z.infolist();names=[x.filename for x in inf]
        if (len(names)>20 or len(set(names))!=len(names)
            or any(x.file_size>3_000_000 or x.filename.startswith('/')
                or '..' in x.filename.split('/') for x in inf)
            or sum(x.file_size for x in inf)>5_000_000):
            raise ValueError('unsafe_original_artifact_manifest')
        if not {'health.json'}.issubset(names):raise ValueError('missing_original_health')
        health=json.loads(z.read('health.json'))
        base={'schema':'aggregateit-v2-b49-original-artifact-inventory/1',
            'source':'original_github_actions_zip','original_run_id':run_id,
            'zip_sha256':sha256(raw).hexdigest(),'product':product,
            'app_reported_delivery_is_not_discord_verified':True,
            'original_source_bytes_available':False,
            'independent_factual_review_verified':False,
            'can_release':False}
        if product=='arabic':
            if not ARABIC_PAGES.issubset(names) or 'briefing.json' not in names:
                raise ValueError('missing_original_arabic_pages')
            briefing=json.loads(z.read('briefing.json'))
            if briefing.get('sample') is not False or briefing.get('schema_version')!='arabic-brief-v3':
                raise ValueError('not_production_briefing')
            pages=[]
            for name in sorted(ARABIC_PAGES):
                b=z.read(name)
                with Image.open(BytesIO(b)) as im:
                    if im.format!='PNG' or im.size!=(3840,2160):
                        raise ValueError('wrong_original_native_image')
                    im.verify()
                pages.append({'page':name,'sha256':sha256(b).hexdigest(),
                              'width':3840,'height':2160})
            trans=health.get('translation',{})
            req=trans.get('requested_foreign');got=trans.get('translated_foreign')
            if type(req) is not int or type(got) is not int or not 0<=got<=req:
                raise ValueError('invalid_original_translation_status')
            fallback_403=sum(r.get('route')=='fallback' and r.get('error')=='http_403'
                  for r in trans.get('routes',[]) if isinstance(r,dict))
            delivery=health.get('delivery')
            return {**base,'original_window_start':_date(briefing['window_start']),
                'original_window_end':_date(briefing['window_end']),
                'native_png_receipts':pages,
                'native_page_count':len(pages),'source_events_count':len(briefing['events']),
                'foreign_translation_requested':req,'foreign_translation_completed':got,
                'foreign_translation_full':req==got,
                'fallback_403_instances':fallback_403,
                'production_app_delivery_claim':isinstance(delivery,dict) and delivery.get('confirmed') is True,
                'independently_fetched_discord_message':False,
                'native_english_equivalent_in_archive':False}
        if not {'run.json','token_usage.json'}.issubset(names):
            raise ValueError('original_english_report_incomplete')
        run=json.loads(z.read('run.json'))
        if run.get('dry_run') is not False:raise ValueError('english_original_not_live')
        return {**base,'original_run_at':_date(run['run']),
            'native_page_count':0,'english_final_native_image_available':False,
            'original_run_items_fetched':run.get('fetched'),
            'original_run_events':len(run.get('events',[])),
            'original_health':health.get('overall'),
            'original_degraded_alert_count':len(health.get('degraded',[])),
            'delivery_receipt_in_archive':False}

def assess_original_vs_v2(originals:list[dict],*,v2_observed_at:str)->dict:
    _date(v2_observed_at)
    if (not isinstance(originals,list) or len(originals)!=2
        or {r.get('product') for r in originals}!={'english','arabic'}
        or any(r.get('schema')!='aggregateit-v2-b49-original-artifact-inventory/1'
               or r.get('can_release') is not False for r in originals)):
        raise ValueError('incomplete_original_edition_inventory')
    en=next(r for r in originals if r['product']=='english')
    ar=next(r for r in originals if r['product']=='arabic')
    blockers=['v1_v2_original_feed_byte_equivalence_not_available',
              'production_v1_full_english_native_pages_not_archived',
              'original_english_newsroom_and_delivery_receipt_not_equivalent',
              'no_authenticated_same_slot_v1_v2_translation_and_analysis',
              'no_independent_discord_client_receipt',
              'incomplete_weekly_history_and_publisher_rights']
    if not ar['foreign_translation_full']:
        blockers.append('real_arabic_production_translation_incomplete')
    if ar['fallback_403_instances']:
        blockers.append('production_arabic_fallback_http_403')
    return {'schema':'aggregateit-v2-b49-original-full-edition-gate/1',
        'v2_observed_at':_date(v2_observed_at),'archived_originals_count':2,
        'arabic_v1_png_count':ar['native_page_count'],
        'english_v1_png_count':en['native_page_count'],
        'arabic_foreign_translation_ratio':str(ar['foreign_translation_completed'])+
             '/'+str(ar['foreign_translation_requested']),
        'source_window_identical_and_replayable':False,
        'english_original_full_edition_comparable':False,
        'arabic_original_visual_baseline_available':True,
        'critical_blockers':blockers,
        'status':'HOLD_MISSING_AUTHENTIC_FULL_V1_V2_PAIR',
        'production_modified':False,'discord_sent':False,'can_release':False}
