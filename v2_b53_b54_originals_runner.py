"""B53/B54 one-shot actual archived main artifacts into sanitized hold record."""
import argparse,json,os,subprocess
from pathlib import Path
from v2_b49_archived_edition_runner import get_artifact
from v2_b53_authentic_full_editions import (
    EXPECTED_ORIGINALS,inspect_original_final_edition,assess_original_final_pair,decide_acceptance)

def execute(token,root):
    records=[]
    for product in ('english','arabic'):
        v=EXPECTED_ORIGINALS[product]
        raw=get_artifact('4mghonly/AggregateIT',v['artifact_id'],token)
        records.append(inspect_original_final_edition(raw,product=product,
          run_id=v['run_id'],expected_zip_sha256=v['zip_sha256']))
    old=assess_original_final_pair(records,v2_observed_at='2026-10-27T09:15:59.555886+00:00')
    dep=Path(root)/'.github/workflows/audit.yml'
    config=dep.read_text(encoding='utf8')
    # A workflow YAML may include requests as a word in comments; inspect pip steps.
    pip_lines=[line.strip() for line in config.splitlines() if 'pip install' in line]
    good=bool(pip_lines and any('requests' in x.split() for x in pip_lines))
    release=decide_acceptance(old,source_audit_healthy=good)
    production_sha=subprocess.check_output(
        ['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    return {'schema':'aggregateit-v2-b53-b54-authentic-baseline/1',
      'source_production_main_sha':production_sha,
      'live_originals':records,'original_pair':old,'release':release,
      'production_audit_requests_installed':good,
      'model_provider_calls':0,'live_articles_fetched':0,
      'original_page_bytes_uploaded':False,'main_modified':False,
      'discord_sent':False,'can_release':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path)
    p.add_argument('--main-root',required=True,type=Path)
    a=p.parse_args()
    try:result=execute(os.getenv('GITHUB_TOKEN',''),a.main_root)
    except Exception as exc:
        result={'schema':'aggregateit-v2-b53-b54-authentic-baseline/1',
          'status':'HOLD_ORIGINAL_ARCHIVE_INSPECTION_FAILURE',
          'failure_class':type(exc).__name__,'can_release':False,
          'main_modified':False,'discord_sent':False}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    accepted=result.get('release',{})
    print(json.dumps({'status':accepted.get('status',result.get('status')),
      'genuine_v1_visuals_both_products':accepted.get('original_en_ar_native_page_baselines_confirmed',False),
      'blocker_count':accepted.get('critical_blocker_count'),
      'audit_dependency_ok':result.get('production_audit_requests_installed'),
      'canary_authorized':False,'can_release':False}))
