"""B49 no-post same-snapshot V1/V2 partial acceptance diagnostic."""
import argparse
import json
from pathlib import Path
from v2_b49_single_slot_shadow import run_one_slot

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--production-baseline',type=Path)
    parser.add_argument('--candidate-root',type=Path)
    args=parser.parse_args()
    report=run_one_slot(production_baseline=args.production_baseline,
                       candidate_root=args.candidate_root)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(json.dumps({'status':report['status'],
        'parser_parity':report.get('all_parser_parity'),
        'headline_parity':report.get('all_source_headline_parity'),
        'four_v2_products':report.get('v2_four_products_held'),
        'ops_alert_count':len((report.get('operational_preflight') or {}).get('alerts',[])),
        'joined_b47_b48_b49':report.get('same_live_capture_used_for_b47_b48_b49'),
        'v1_v2_full_editorial_compared':False,
        'can_release':False}))
