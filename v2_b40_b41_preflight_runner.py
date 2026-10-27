"""B40/B41 one-shot live source preview and main-read-only preflight batch."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
from v2_b38_live_pair import SOURCES,MAX_BYTES,_failure_code
from v2_secure_transport import pinned_https_fetch
from v2_b40_shared_preview import compare_previews
from v2_b41_production_preflight import inspect_workflows
from v2_b28_canary_rehearsal import rehearse_canary_rollback

def run_batch(baseline_root:Path,candidate_root:Path):
    observed=datetime.now(timezone.utc).isoformat()
    captures=[]
    for product,label,url in SOURCES:
        row={'product':product,'source_label':label,'status':'HOLD'}
        try:
            packet=pinned_https_fetch(url,timeout=9,max_bytes=MAX_BYTES,max_redirects=1,
                       headers={'Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml'})
            finding=compare_previews(packet['body'],product=product,feed_url=packet['final_url'],
                                      observed_at=observed)
            row.update(finding)
            row['status']='COMPARED' if finding['identity_parity'] else 'HOLD_MISMATCH'
        except Exception as exc:
            row['failure_class']=_failure_code(exc)
        captures.append(row)
    prod=inspect_workflows(baseline_root=baseline_root,candidate_root=candidate_root)
    rehearsal=rehearse_canary_rollback(
        baseline_sha=prod['baseline_main_sha'],
        candidate_sha=prod['candidate_v2_sha'],
        incident='schedule_regression',
        receipts=[{'product':'english','status':'unsent'},
                  {'product':'arabic','status':'ambiguous'}])
    result={'schema':'aggregateit-v2-b40-b41-independent-batch/1',
            'live_source_headline_previews':captures,
            'preflight':prod,
            'rollback_tabletop':rehearsal,
            'all_source_only_previews_aligned':all(x['status']=='COMPARED' for x in captures),
            'actual_full_v1_v2_editorial_compared':False,
            'native_live_news_pages_compared':False,
            'translation_or_fallback_tested':False,
            'live_canary_performed':False,
            'no_post':True,'main_modified':False,'discord_sent':False,
            'can_release':False}
    if any(p['status'] not in ('COMPARED','HOLD','HOLD_MISMATCH') for p in captures):
        raise ValueError('unexpected_capture_status')
    if result['preflight']['can_release'] is not False or result['rollback_tabletop']['rollback_acceptance']!='TABLETOP_ONLY':
        raise ValueError('untrusted_release_claim')
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--baseline-root',type=Path,required=True)
    ap.add_argument('--candidate-root',type=Path,default=Path('.'))
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    report=run_batch(args.baseline_root,args.candidate_root)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(json.dumps({'live_preview_status':[{'source':x['source_label'],'status':x['status'],
                      'parity':x.get('identity_parity')} for x in report['live_source_headline_previews']],
                      'main_sha':report['preflight']['baseline_main_sha'],
                      'workflow_findings':report['preflight']['preflight_findings'],
                      'can_release':False},ensure_ascii=False))
