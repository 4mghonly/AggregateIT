"""B115 no-post paired evidence receipts: one GitHub run is not one date."""
from __future__ import annotations
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import json, os, re

SHA = re.compile(r"[0-9a-f]{64}\Z")
RUN = re.compile(r"[0-9]{8,16}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
NAME = re.compile(r"(?P<run>[0-9]{8,16})-(?P<day>\d{4}-\d{2}-\d{2})\.json\Z")


def make_pair(live: dict, *, run_id: str, head_sha: str) -> dict:
    if not isinstance(live, dict) or live.get('schema') != 'aggregateit-v2-b46-live-chain/1' or live.get('can_release') is not False:
        raise ValueError('untrusted_live_capture')
    b = live.get('b115_same_capture', {})
    if (b.get('schema') != 'aggregateit-v2-b115-same-capture/1'
            or b.get('source_capture_identity_verified') is not True
            or b.get('v1_deterministic_functions_executed') is not True
            or b.get('v2_actual_editorial_compiler_executed') is not True
            or b.get('can_release') is not False or b.get('discord_sent') is not False
            or not isinstance(b.get('input_manifest_sha256'), str)
            or not SHA.fullmatch(b['input_manifest_sha256'])):
        raise ValueError('incomplete_same_capture')
    if not isinstance(run_id, str) or not RUN.fullmatch(run_id) or not isinstance(head_sha,str) or not COMMIT.fullmatch(head_sha):
        raise ValueError('missing_ci_run_provenance')
    instant = datetime.fromisoformat(b['observed_at'].replace('Z','+00:00'))
    if instant.tzinfo is None or instant.utcoffset() is None or b['utc_date'] != instant.astimezone(timezone.utc).date().isoformat():
        raise ValueError('invalid_capture_date')
    products = {}
    for p in ('english', 'arabic'):
        row = b['products'][p]
        count = live['editorial']['products'][p]['story_count']
        if any(type(row[k]) is not int or not 0 <= row[k] <= 30 for k in ('attempted_article_pages','v1_selected','v2_selected','both_selected')) or type(count) is not int or not 0 <= count <= 30:
            raise ValueError('invalid_pair_counts')
        products[p] = {k: row[k] for k in ('attempted_article_pages','v1_selected','v2_selected','both_selected')}
        products[p]['operational_v2_selected'] = count
        products[p]['v1_only'] = len(row['v1_only_sha256'])
        products[p]['v2_only'] = len(row['v2_only_sha256'])
    return {'schema':'aggregateit-v2-b115-paired-run/1', 'utc_date':b['utc_date'],
        'observed_at':b['observed_at'], 'github_run_id':run_id,'head_sha':head_sha,
        'input_manifest_sha256':b['input_manifest_sha256'],
        'source_feed_sha256':{x['product']+':'+x['source_id']:x['sha256'] for x in b['feeds']},
        'products':products,
        'full_v1_editorial_model_and_delivery_verified':False,
        'publisher_provenance_independently_authenticated':False,
        'can_release':False}


def verify_pair(row:dict, *, run_id:str, today:date, expected_day:str|None=None):
    if not isinstance(row,dict) or row.get('schema')!='aggregateit-v2-b115-paired-run/1' or row.get('can_release') is not False:
        raise ValueError('untrusted_pair_receipt')
    if row.get('github_run_id')!=run_id or not RUN.fullmatch(run_id):
        raise ValueError('paired_run_identity_mismatch')
    if not isinstance(row.get('head_sha'),str) or not COMMIT.fullmatch(row['head_sha']):
        raise ValueError('invalid_paired_commit')
    stamp=datetime.fromisoformat(row['observed_at'].replace('Z','+00:00'))
    day=date.fromisoformat(row['utc_date'])
    if stamp.tzinfo is None or stamp.utcoffset() is None or stamp.astimezone(timezone.utc).date()!=day:
        raise ValueError('paired_date_mismatch')
    if expected_day is not None and row['utc_date']!=expected_day:
        raise ValueError('filename_day_mismatch')
    if day>today or day<today-timedelta(days=29):
        raise ValueError('outside_pair_retention')
    if not isinstance(row.get('input_manifest_sha256'),str) or not SHA.fullmatch(row['input_manifest_sha256']):
        raise ValueError('invalid_pair_manifest')
    if not isinstance(row.get('source_feed_sha256'),dict) or len(row['source_feed_sha256'])<2 or any(not SHA.fullmatch(x) for x in row['source_feed_sha256'].values()):
        raise ValueError('invalid_pair_feeds')
    if set(row.get('products',{}))!={'english','arabic'}:
        raise ValueError('missing_pair_product')
    for p in ('english','arabic'):
        product=row['products'][p]
        if set(product)!={'attempted_article_pages','v1_selected','v2_selected','both_selected','operational_v2_selected','v1_only','v2_only'}:
            raise ValueError('incomplete_pair_product')
        if any(type(value) is not int or not 0<=value<=30 for value in product.values()):
            raise ValueError('invalid_pair_product_counts')
        if product['both_selected']>min(product['v1_selected'],product['v2_selected']):
            raise ValueError('inconsistent_pair_selection')
    return row


def history(directory:Path, *, today:date)->dict:
    root=Path(directory)
    files=sorted(root.glob('*.json')) if root.exists() else []
    if len(files)>45:raise ValueError('too_many_pair_receipts')
    slots={}
    for file in files:
        match=NAME.fullmatch(file.name)
        if not match or file.is_symlink() or file.stat().st_size>65536:
            raise ValueError('unsafe_pair_history_file')
        row=verify_pair(json.loads(file.read_bytes()),run_id=match['run'],
                        today=today,expected_day=match['day'])
        slots.setdefault(row['utc_date'],[]).append(row)
    window=[(today-timedelta(days=i)).isoformat() for i in range(6,-1,-1)]
    daily={}
    for day in window:
        captures=slots.get(day,[])
        variants={x['input_manifest_sha256'] for x in captures}
        daily[day]={'capture_runs':len(captures),'input_variants':len(variants),
            'english_positive':any(x['products']['english']['operational_v2_selected']>0 for x in captures),
            'arabic_positive':any(x['products']['arabic']['operational_v2_selected']>0 for x in captures)}
    return {'schema':'aggregateit-v2-b115-seven-day-paired-history/1',
       'window':window,'daily':daily,'historical_runs':len(files),
       'distinct_capture_days':sum(x['capture_runs']>0 for x in daily.values()),
       'english_positive_days':sum(x['english_positive'] for x in daily.values()),
       'arabic_positive_days':sum(x['arabic_positive'] for x in daily.values()),
       'seven_distinct_paired_capture_dates':all(x['capture_runs']>0 for x in daily.values()),
       'seven_positive_bilingual_days':all(x['english_positive'] and x['arabic_positive'] for x in daily.values()),
       'full_v1_model_visual_delivery_parity_verified':False,
       'can_release':False}


if __name__ == '__main__':
    import argparse
    args = argparse.ArgumentParser()
    args.add_argument('--history', action='store_true')
    options = args.parse_args()
    if not options.history:
        live = json.loads(Path('b80_b81_live_editorial.json').read_text())
        paired = make_pair(live, run_id=os.environ.get('GITHUB_RUN_ID',''),
                           head_sha=os.environ.get('GITHUB_SHA',''))
        Path('b115_paired_run.json').write_text(json.dumps(paired,sort_keys=True,indent=2)+'\n')
        print(json.dumps({'paired_utc_date':paired['utc_date'],
                          'source_input_sha256':paired['input_manifest_sha256'],
                          'products':paired['products'],'can_release':False}))
    else:
        today=datetime.now(timezone.utc).date()
        paired=json.loads(Path('b115_paired_run.json').read_text())
        verify_pair(paired,run_id=os.environ.get('GITHUB_RUN_ID',''),today=today)
        root=Path('b115-history');root.mkdir(exist_ok=True)
        path=root/(paired['github_run_id']+'-'+paired['utc_date']+'.json')
        path.write_text(json.dumps(paired,sort_keys=True)+'\n')
        report=history(root,today=today)
        Path('b115_seven_day_history.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
        print(json.dumps({'b115_distinct_capture_days':report['distinct_capture_days'],
                          'b115_bilingual_positive_days':min(report['english_positive_days'],report['arabic_positive_days']),
                          'b115_seven_day_complete':report['seven_positive_bilingual_days'],
                          'can_release':False}))
