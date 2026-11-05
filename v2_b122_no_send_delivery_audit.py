"""B122 read-only production contract comparison and durable no-post rollback test."""
from __future__ import annotations
from pathlib import Path
from v2_replacement_contract import check_contract
from v2_b39_rollback_rehearsal import exercise_durable_no_send
from v2_discord_edition import DESTINATIONS
from v2_delivery_gate import DESTINATION_KEYS

def audit_no_send_delivery(repo_root:Path,empty_rehearsal_dir:Path,*,slot_id:str)->dict:
    contract=check_contract(Path(repo_root))
    rehearsal=exercise_durable_no_send(Path(empty_rehearsal_dir),slot_id=slot_id)
    distinct=(set(DESTINATIONS)=={'english','arabic'}
              and len(set(DESTINATIONS.values()))==2
              and DESTINATIONS==DESTINATION_KEYS)
    return {
        'schema':'aggregateit-v2-b122-no-send-delivery-audit/1',
        'v1_schedule_continuity_checked':contract['continuity_verified'],
        'v2_distinct_destination_keys':distinct,
        'ambiguous_network_outcome_persisted':rehearsal['ambiguous_survived_reopen'],
        'blind_retry_refused':rehearsal['blind_retry_refused'],
        'wrong_channel_refused':rehearsal['wrong_destination_refused'],
        'rollback_rehearsal':rehearsal['rollback_acceptance'],
        'live_v1_receipts_present':False,
        'live_v2_receipts_present':False,
        'authenticated_v1_v2_delivery_parity_verified':False,
        'actual_rollout_or_rollback_exercised':False,
        'retry_allowed':rehearsal['retry_allowed'],
        'discord_sent':False,
        'production_modified':False,
        'release_status':'HOLD',
        'can_release':False,
    }

if __name__=='__main__':
    from tempfile import TemporaryDirectory
    import json
    from datetime import datetime,timezone
    with TemporaryDirectory(prefix='b122-no-send-') as td:
        result=audit_no_send_delivery(Path('.'),Path(td),slot_id=datetime.now(timezone.utc).isoformat())
    Path("b122_no_send_delivery.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps(result,sort_keys=True))
