"""B17 engineering acceptance only. No rights/legal decision or live sending."""
from __future__ import annotations


REQUIRED = ('dependency_suite_passed', 'source_parser_parity_passed',
            'bilingual_preview_passed', 'destination_isolation_passed',
            'rollback_rehearsal_passed', 'live_same_window_measured')


def evaluate_release_readiness(evidence: dict) -> dict:
    if not isinstance(evidence, dict):
        raise ValueError('invalid_release_evidence')
    missing = [key for key in REQUIRED if evidence.get(key) is not True]
    # Even complete *technical* rehearsal can only nominate a candidate.
    return {'schema': 'aggregateit-v2-b17-technical-readiness/1',
            'checks': {key: evidence.get(key) is True for key in REQUIRED},
            'unmet_checks': missing, 'candidate_ready': not missing,
            'production_cutover_performed': False, 'can_send': False,
            'rights_or_legal_review_in_scope': False}
