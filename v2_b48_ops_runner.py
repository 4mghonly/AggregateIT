"""B48 run latest B47 genuine held receipts and inspect production read-only."""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse
import json
from v2_b46_live_editorial_runner import run
from v2_b41_production_preflight import inspect_workflows
from v2_b39_rollback_rehearsal import exercise_durable_no_send
from v2_b48_operations_readiness import evaluate_operations

def run_batch(production_dir:Path,candidate_dir:Path):
    observed_at=datetime.now(timezone.utc).isoformat()
    live=run(render_four_products=True)
    if live.get('four_products',{}).get('schema')!='aggregateit-v2-b47-four-product-held/1':
        return {'schema':'aggregateit-v2-b48-live-ops/1',
                'status':'HOLD_GENUINE_FOUR_PRODUCTS_NOT_AVAILABLE',
                'failure_class':live.get('four_products',{}).get('status','missing'),
                'source_attempts':live.get('source_attempts',{}),
                'main_modified':False,'discord_sent':False,'can_release':False}
    prod=inspect_workflows(baseline_root=production_dir,candidate_root=candidate_dir)
    with TemporaryDirectory(prefix='aggregateit-b48-recovery-') as tmp:
        durable=exercise_durable_no_send(Path(tmp),slot_id=observed_at)
    report=evaluate_operations(live['four_products'],prod,durable,observed_at=observed_at)
    return {'schema':'aggregateit-v2-b48-live-ops/1','status':report['status'],
            'source_attempts':live.get('source_attempts',{}),
            'operations':report,'production_modified':False,'discord_sent':False,
            'can_release':False}

if __name__=='__main__':
    args=argparse.ArgumentParser()
    args.add_argument('--baseline',required=True,type=Path)
    args.add_argument('--candidate',default='.',type=Path)
    args.add_argument('--output',required=True,type=Path)
    options=args.parse_args()
    result=run_batch(options.baseline,options.candidate)
    options.output.parent.mkdir(parents=True,exist_ok=True)
    options.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'status':result['status'],
                      'alert_count':len(result.get('operations',{}).get('alerts',[])),
                      'critical':result.get('operations',{}).get('alert_summary',{}).get('critical',0),
                      'durable_reopen_ok':result.get('operations',{}).get('durable_ambiguous_state_persists'),
                      'can_release':False}))
