"""B13 deterministic *rights-held* newsletter balancing for preview only.

No article text is republished unless the row is an explicitly invented
synthetic fixture. No real source claims are independently confirmed by this
planner. It is deliberately not the permission-granting publication pathway.
"""
from __future__ import annotations

from collections import Counter
from urllib.parse import urlsplit

from v2_editorial import AR_REGIONS, AR_TOPICS, EN_TOPICS

REGIONS = frozenset(AR_REGIONS)
_LANG = {'english':'en','arabic':'ar'}

def _valid_source(url):
    if not isinstance(url,str):
        raise ValueError('invalid_source_url')
    p=urlsplit(url)
    if p.scheme!='https' or not p.hostname or p.username or p.password or p.port not in (None,443):
        raise ValueError('invalid_source_url')

def balance_held_news(entries:list[dict], *,product:str,max_tiles:int=10)->dict:
    if product not in _LANG:raise ValueError('unknown_product')
    if (type(max_tiles) is not int or not 1<=max_tiles<=12
            or not isinstance(entries,list) or len(entries)>300):
        raise ValueError('invalid_balance_input')
    admissible=[];non_native=0;ids=set()
    mandatory={'event_id','region','source_id','original_language','subject_country',
               'topic','priority','headline','synthetic','rights_status','source_url'}
    for e in entries:
        if not isinstance(e,dict) or not mandatory.issubset(e):
            raise ValueError('invalid_entry')
        if e['event_id'] in ids:raise ValueError('duplicate_event_id')
        ids.add(e['event_id'])
        if (e['region'] not in REGIONS or not isinstance(e['source_id'],str)
                or not e['source_id'] or type(e['priority']) is not int
                or not 0<=e['priority']<=100 or not isinstance(e['headline'],str)
                or not e['headline'] or len(e['headline'])>240
                or type(e['synthetic']) is not bool
                or not isinstance(e['subject_country'],str)
                or len(e['subject_country'])!=2):
            raise ValueError('invalid_entry')
        if e['topic'] not in (EN_TOPICS if product=='english' else AR_TOPICS):
            raise ValueError('unapproved_product_topic')
        _valid_source(e['source_url'])
        if e['original_language'].split('-')[0]!=_LANG[product]:
            non_native+=1
            continue
        admissible.append(dict(e))
    # Stable priority within each region, with an explicit UAE-first sector in
    # Arabic. A region seen in the sample is not proof it has adequate coverage.
    admissible.sort(key=lambda x:(-x['priority'],x['event_id']))
    selected=[];selected_ids=set();regions=set()
    if product=='arabic':
        uae=[x for x in admissible if x['subject_country']=='AE' and x['region']=='gcc']
        if uae:
            selected.append(uae[0]);selected_ids.add(uae[0]['event_id']);regions.add('gcc')
    for item in admissible:
        if len(selected)>=max_tiles:break
        if item['event_id'] not in selected_ids and item['region'] not in regions:
            selected.append(item);selected_ids.add(item['event_id']);regions.add(item['region'])
    per_source=Counter(x['source_id'] for x in selected)
    per_region=Counter(x['region'] for x in selected)
    for item in admissible:
        if len(selected)>=max_tiles:break
        if item['event_id'] not in selected_ids and per_source[item['source_id']]<2 and per_region[item['region']]<2:
            selected.append(item);selected_ids.add(item['event_id'])
            per_source[item['source_id']]+=1;per_region[item['region']]+=1
    tiles=[]
    for item in selected:
        # The input's self-asserted "explicit_licensed" is never a license
        # document. Real content remains masked in this presentation.
        headline=item['headline'] if item['synthetic'] else (
            'حقوق إعادة النشر غير مؤكدة' if product=='arabic'
            else 'SOURCE TEXT WITHHELD — RIGHTS NOT CLEARED'
        )
        tiles.append({'event_id':item['event_id'], 'region':item['region'],
                      'source_id':item['source_id'],'source_url':item['source_url'],
                      'original_language':item['original_language'],
                      'subject_country':item['subject_country'],
                      'priority':item['priority'],'display_headline':headline,
                      'synthetic':item['synthetic'],
                      'rights_status':'synthetic_only' if item['synthetic'] else 'rights_hold',
                      'publisher_facts_verified':False})
    represented={x['region'] for x in selected}
    return {'schema':'aggregateit-v2-b13-balanced-held-preview/1',
            'product':product,'language':_LANG[product],
            'tiles':tiles,'tiles_selected':len(tiles),
            'represented_regions':sorted(represented),
            'unrepresented_target_regions':sorted(REGIONS-represented),
            'withheld_non_native':non_native,
            'omitted_due_to_space':len(admissible)-len(tiles),
            'rights_cleared':False,'publisher_independence_verified':False,
            'editorial_coverage_verified':False,'source_facts_verified':False,
            'llm_called':False,'delivery_authorized':False}
