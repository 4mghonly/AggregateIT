"""B25 private failure classification; refuses unbounded automatic retries."""
from __future__ import annotations


def plan_private_recovery(*, stage: str, failure_code: str, attempts: int,
                          last_verified_snapshot: dict | None = None) -> dict:
    stages = {'source_fetch', 'parse', 'evidence', 'editorial', 'render', 'packet'}
    temporary = {'network_error', 'http_429', 'http_502', 'http_503', 'timeout'}
    permanent = {'unsafe_url', 'invalid_source', 'schema_error', 'missing_evidence',
                 'language_mismatch', 'checksum_mismatch'}
    if stage not in stages or failure_code not in temporary | permanent:
        raise ValueError('invalid_recovery_event')
    if type(attempts) is not int or not 0 <= attempts <= 3:
        raise ValueError('invalid_attempt_count')
    previous = None
    if last_verified_snapshot is not None:
        if (not isinstance(last_verified_snapshot, dict)
                or last_verified_snapshot.get('schema') != 'aggregateit-v2-b21-private-snapshot/1'
                or last_verified_snapshot.get('private_only') is not True):
            raise ValueError('untrusted_prior_snapshot')
        previous = {'sha256': last_verified_snapshot['sha256'],
                    'observed_at': last_verified_snapshot['observed_at'],
                    'stale_fallback_only': True}
    retry_eligible = failure_code in temporary and attempts < 2
    return {'schema': 'aggregateit-v2-b25-private-recovery/1', 'stage': stage,
            'failure_code': failure_code, 'attempts_seen': attempts,
            'retry_eligible': retry_eligible, 'retry_automatically': False,
            'last_verified_preview': previous, 'quality_degraded': True,
            'can_publish': False, 'discord_sent': False}
