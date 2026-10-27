"""B44/45 isolated read-only runner, same captured RSS bytes, no LLM or Discord."""
import json
from pathlib import Path
from datetime import datetime,timezone
from v2_b43_somalia_production_validation import _CANDIDATES,audit_one,collector_same_bytes,language_route
from v2_b44_staged_registry import candidates,coverage
from v2_b45_source_translation_review import samples_for_source,inspect_translations,pending_summary

def run(registry_path,audit_path):
    registry=json.loads(Path(registry_path).read_text(encoding='utf8'))
    audit=json.loads(Path(audit_path).read_text(encoding='utf8'))
    staged={r['id']:r for r in candidates(registry)}
    evidence=[];samples=[]
    for initial in _CANDIDATES:
        stage=staged[initial['id']]
        if stage['entrypoint']!=initial['feed'] or stage['language']!=initial['language']:
            raise ValueError('candidate_registry_drift')
        source={**initial,'enabled':False}
        outcome,raw,trace=audit_one(source)
        rows=[];health={}
        if raw is not None:
            rows,health=collector_same_bytes(source,raw)
            samples.extend(samples_for_source(source,rows,max_samples=2))
        now=datetime.now(timezone.utc).timestamp()
        fresh=sum(type(row.get('published')) in (int,float)
                  and 0<=now-row['published']<=259200 for row in rows)
        route=language_route(rows,declared_language=source['language'])
        evidence.append({'candidate_id':initial['id'],
          'production_compatible':outcome.get('production_compatible') is True,
          'source_entries':outcome.get('entries',0),'collector_status':health.get('status','unavailable'),
          'collector_items':len(rows),'recent_72h':fresh,
          'observed_language_guess':route['aggregated_headline_language_guess'],
          'declared_language':source['language'],'feed_sha256':trace.get('feed_sha256'),
          'translation_pending':True,'enabled':False})
    regional=coverage(registry,audit,evidence)
    translation=pending_summary(samples)
    review=inspect_translations(samples,{'items':[]})
    return {'schema':'aggregateit-v2-b44-b45-integration/1',
       'observed_at':datetime.now(timezone.utc).isoformat(),
       'candidates':evidence,'coverage':regional,'translation_demand':translation,
       'untranslated_sample_rejections':review['reasons'],
       'real_model_calls':0,'real_arabic_quality_verified':False,
       'production_audit_reexecuted':False,'production_registry_modified':False,
       'discord_sent':False,'can_release':False}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--production-audit',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    result=run('config/v2/source_registry.json',a.production_audit)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'status':'HOLD_LIVE_TRANSLATION',
      'somalia_technical_candidates':result['coverage']['live_candidate_technical_families'],
      'production_below_floor':result['coverage']['production_regions_below_floor'],
      'translation_samples':result['translation_demand']['sample_count'],
      'candidate_health':[{'id':x['candidate_id'],'fresh':x['recent_72h']} for x in result['candidates']],
      'can_release':False},ensure_ascii=False))
