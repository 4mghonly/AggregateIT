"""Build bilingual daily publication candidates from evidence-bound plans, never sendable."""
from __future__ import annotations
from datetime import datetime
from copy import deepcopy
from math import isfinite

AR_TOPICS={'diplomacy','military','security','political_stability','humanitarian_conflict','sanctions','strategic_infrastructure'}
EN_TOPICS={'geopolitics','markets','finance','macro','energy','security','trade','policy','cyber'}

def _timestamp(x):
    try:d=datetime.fromisoformat(x.replace('Z','+00:00'))
    except (TypeError,ValueError,AttributeError) as exc:raise ValueError('invalid_edition_slot') from exc
    if d.utcoffset() is None:raise ValueError('naive_edition_slot')
    return d.isoformat()

def compile_daily(*, editorial_plan, critic_report=None, market_observations=None):
    p=editorial_plan
    if not isinstance(p,dict) or p.get('schema')!='aggregateit-editorial-plan/1' or p.get('delivery_authorized') is not False:
        raise ValueError('untrusted_editorial_plan')
    product=p.get('product')
    if product not in ('english','arabic'):raise ValueError('invalid_edition_product')
    slot=_timestamp(p.get('slot_id'))
    if p.get('language')!=('en' if product=='english' else 'ar'):
        raise ValueError('wrong_edition_language')
    topics=AR_TOPICS if product=='arabic' else EN_TOPICS
    rows=[]
    for item in p.get('items',[]):
        if not isinstance(item,dict) or item.get('topic') not in topics:
            raise ValueError('excluded_product_topic')
        evidence=item.get('evidence')
        if not isinstance(evidence,dict) or any(not isinstance(evidence.get(k),str) or not evidence[k] for k in ('excerpt_id','source_id','quote','source_url')):
            raise ValueError('source_excerpt_missing')
        if evidence.get('original_language','').split('-')[0]!=p['language']:
            raise ValueError('unverified_edition_translation')
        if item.get('reporting_status')!='publisher_attributed_not_independently_verified':
            raise ValueError('unjustified_reporting_status')
        rows.append({'event_id':item['event_id'],'region':item['region'],'topic':item['topic'],
                     'source_id':evidence['source_id'],'excerpt_id':evidence['excerpt_id'],
                     'source_url':evidence['source_url'],'quote':evidence['quote'],
                     'change':item.get('change','unknown_no_baseline'),
                     'assessment':None,'verification':'publisher_attributed_unverified'})
    if product=='arabic' and market_observations:
        raise ValueError('arabic_financial_section_forbidden')
    if product=='english' and market_observations is None:market_observations=[]
    if market_observations is not None and not isinstance(market_observations,list):
        raise ValueError('invalid_market_observations')
    markets=[]
    for m in market_observations or []:
        if not isinstance(m,dict) or m.get('source') in (None,'','tradingview_widget','unknown') or any(k not in m for k in ('symbol','observed_at','value','unit')):
            raise ValueError('unverified_market_observation')
        _timestamp(m['observed_at'])
        if not isinstance(m['value'],(int,float)) or isinstance(m['value'],bool) or not isfinite(m['value']):
            raise ValueError('invalid_market_value')
        markets.append(deepcopy(m))
    if critic_report is None:
        critic_state='insufficient_evidence'
    elif not isinstance(critic_report,dict) or critic_report.get('schema')!='aggregateit-naysayer-report/1' or critic_report.get('product')!=product or critic_report.get('cadence')!='daily' or critic_report.get('slot_id')!=p['slot_id'] or critic_report.get('delivery_authorized') is not False:
        raise ValueError('invalid_critical_review_contract')
    else:
        sections=critic_report.get('sections',[])
        if len(sections)!=1:raise ValueError('daily_requires_one_critic_section')
        critic_state=sections[0]['review_status']
    return {'schema':'aggregateit-v2-daily-publication-candidate/1',
            'product':product,'slot_id':slot,'stories':rows,'market_observations':markets,
            'market_data_status':('not_applicable' if product=='arabic' else 'observed_unverified' if markets else 'unavailable'),
            'naysayer_status':critic_state,'coverage_gaps':deepcopy(p.get('missing_target_regions',[])),
            'content_truth_verified':False,'delivery_authorized':False}
