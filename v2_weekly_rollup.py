"""Offline bilingual weekly rollup from V2 evidence-gated daily edition plans.

No collection, model, sender or database I/O; no independent truth claim.
"""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
from math import isfinite

REGIONS={'gcc','oman','iran','turkey','iraq','yemen','egypt','sudan','sahel','north_africa','pakistan','afghanistan','horn','somalia','levant','palestine_israel','jordan'}

def _dt(value):
    try: dt=datetime.fromisoformat(value)
    except (ValueError,TypeError) as exc: raise ValueError('invalid_dated_value') from exc
    if dt.tzinfo is None or dt.utcoffset() is None:raise ValueError('timezone_required')
    return dt.astimezone(timezone.utc)

def rollup_week(daily_plans, *,product,as_of,market_snapshots=None,max_stories=30):
    if product not in ('english','arabic') or not isinstance(daily_plans,list) or len(daily_plans)>60:
        raise ValueError('invalid_weekly_inputs')
    if type(max_stories) is not int or not 1<=max_stories<=50:raise ValueError('invalid_story_cap')
    now=_dt(as_of);start=now-timedelta(days=7)
    if product=='arabic' and market_snapshots:raise ValueError('arabic_market_not_supported')
    histories={};days=set()
    for edition in daily_plans:
        if not isinstance(edition,dict) or edition.get('schema')!='aggregateit-editorial-plan/1' or edition.get('product')!=product or edition.get('delivery_authorized') is not False:
            raise ValueError('untrusted_daily_plan')
        when=_dt(edition.get('as_of'))
        if not start<=when<=now:raise ValueError('daily_plan_outside_week')
        if not isinstance(edition.get('items'),list) or len(edition['items'])>30:raise ValueError('invalid_daily_items')
        days.add(when.date().isoformat())
        for item in edition['items']:
            if not isinstance(item,dict) or any(not isinstance(item.get(k),str) or not item[k] for k in ('event_id','version_id','region')):
                raise ValueError('invalid_weekly_event')
            ev=item.get('evidence')
            if not isinstance(ev,dict) or any(not isinstance(ev.get(k),str) or not ev[k] for k in ('source_id','excerpt_id','source_url','quote','original_language')):
                raise ValueError('weekly_requires_exact_source')
            if ev['original_language'].split('-')[0]!=('en' if product=='english' else 'ar'):
                raise ValueError('wrong_original_language')
            row=histories.setdefault(item['event_id'],{'versions':set(),'dates':set(),'entries':[],'region':item['region'],'priority':0,'baseline_new':False})
            if row['region']!=item['region']:raise ValueError('conflicting_event_geography')
            row['versions'].add(item['version_id'])
            row['dates'].add(when.isoformat())
            row['entries'].append((when,item))
            row['priority']=max(row['priority'],item.get('priority',0))
            row['baseline_new'] |= item.get('change')=='new'
    stories=[]
    for eid,row in histories.items():
        latest=max(row['entries'],key=lambda a:(a[0],a[1]['version_id']))[1]
        change=('updated_during_week' if len(row['versions'])>1 else ('new_with_verified_baseline' if row['baseline_new'] else 'observed_no_verified_baseline'))
        stories.append({'event_id':eid,'region':row['region'],'priority':row['priority'],
                        'change_status':change,'revision_count':len(row['versions']),
                        'observation_days':len({x.split('T')[0] for x in row['dates']}),
                        'evidence':{k:latest['evidence'][k] for k in ('source_id','excerpt_id','source_url','original_language')},
                        'reporting_status':'publisher_attributed_not_independently_verified'})
    stories.sort(key=lambda x:(-x['priority'],-x['revision_count'],x['event_id']))
    markets=[]
    if product=='english':
        if market_snapshots is None:market_snapshots=[]
        if not isinstance(market_snapshots,list) or len(market_snapshots)>250:raise ValueError('invalid_market_input')
        by_symbol={}
        for m in market_snapshots:
            if not isinstance(m,dict) or any(k not in m for k in ('instrument','source','observed_at','value','unit')):
                raise ValueError('invalid_market_observation')
            if m['source'] in ('tradingview_widget','unknown',None):raise ValueError('unverified_market_source')
            if not all(isinstance(m[k],str) and m[k] for k in ('instrument','source','unit')):
                raise ValueError('invalid_market_source')
            val=m['value']
            if not isinstance(val,(float,int)) or isinstance(val,bool) or not isfinite(val) or val<=0:
                raise ValueError('invalid_market_value')
            date=_dt(m['observed_at'])
            if not start<=date<=now:raise ValueError('market_data_outside_week')
            bucket=by_symbol.setdefault(m['instrument'],[])
            if bucket and (bucket[0][1]['source']!=m['source'] or bucket[0][1]['unit']!=m['unit']):
                raise ValueError('incompatible_market_series')
            bucket.append((date,m))
        for instrument,values in sorted(by_symbol.items()):
            values.sort(key=lambda x:x[0]);first,last=values[0][1],values[-1][1]
            change=100*(last['value']/first['value']-1) if len(values)>=2 and values[0][0]!=values[-1][0] else None
            markets.append({'instrument':instrument,'source':first['source'],'unit':first['unit'],
                            'first_at':first['observed_at'],'last_at':last['observed_at'],
                            'first_value':first['value'],'last_value':last['value'],
                            'change_pct':round(change,3) if change is not None else None})
    represented=sorted({s['region'] for s in stories})
    return {'schema':'aggregateit-v2-weekly-rollup/1','product':product,'as_of':as_of,
            'window_days':7,'days_with_snapshots':len(days),'unique_events':len(stories),
            'stories':stories[:max_stories],'omitted_over_budget':max(0,len(stories)-max_stories),
            'regions_covered':represented,'regions_uncovered':sorted(REGIONS-set(represented)) if product=='arabic' else [],
            'market_changes':markets,'analysis_status':'requires_independent_source_and_editorial_verification',
            'naysayer_status':'not_supplied','delivery_authorized':False}
