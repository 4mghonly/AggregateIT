"""B44: validate dormant V2 source overlay; report current regional floor without promotion."""
from __future__ import annotations
from v2_b11_coverage_readiness import TARGET_REGIONS
from urllib.parse import urlsplit

def candidates(registry):
    if registry.get('schema_version')!='2.0.0-preview' or not isinstance(registry.get('sources'),list):
        raise ValueError('invalid_source_registry')
    staged=registry.get('staged_sources')
    if not isinstance(staged,list) or len(staged)!=4:
        raise ValueError('invalid_staged_roster')
    families=set()
    ids={r['id'] for r in registry['sources']}
    for row in staged:
        if row.get('id') in ids or row.get('region')!='somalia':
            raise ValueError('mixed_source_registry')
        if any(row.get(k) is not False for k in
               ('enabled','eligible_for_collection','eligible_for_publishing',
                'activation_approved','translation_verified')):
            raise ValueError('not_disabled')
        family=row.get('publisher_family_candidate')
        if not family or family in families:raise ValueError('publisher_family_duplicate')
        families.add(family)
        p=urlsplit(row.get('entrypoint',''))
        if p.scheme!='https' or not p.hostname or p.username or p.password:
            raise ValueError('unsafe_source_url')
        if row.get('language') not in ('en','so'):raise ValueError('unknown_source_language')
    if len({r['id'] for r in staged})!=len(staged):raise ValueError('duplicate_source_id')
    return staged

def coverage(registry,audit,live):
    staged=candidates(registry)
    byid={r['candidate_id']:r for r in live}
    if len(byid)!=len(staged) or set(byid)!={r['id'] for r in staged}:
        raise ValueError('incomplete_source_evidence')
    records={}
    for name in TARGET_REGIONS:
        observed=audit.get('regions',{}).get(name)
        if not isinstance(observed,dict) or type(observed.get('compatible')) is not int:
            raise ValueError('missing_prod_region')
        count=observed['compatible']; goal=3 if name=='gcc' else 2
        records[name]={'production_compatible':count,'floor':goal,
                       'production_floor_met_by_adapter':count>=goal,
                       'publisher_independence_verified':False}
    active_technical=set()
    for source in staged:
        row=byid[source['id']]
        if row.get('production_compatible') is True and row.get('collector_status')=='active' and (
                type(row.get('recent_72h')) is int and row['recent_72h']>0):
            active_technical.add(source['publisher_family_candidate'])
    records['somalia']['candidate_technical_families_disabled']=len(active_technical)
    records['somalia']['hypothetical_after_promotion']=records['somalia']['production_compatible']+len(active_technical)
    records['somalia']['production_floor_closed_by_b44']=False
    return {'schema':'aggregateit-v2-b44-regional-coverage/1',
            'regions':records,'live_candidate_technical_families':len(active_technical),
            'production_regions_below_floor':[k for k,v in records.items() if not v['production_floor_met_by_adapter']],
            'production_registry_modified':False,'editorial_region_coverage_verified':False,
            'can_release':False}
