"""B39 local durable ambiguous-send preservation and no-cutover gate. NO SENDER."""
from __future__ import annotations
from pathlib import Path
from v2_delivery_receipt_store import DurableReceiptStore
from v2_b28_canary_rehearsal import rehearse_canary_rollback
from v2_delivery_gate import DESTINATION_KEYS

def exercise_durable_no_send(directory: Path, *, slot_id: str) -> dict:
    directory=Path(directory)
    if not directory.is_dir() or any(directory.iterdir()):
        raise ValueError('rehearsal_directory_must_be_empty')
    values={'english':'e'*64,'arabic':'a'*64}
    with DurableReceiptStore(directory) as store:
        for product in sorted(values):
            store.reserve(product=product,slot_id=slot_id,
                          destination_key=DESTINATION_KEYS[product],edition_digest=values[product])
        wrong_destination_refused=False
        try:
            store.reserve(product='arabic',slot_id=slot_id,
                          destination_key=DESTINATION_KEYS['english'],edition_digest=values['arabic'])
        except ValueError:
            wrong_destination_refused=True
        for product in sorted(values):
            store.mark_network_attempt(product=product,slot_id=slot_id)
    with DurableReceiptStore(directory) as restored:
        states={p:restored.snapshot(product=p,slot_id=slot_id) for p in sorted(values)}
        retry={p:restored.retry_allowed(product=p,slot_id=slot_id) for p in sorted(values)}
        blind_retry_refused=False
        try:
            restored.mark_network_attempt(product='english',slot_id=slot_id)
        except ValueError:
            blind_retry_refused=True
    ambiguous=all(s['state']=='ambiguous_network_outcome' for s in states.values())
    tabletop=rehearse_canary_rollback(baseline_sha='a'*40,candidate_sha='b'*40,
                       incident='delivery_ambiguity',
                       receipts=[{'product':p,'status':'ambiguous'} for p in sorted(values)])
    return {'schema':'aggregateit-v2-b39-no-send-durable-rehearsal/1',
            'products':sorted(values),'ambiguous_survived_reopen':ambiguous,
            'retry_allowed':any(retry.values()),
            'wrong_destination_refused':wrong_destination_refused,
            'blind_retry_refused':blind_retry_refused,
            'ambiguous_count':tabletop['ambiguous_receipts'],
            'rollback_acceptance':tabletop['rollback_acceptance'],
            'rollback_actuated':False,'production_modified':False,
            'discord_sent':False,'can_release':False}

def assess_cutover_blockers(shadow: dict, rehearsal: dict) -> dict:
    if (not isinstance(shadow,dict) or shadow.get('schema')!='aggregateit-v2-b38-live-parser-pair/1'
        or not isinstance(rehearsal,dict) or rehearsal.get('schema')!='aggregateit-v2-b39-no-send-durable-rehearsal/1'):
        raise ValueError('untrusted_cutover_evidence')
    blockers=['no_authenticated_full_system_v1_v2_comparison',
              'unverified_live_discord_client','unverified_production_rollback',
              'controlled_cutover_not_authorized']
    if shadow.get('status')!='COMPARED' or shadow.get('parity_all') is not True:
        blockers.insert(0,'live_parser_parity_not_complete')
    if (rehearsal.get('ambiguous_survived_reopen') is not True
        or rehearsal.get('retry_allowed') is not False
        or rehearsal.get('wrong_destination_refused') is not True
        or rehearsal.get('blind_retry_refused') is not True):
        blockers.insert(0,'durable_ambiguity_rehearsal_not_passed')
    return {'schema':'aggregateit-v2-b39-cutover-preflight/1',
            'status':'HOLD','can_release':False,'can_send':False,
            'blockers':blockers,'no_owner_approval_asserted':True,
            'discord_sent':False,'production_modified':False}
