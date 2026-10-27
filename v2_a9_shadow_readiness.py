"""B7 V1/V2 genuine-window availability gate; never turn missing data into zero.

Attestation flags are caller declarations, *not* cryptographic proof. The
comparison remains offline and cannot authorize release even when comparable.
"""
from __future__ import annotations

from v2_shadow_scorecard import _window_identity, compare_runs, validate_run


def _held(reason: str) -> dict:
    return {
        'schema': 'aggregateit-v2-a9-shadow-readiness/1',
        'comparable': False,
        'reason': reason,
        'status': 'hold_missing_or_unverified_evidence',
        'metrics_authentication': 'not_proven_by_this_module',
        'delivery_authorized': False,
    }


def classify_shadow_pair(v1: dict | None, v2: dict | None, *,
                         v1_attested: bool = False,
                         v2_attested: bool = False) -> dict:
    """Require separate genuine same-window V1 and V2 run logs.

    Metrics are still caller-supplied, and this function does not authenticate
    them. An operator must retain and verify originals outside this function.
    """
    if type(v1_attested) is not bool or type(v2_attested) is not bool:
        raise ValueError('invalid_attestation_flag')
    if v1 is None:
        return _held('v1_baseline_missing')
    if v2 is None:
        return _held('v2_candidate_missing')
    a, b = validate_run(v1), validate_run(v2)
    if _window_identity(a) != _window_identity(b):
        return _held('different_product_or_window')
    if a['code_revision'] == b['code_revision']:
        return _held('revisions_not_distinct')
    if not (v1_attested and v2_attested):
        return _held('unattested_run_metrics')
    report = compare_runs(a,b)
    report['metrics_authentication'] = 'caller_attested_not_independently_proven'
    report['delivery_authorized'] = False
    return report
