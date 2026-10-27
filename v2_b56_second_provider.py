"""B56 second-provider evaluation within original $0.50 B55 + B56 cap."""
import json,os
from datetime import datetime,timezone
import requests
from v2_b55_budgeted_models import API,make_fixture,parse_response,_usage_cost

CAP=.50
PRIOR_B55_RESERVED=.0323148
PRIOR_B55_SPENT=.0013859
MODELS={'fallback':'openai/gpt-oss-120b','candidate':'qwen/qwen3.8-flash'}
RATES={'fallback':(.50,1.80),'candidate':(.60,1.80)}

def reserve(text,role):
    if role not in MODELS or len(text.encode('utf8'))>5000:raise ValueError('unknown_or_oversized_model_input')
    inp,out=RATES[role]
    return round((4*(len(text.encode('utf8'))+512)*inp+700*out)*3/1_000_000+0.000001,9)

def parse(raw,source):
    if not isinstance(raw,dict) or not raw.get('choices'):raise ValueError('missing_choices')
    choice=raw['choices'][0]
    if choice.get('finish_reason') in ('length','content_filter'):raise ValueError('truncated_response')
    msg=choice.get('message',{})
    value=msg.get('content') if isinstance(msg,dict) else None
    if not isinstance(value,str) or not value.strip():raise ValueError('empty_content')
    value=value.strip()
    fence=chr(96)*3
    if value.startswith(fence+'json') and value.endswith(fence):
        value=value[len(fence)+4:-len(fence)].strip()
    elif value.startswith(fence) and value.endswith(fence):
        value=value[len(fence):-len(fence)].strip()
    return parse_response({'choices':[{'message':{'content':value}}]},source)

def run(*,key=None,sender=None,scenarios=None):
    if key is None:key=os.getenv('OPENROUTER_API_KEY','')
    if scenarios is None:scenarios=[(r,l) for r in MODELS for l in ('en','so')]
    if not isinstance(scenarios,list) or len(scenarios)>4 or len(set(scenarios))!=len(scenarios) or any(
        r not in MODELS or l not in ('en','so') for r,l in scenarios):raise ValueError('unapproved_scenarios')
    if not key:return {'schema':'aggregateit-v2-b56-second-provider/1','status':'HOLD_KEY_MISSING',
                        'attempts':0,'can_release':False}
    transport=sender or requests.post
    reservation=0.;reported=0.;checks=[]
    for role,lang in scenarios:
        item=make_fixture(lang)
        system=('Translate exactly into Modern Standard Arabic. Preserve numbers and '
            'negative/provisional meaning. Return JSON only with items array, index 0, '
            'title_ar, summary_ar and exact unchanged source_sha256. No inventions.')
        entry=json.dumps({'index':0,'language':lang,'title':item['title'],
               'summary':item['summary'],'source_sha256':item['source_sha256']},ensure_ascii=False)
        liability=reserve(system+entry,role)
        if PRIOR_B55_RESERVED+reservation+liability>CAP:
            checks.append({'role':role,'lang':lang,'status':'HOLD_SPENDING_CEILING'});break
        reservation+=liability
        payload={'model':MODELS[role],'messages':[{'role':'system','content':system},
                 {'role':'user','content':entry}], 'temperature':0,'max_tokens':700,
                 'response_format':{'type':'json_object'},'usage':{'include':True}}
        record={'role':role,'model':MODELS[role],'lang':lang,'budget_reserved_usd':liability}
        try:
            resp=transport(API,headers={'Authorization':'Bearer '+key,
                'Content-Type':'application/json'},json=payload,timeout=(7,35),allow_redirects=False)
            if resp.status_code!=200:record['status']='HOLD_HTTP_'+str(resp.status_code)
            elif len(resp.content)>30000:record['status']='HOLD_OVERSIZED_RESPONSE'
            else:
                body=resp.json();cost=_usage_cost(body)
                if cost is not None:reported+=cost;record['reported_cost_usd']=round(cost,9)
                verdict=parse(body,item);record.update(verdict)
                record['status']='STRUCTURAL_PASS' if verdict['structural_pass'] and verdict['negation_marker_present'] else 'HOLD_QUALITY'
                if cost is not None and (cost>liability or PRIOR_B55_SPENT+reported>CAP):
                    record['status']='HOLD_COST_MISMATCH'
            resp.close()
        except Exception as exc:record['status']='HOLD_'+type(exc).__name__
        checks.append(record)
        if record['status']=='HOLD_COST_MISMATCH':break
    return {'schema':'aggregateit-v2-b56-second-provider/1',
            'status':'EVALUATED_RELEASE_HELD','checked_at':datetime.now(timezone.utc).isoformat(),
            'attempts':len(checks),'results':checks,
            'prior_b55_reported_usd':PRIOR_B55_SPENT,
            'additional_reported_usd':round(reported,8),
            'combined_reported_usd':round(PRIOR_B55_SPENT+reported,8),
            'combined_conservative_reserved_usd':round(PRIOR_B55_RESERVED+reservation,8),
            'authorized_cap_usd':CAP,
            'model_independent_fallback_structurally_verified':any(
                x.get('role')=='fallback' and x.get('status')=='STRUCTURAL_PASS' for x in checks),
            'real_primary_failure_to_fallback_orchestration_verified':False,
            'real_news_source_translation_verified':False,'full_v1_v2_same_slot_acceptance_verified':False,
            'original_publisher_text_sent':False,'discord_sent':False,'can_release':False}
if __name__=='__main__':
    import argparse
    from pathlib import Path
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    r=run();a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'calls':r['attempts'],'statuses':[(x['role'],x['lang'],x['status']) for x in r.get('results',[])],
      'cumulative_usd':r.get('combined_reported_usd'),'reserved_usd':r.get('combined_conservative_reserved_usd'),
      'can_release':False}))
