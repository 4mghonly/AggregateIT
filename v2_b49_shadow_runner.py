"""B49 no-post same-snapshot V1/V2 partial acceptance diagnostic."""
import argparse
import json
from pathlib import Path
from v2_b49_single_slot_shadow import run_one_slot

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    report=run_one_slot()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(json.dumps({'status':report['status'],
        'parser_parity':report.get('all_parser_parity'),
        'headline_parity':report.get('all_source_headline_parity'),
        'four_v2_products':report.get('v2_four_products_held'),
        'v1_v2_full_editorial_compared':False,
        'can_release':False}))
