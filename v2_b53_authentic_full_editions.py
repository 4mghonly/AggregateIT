"""B53 genuine original English+Arabic 4K archives and B54 hard release blockers.

All original production artifact identifiers and SHA256 values are pinned to
their live GitHub Actions evidence. No guessed V1 source bytes, model results,
publisher rights, or Discord client confirmations; no canary authorization.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile,BadZipFile
from PIL import Image

EXPECTED_ORIGINALS={
    'english':{
      'run_id':40497262560,'artifact_id':12731017257,
      'zip_sha256':'0f1353b89266a0ba3171abfe6823db5cdcc64c493a9477c6c23baf430803f1c1',
      'pages':['intel_slide_p1.png','intel_slide_p2.png']},
    'arabic':{
      'run_id':40517778731,'artifact_id':12741710341,
      'zip_sha256':'3ba4943ebeeaab828f8285d727a1787d6178000f8d8377004b9edf7a3f1ff1bd',
      'pages':['arabic-p1.png','arabic-p2.png','arabic-p3.png']},
}
def _instant(value):
    try:
        d=datetime.fromisoformat(value.replace('Z','+00:00'))
        if d.utcoffset() is None:raise ValueError('tz')
        return d.astimezone(timezone.utc)
    except (ValueError,AttributeError,TypeError):
        raise ValueError('invalid_original_edition_timestamp') from None

def inspect_original_final_edition(raw:bytes,*,product:str,run_id:int,expected_zip_sha256:str)->dict:
    known=EXPECTED_ORIGINALS.get(product)
    if (not known or type(run_id) is not int or run_id!=known['run_id']
        or not isinstance(raw,bytes) or not 150<=len(raw)<=3_000_000
        or not isinstance(expected_zip_sha256,str) or len(expected_zip_sha256)!=64):
        raise ValueError('unapproved_original_edition')
    digest=sha256(raw).hexdigest()
    if digest!=expected_zip_sha256:raise ValueError('original_zip_digest_mismatch')
    try:
        archive=ZipFile(BytesIO(raw))
    except BadZipFile:raise ValueError('invalid_original_archive') from None
    with archive as z:
        entries=z.infolist()
        if (len(entries)>15 or sum(x.file_size for x in entries)>5_000_000
            or any(x.file_size>3_000_000 or x.filename.startswith('/')
                   or '..' in x.filename.split('/') or x.is_dir() for x in entries)
            or len({x.filename for x in entries})!=len(entries)):
            raise ValueError('unsafe_original_zip_manifest')
        names=set(z.namelist())
        if not set(known['pages']).issubset(names):
            raise ValueError('missing_original_final_pages')
        page_receipts=[]
        for name in known['pages']:
            data=z.read(name)
            with Image.open(BytesIO(data)) as im:
                if im.format!='PNG' or im.size!=(3840,2160) or im.mode not in ('RGB','RGBA'):
                    raise ValueError('wrong_original_4k_image')
                im.verify()
            page_receipts.append({'name':name,'sha256':sha256(data).hexdigest(),
                 'width':3840,'height':2160})
        result={'schema':'aggregateit-v2-b53-original-final-page-receipt/1',
            'product':product,'run_id':run_id,
            'artifact_id':known['artifact_id'],
            'zip_sha256':digest,'native_page_count':len(page_receipts),
            'page_receipts':page_receipts,
            'publisher_text_or_images_uploaded':False,
            'independent_discord_client_receipt':False,
            'original_feed_bytes_saved':False,
            'source_rights_verified':False,'can_release':False}
        if product=='english':
            if 'gazette_health.json' not in names:raise ValueError('missing_original_gazette_health')
            health=json.loads(z.read('gazette_health.json'))
            if type(health.get('llm_ok')) is not bool:raise ValueError('bad_original_gazette_llm')
            return {**result,'llm_ok':health['llm_ok'],
              'health_status':str(health.get('status','unknown'))[:40],
              'app_claimed_delivery':health.get('delivery',{}).get('confirmed') is True,
              'original_english_source_snapshot_available':False}
        if 'briefing.json' not in names or 'health.json' not in names:
            raise ValueError('missing_original_arabic_health')
        briefing=json.loads(z.read('briefing.json'))
        health=json.loads(z.read('health.json'))
        if (briefing.get('schema_version')!='arabic-brief-v3'
            or briefing.get('sample') is not False):
            raise ValueError('not_real_arabic_production')
        req=health.get('translation',{}).get('requested_foreign')
        done=health.get('translation',{}).get('translated_foreign')
        if type(req) is not int or type(done) is not int or not 0<=done<=req:
            raise ValueError('invalid_foreign_translation')
        fallback=sum(x.get('route')=='fallback' and x.get('error')=='http_403'
                     for x in health.get('translation',{}).get('routes',[]) if isinstance(x,dict))
        start=_instant(briefing['window_start']);end=_instant(briefing['window_end'])
        if start>=end:raise ValueError('invalid_original_arabic_window')
        return {**result,
          'original_window_utc':[start.isoformat(),end.isoformat()],
          'source_event_count':len(briefing.get('events',[])),
          'foreign_translation_requested':req,'foreign_translation_completed':done,
          'translation_complete':req==done,
          'fallback_http_403':fallback,
          'app_claimed_delivery':health.get('delivery',{}).get('confirmed') is True}

def assess_original_final_pair(originals:list[dict],*,v2_observed_at:str)->dict:
    at=_instant(v2_observed_at)
    if (not isinstance(originals,list) or len(originals)!=2
        or {r.get('product') for r in originals}!={'english','arabic'}
        or any(r.get('schema')!='aggregateit-v2-b53-original-final-page-receipt/1'
               or r.get('can_release') is not False for r in originals)):
        raise ValueError('untrusted_original_pair')
    index={x['product']:x for x in originals}
    if index['english']['native_page_count']!=2 or index['arabic']['native_page_count']!=3:
        raise ValueError('incorrect_original_page_count')
    return {'schema':'aggregateit-v2-b53-genuine-original-visual-review/1',
        'original_evidence':[{'product':p,'run_id':r['run_id'],'artifact_id':r['artifact_id'],
                              'zip_sha256':r['zip_sha256'],'native_pages':r['native_page_count']}
                              for p,r in index.items()],
        'both_original_products_have_4k_pages':True,
        'arabic_original_translation':'%s/%s'%(index['arabic']['foreign_translation_completed'],
                                                 index['arabic']['foreign_translation_requested']),
        'original_english_llm_healthy':index['english']['llm_ok'],
        'original_arabic_fallback_healthy':index['arabic']['fallback_http_403']==0,
        'v2_observed_at':at.isoformat(),
        'matched_v1_v2_full_edition_slots':0,
        'source_bytes_replayable':False,
        'full_editorial_equivalence_verified':False,
        'manual_language_visual_legibility_reviewed':False,
        'independent_discord_client_receipts':False,
        'can_release':False}

def decide_acceptance(original_pair:dict,*,source_audit_healthy:bool|None)->dict:
    if (not isinstance(original_pair,dict)
        or original_pair.get('schema')!='aggregateit-v2-b53-genuine-original-visual-review/1'
        or original_pair.get('can_release') is not False
        or type(source_audit_healthy) not in (bool,type(None))):
        raise ValueError('untrusted_genuine_visual_gate')
    blockers=[
      'b45_real_translation_and_independent_fallback_not_accepted',
      'full_edition_v1_v2_same_slot_source_bytes_missing',
      'full_editorial_model_and_native_output_parity_unverified',
      'genuine_7day_weekly_history_not_retained',
      'source_redistribution_rights_not_certified',
      'independent_discord_client_receipts_not_verified',
      'manual_final_visual_legibility_not_accepted',
      'production_rollback_not_executed',
    ]
    if source_audit_healthy is not True:
        blockers.append('production_source_audit_not_green')
    if not original_pair['original_english_llm_healthy']:
        blockers.append('original_english_llm_degraded')
    if not original_pair['original_arabic_fallback_healthy']:
        blockers.append('original_arabic_fallback_http_403')
    return {'schema':'aggregateit-v2-b54-release-acceptance-hold/1',
      'status':'HOLD_REQUIRE_AUTHENTIC_PRODUCTION_EQUIVALENCE_AND_MODEL_RELIABILITY',
      'original_en_ar_native_page_baselines_confirmed':True,
      'source_audit_status':('PASS' if source_audit_healthy is True else
           'FAILED' if source_audit_healthy is False else 'NOT_INDEPENDENTLY_VERIFIED'),
      'critical_blockers':blockers,'critical_blocker_count':len(blockers),
      'missing_original_page_baseline':False,
      'new_verified_english_original':True,
      'new_verified_arabic_original':True,
      'full_system_same_slot_proof':False,
      'paid_model_calls':0,'publisher_payloads_exposed':False,
      'source_rights_verified':False,'no_prod_writes':True,
      'discord_sent':False,'canary_authorized':False,'can_release':False}
