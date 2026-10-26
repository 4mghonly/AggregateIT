"""B28 rollback tabletop with synthetic state; never deploys or flips a route."""
from __future__ import annotations


def rehearse_canary_rollback(*, baseline_sha: str, candidate_sha: str,
                             incident: str, receipts: list[dict]) -> dict:
    if (not isinstance(baseline_sha, str) or not isinstance(candidate_sha, str)
            or len(baseline_sha) != 40 or len(candidate_sha) != 40
            or baseline_sha == candidate_sha or any(c not in '0123456789abcdef' for c in baseline_sha + candidate_sha)):
        raise ValueError('invalid_rollback_heads')
    if incident not in ('render_quality', 'source_integrity', 'delivery_ambiguity', 'schedule_regression'):
        raise ValueError('invalid_incident')
    if not isinstance(receipts, list) or len(receipts) > 50:
        raise ValueError('invalid_receipt_list')
    ambiguous = 0
    for receipt in receipts:
        if not isinstance(receipt, dict) or receipt.get('product') not in ('english', 'arabic'):
            raise ValueError('invalid_canary_receipt')
        if receipt.get('status') not in ('unsent', 'confirmed', 'ambiguous'):
            raise ValueError('invalid_canary_status')
        ambiguous += receipt['status'] == 'ambiguous'
    return {'schema': 'aggregateit-v2-b28-canary-rollback/1',
            'baseline_ref': baseline_sha, 'candidate_ref': candidate_sha,
            'incident': incident, 'total_receipts': len(receipts),
            'ambiguous_receipts': ambiguous,
            'plan': ['freeze_candidate', 'retain_ambiguous_receipts',
                     'switch_symbolic_route_to_baseline', 'verify_baseline_health',
                     'do_not_replay_ambiguous_delivery'],
            'dry_run': True, 'routes_changed': False,
            'production_reverted': False, 'discord_sent': False,
            'rollback_acceptance': 'TABLETOP_ONLY'}
