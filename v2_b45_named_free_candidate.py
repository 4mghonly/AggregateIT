"""B45 third and final materially different attempt: pinned ZERO-PRICE fallback MODEL.

Uses the existing OpenRouter credential only for a separate named free model.
No provider-independent failover, no production fallback secret or publisher text.
"""
from datetime import datetime,timezone
from arabic_live_v2 import _route,_route_call,TRANSLATE_SYSTEM
from v2_b45_free_live_models import free_route_guard,fixture
from v2_b45_source_translation_review import inspect_translations
MODEL='nvidia/nemotron-3.5-lightning:free'

def evaluate_named_free(*,configured=None,caller=None,resolve_env=True):
    original=configured if configured is not None else (_route('ARABIC_LLM_') if resolve_env else {})
    safe=free_route_guard(original)
    if safe!='FREE_ROUTE_CONFIGURED':
        return {'schema':'aggregateit-v2-b45-named-free/1','status':'HOLD_'+safe,
                'attempts':0,'languages':{},'model':MODEL,'paid_calls':0,
                'actual_second_provider_verified':False,'can_release':False}
    route={**original,'model':MODEL,'options':{}}
    invoke=caller or _route_call
    results={}
    for lang in ('en','so'):
        x=fixture(lang)
        req={'items':[{'index':0,'source_sha256':x['source_sha256'],
              'language':lang,'title':x['title'],'summary':x['summary']}]}
        system=TRANSLATE_SYSTEM+'\nReturn JSON only. Every item must echo source_sha256 EXACTLY. Preserve 12 and 27 and the unconfirmed/planned status.'
        try:
            resp=invoke(route,system,req,max_tokens=400)
            out=inspect_translations([x],resp)
            results[lang]='STRUCTURAL_PASS' if out['structural_review_passed']==1 and not out['reasons'] else 'HOLD_STRUCTURAL_QUALITY'
        except Exception as exc:
            results[lang]='HOLD_'+type(exc).__name__
    return {'schema':'aggregateit-v2-b45-named-free/1','checked_at':datetime.now(timezone.utc).isoformat(),
        'status':'CANDIDATE_FREE_MODEL_STRUCTURAL_PASS' if all(v=='STRUCTURAL_PASS' for v in results.values())
          else 'HOLD_INCOMPLETE_FREE_MODEL_QUALITY',
        'attempts':2,'languages':results,'model':MODEL,
        'paid_calls':0,'real_free_model_called':True,
        'actual_second_provider_verified':False,
        'real_independent_primary_to_fallback_failover_verified':False,
        'real_publisher_translation_quality_verified':False,
        'factual_semantic_coverage_verified':False,
        'discord_sent':False,'can_release':False}
if __name__=='__main__':
    import json,argparse
    from pathlib import Path
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    o=p.parse_args();res=evaluate_named_free()
    o.output.parent.mkdir(parents=True,exist_ok=True)
    o.output.write_text(json.dumps(res,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':res['status'],'lang_results':res['languages'],
      'attempts':res['attempts'],'model_family':'named_verified_free_nvidia',
      'paid_calls':0,'can_release':False}))
