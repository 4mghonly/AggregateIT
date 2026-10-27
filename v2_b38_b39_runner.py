"""B38-B39 bounded read-only hosted runner; writes aggregate metadata only."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from v2_b38_live_pair import run_live_pairs
from v2_b39_rollback_rehearsal import exercise_durable_no_send,assess_cutover_blockers

def run():
    shadow=run_live_pairs()
    with TemporaryDirectory(prefix='aggregateit-b39-') as d:
        durable=exercise_durable_no_send(Path(d),slot_id='2026-10-27T06:00:00+04:00')
    gate=assess_cutover_blockers(shadow,durable)
    if not (durable['ambiguous_survived_reopen'] and durable['blind_retry_refused']
            and durable['wrong_destination_refused'] and not durable['retry_allowed']):
        raise RuntimeError('local_durable_replay_safety_failed')
    return {'schema':'aggregateit-v2-b38-b39-report/1',
            'same_input_shadow':shadow,'durable_failure_rehearsal':durable,
            'cutover_preflight':gate,'production_changed':False,'discord_sent':False}

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True)
    a=ap.parse_args()
    report=run()
    output=Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(json.dumps({'shadow_status':report['same_input_shadow']['status'],
                       'parity_all':report['same_input_shadow']['parity_all'],
                       'crash_marker_durable':report['durable_failure_rehearsal']['ambiguous_survived_reopen'],
                       'can_release':report['cutover_preflight']['can_release']}))
