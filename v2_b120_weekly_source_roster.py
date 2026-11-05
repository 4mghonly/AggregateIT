"""B120 no-post future seven-UTC-day source roster; never a full weekly newsletter.

Conserves only sources, canonical URLs and cryptographic event identifiers.
Publisher quotes, bodies and headlines are deliberately excluded. A source
roster does NOT satisfy full analytical, model, visual or Discord parity.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from html import escape
from json import dumps
from urllib.parse import urlsplit
import re

SCHEMA='aggregateit-v2-b120-source-roster-day/1'
WEEK_SCHEMA='aggregateit-v2-b120-source-roster-week/1'
WORKFLOW='.github/workflows/v2-b80-b83-live-acceptance.yml'
BRANCH='rebuild/aggregateit-v2'
COMMIT=re.compile(r'[0-9a-f]{40}\Z')
DIGEST=re.compile(r'[0-9a-f]{64}\Z')
RUN=re.compile(r'[1-9][0-9]{0,17}\Z')

def _datetime(raw):
    if not isinstance(raw,str):raise ValueError('invalid_observation_time')
    try:dt=datetime.fromisoformat(raw.replace('Z','+00:00'))
    except (ValueError,TypeError):raise ValueError('invalid_observation_time') from None
    if dt.tzinfo is None or dt.utcoffset() is None:raise ValueError('timezone_required')
    return dt.astimezone(timezone.utc)

def manifest_sha256(receipt):
    data=dict(receipt)
    data.pop('manifest_sha256',None)
    return sha256(dumps(data,sort_keys=True,ensure_ascii=False,
                        separators=(',',':')).encode('utf8')).hexdigest()

def make_daily_source_roster(editorial,*,observed_at,run_id,head_sha,capture_sha256):
    if (not isinstance(editorial,dict) or
        editorial.get('schema')!='aggregateit-v2-b46-article-editorial/1' or
        editorial.get('can_send') is not False):
        raise ValueError('untrusted_editorial_plan')
    if not (isinstance(run_id,str) and RUN.fullmatch(run_id)
            and isinstance(head_sha,str) and COMMIT.fullmatch(head_sha)
            and isinstance(capture_sha256,str) and DIGEST.fullmatch(capture_sha256)):
        raise ValueError('missing_ci_provenance')
    observed=_datetime(observed_at)
    products=editorial.get('products',{})
    if set(products)!={'english','arabic'}:raise ValueError('missing_bilingual_products')
    safe_products={}
    for product,lang in (('english','en'),('arabic','ar')):
        row=products[product]
        plan=row.get('editorial_plan',{})
        if (plan.get('schema')!='aggregateit-editorial-plan/1' or
            plan.get('delivery_authorized') is not False or
            plan.get('product')!=product or plan.get('language')!=lang or
            _datetime(plan.get('as_of'))!=observed):
            raise ValueError('untrusted_daily_roster_plan')
        items=plan.get('items')
        if not isinstance(items,list) or len(items)>15:raise ValueError('invalid_daily_roster_items')
        projected=[]
        for item in items:
            if not isinstance(item,dict):raise ValueError('invalid_roster_event')
            evidence=item.get('evidence',{})
            url=evidence.get('source_url')
            if not isinstance(url,str) or len(url)>1600:raise ValueError('invalid_source_url')
            p=urlsplit(url)
            if p.scheme!='https' or not p.hostname or p.username or p.password:
                raise ValueError('untrusted_source_url')
            if evidence.get('original_language')!=lang:raise ValueError('wrong_source_language')
            for key in ('event_id','version_id','region','topic'):
                if not isinstance(item.get(key),str) or not item[key]:
                    raise ValueError('invalid_roster_event')
            for key in ('source_id','excerpt_id'):
                if not isinstance(evidence.get(key),str) or not evidence[key]:
                    raise ValueError('missing_roster_source_identity')
            if type(item.get('priority')) not in (int,float):
                raise ValueError('invalid_roster_priority')
            projected.append({
                'event_id':item['event_id'],'version_id':item['version_id'],
                'region':item['region'],'topic':item['topic'],
                'priority':item['priority'],'source_id':evidence['source_id'],
                'excerpt_id':evidence['excerpt_id'],
                'source_url':url,
                'identity_sha256':sha256(url.encode('utf8')).hexdigest(),
                'original_language':lang,
                'source_factuality_verified':False})
        safe_products[product]={'story_count':len(projected),'stories':projected}
    receipt={'schema':SCHEMA,'utc_date':observed.date().isoformat(),
             'observed_at':observed.isoformat(),'github_run_id':run_id,
             'head_sha':head_sha,'capture_sha256':capture_sha256,
             'products':safe_products,
             'source_type':'source_linked_original_language_no_post',
             'publisher_full_text_persisted':False,
             'publisher_quote_persisted':False,
             'editorial_model_visual_delivery_verified':False,
             'can_release':False}
    receipt['manifest_sha256']=manifest_sha256(receipt)
    return receipt

def _verify_one(row,metadata,*,today):
    if not isinstance(row,dict) or row.get('schema')!=SCHEMA or row.get('can_release') is not False:
        raise ValueError('invalid_daily_roster_receipt')
    if row.get('manifest_sha256')!=manifest_sha256(row):
        raise ValueError('manifest_digest_mismatch')
    if not (isinstance(row.get('head_sha'),str) and COMMIT.fullmatch(row['head_sha'])
            and isinstance(row.get('github_run_id'),str) and RUN.fullmatch(row['github_run_id'])):
        raise ValueError('untrusted_roster_identity')
    stamp=_datetime(row.get('observed_at'))
    day=date.fromisoformat(row.get('utc_date',''))
    if day!=stamp.date() or day>today or day<today-timedelta(days=30):
        raise ValueError('invalid_roster_day')
    if set(row.get('products',{}))!={'english','arabic'}:
        raise ValueError('missing_roster_language')
    if not isinstance(metadata,dict) or any((
        metadata.get('id')!=int(row['github_run_id']),
        metadata.get('head_sha')!=row['head_sha'],
        metadata.get('head_branch')!=BRANCH,
        metadata.get('path')!=WORKFLOW,
        metadata.get('status')!='completed',
        metadata.get('conclusion')!='success',
        metadata.get('event') not in ('workflow_dispatch','push'),
    )):
        raise ValueError('github_run_provenance_mismatch')
    started=_datetime(metadata.get('run_started_at'))
    if not -60<=(stamp-started).total_seconds()<=7200:
        raise ValueError('capture_run_time_mismatch')
    for p in ('english','arabic'):
        product=row['products'][p]
        if (type(product.get('story_count')) is not int
            or not 0<product['story_count']<=15
            or len(product.get('stories',[]))!=product['story_count']):
            raise ValueError('missing_positive_roster_story')
        for story in product['stories']:
            if any(k in story for k in ('quote','headline','original_text','html_bytes')):
                raise ValueError('publisher_text_in_roster')
            if not isinstance(story.get('source_url'),str) or not story['source_url'].startswith('https://'):
                raise ValueError('invalid_roster_source')
    return day

def seven_day_roster(receipts,run_metadata,*,today,expected_sha):
    if not isinstance(today,date) or isinstance(today,datetime):
        raise ValueError('invalid_target_date')
    if not isinstance(expected_sha,str) or not COMMIT.fullmatch(expected_sha):
        raise ValueError('missing_release_candidate_sha')
    if not isinstance(receipts,list) or len(receipts)>45 or not isinstance(run_metadata,list):
        raise ValueError('unbounded_weekly_roster')
    run_map={x.get('id'):x for x in run_metadata if isinstance(x,dict)}
    by_date=defaultdict(list)
    window=[(today-timedelta(days=i)).isoformat() for i in range(6,-1,-1)]
    for row in receipts:
        if not isinstance(row,dict):raise ValueError('invalid_roster_row')
        meta=run_map.get(int(row.get('github_run_id','0')))
        day=_verify_one(row,meta,today=today).isoformat()
        if day in window:by_date[day].append(row)
    ambiguous=[day for day,rows in by_date.items() if len(rows)>1]
    distinct=sum(len(by_date.get(day,[]))==1 for day in window)
    invalid_sha=[day for day,rows in by_date.items()
                 if len(rows)==1 and rows[0]['head_sha']!=expected_sha]
    missing=[day for day in window if not by_date.get(day)]
    complete=not ambiguous and not invalid_sha and not missing and distinct==7
    status=('HOLD_AMBIGUOUS_DATE' if ambiguous else
            'HOLD_WRONG_RELEASE_CANDIDATE' if invalid_sha else
            'HOLD_MISSING_GENUINE_DAYS' if missing else
            'COMPLETE_ATTRIBUTED_SOURCE_ROSTER_NO_POST')
    return {'schema':WEEK_SCHEMA,'status':status,'window':window,
            'candidate_sha':expected_sha,
            'genuine_distinct_days':sum(
                len(by_date.get(day,[]))==1 and
                by_date[day][0]['head_sha']==expected_sha for day in window),
            'missing_days':missing,'ambiguous_days':ambiguous,'other_commit_days':invalid_sha,
            'complete_seven_day_source_roster':complete,
            'source_linked_daily_receipts':len(receipts),
            'full_editorial_model_visual_delivery_parity':False,
            'full_weekly_analytical_product_verified':False,
            'publisher_rights_verified':False,'can_release':False}

def render_source_roster_html(weekly, receipts):
    if weekly.get('schema')!=WEEK_SCHEMA or weekly.get('complete_seven_day_source_roster') is not True:
        raise ValueError('weekly_source_roster_incomplete')
    rows=sorted(receipts,key=lambda r:r['utc_date'])
    lines=['<!doctype html><html lang="en"><meta charset="utf-8"><title>AggregateIT - attributed source roster</title>',
           '<body><h1>AggregateIT — attributed sources only (NOT FOR DELIVERY)</h1>',
           '<p>Publisher article links, not validated facts, translated summaries or model analysis.</p>']
    for row in rows:
        lines.append('<h2>'+escape(row['utc_date'])+'</h2>')
        for product in ('english','arabic'):
            direction='rtl' if product=='arabic' else 'ltr'
            lines.append('<section dir="'+direction+'"><h3>'+product+'</h3><ol>')
            for item in row['products'][product]['stories']:
                url=escape(item['source_url'],quote=True)
                lines.append('<li><a rel="noopener noreferrer" href="'+url+'">'+
                             escape(item['source_id'])+'</a> — '+escape(item['region'])+'</li>')
            lines.append('</ol></section>')
    return '\n'.join(lines+['<footer>UNVERIFIED. NO MODEL OR DELIVERY PARITY. NO REPRODUCTION RIGHTS ASSERTED.</footer></body></html>'])

def offline_cli():
    """Only inspect explicitly supplied authenticated GitHub run metadata."""
    import argparse,json
    from pathlib import Path
    parser=argparse.ArgumentParser()
    parser.add_argument('--roster-dir',default='b120-history')
    parser.add_argument('--github-runs-json',default='b120-authenticated-runs.json')
    parser.add_argument('--candidate-sha',required=True)
    parser.add_argument('--as-of',required=True)
    parser.add_argument('--output',default='b120_week_status.json')
    args=parser.parse_args()
    root=Path(args.roster_dir)
    receipts=[]
    for path in sorted(root.glob('*.json')) if root.exists() else []:
        if path.is_symlink() or path.stat().st_size>131072:
            raise ValueError('unsafe_weekly_roster_file')
        receipts.append(json.loads(path.read_text()))
    runs=json.loads(Path(args.github_runs_json).read_text()) if Path(args.github_runs_json).exists() else []
    result=seven_day_roster(receipts,runs,today=date.fromisoformat(args.as_of),
                            expected_sha=args.candidate_sha)
    Path(args.output).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    if result['complete_seven_day_source_roster']:
        Path('b120_held_source_roster.html').write_text(render_source_roster_html(result,receipts),encoding='utf8')
    print(json.dumps({'status':result['status'],'days':result['genuine_distinct_days'],
                      'release':'HOLD','can_release':False}))

if __name__=='__main__':
    offline_cli()
