"""B15 read-only source-health snapshots with explicit unknowns."""
from __future__ import annotations


def summarize_source_watch(observations: list[dict], *, expected_source_ids: list[str]) -> dict:
    if not isinstance(observations, list) or not isinstance(expected_source_ids, list):
        raise ValueError('invalid_source_watch')
    if len(set(expected_source_ids)) != len(expected_source_ids) or len(expected_source_ids) > 300:
        raise ValueError('invalid_expected_sources')
    by_id = {}
    for obs in observations:
        if not isinstance(obs, dict) or obs.get('source_id') not in expected_source_ids:
            raise ValueError('unregistered_source_observation')
        source_id = obs['source_id']
        if source_id in by_id:
            raise ValueError('duplicate_source_observation')
        status = obs.get('status')
        if status not in ('usable_dated_feed', 'stale_feed', 'undated_feed', 'empty_feed',
                          'invalid_xml', 'not_a_feed', 'network_error', 'blocked', 'unprobed'):
            raise ValueError('invalid_source_status')
        if (status == 'usable_dated_feed' and (type(obs.get('recent_count')) is not int
                                                  or obs['recent_count'] < 1)):
            raise ValueError('invalid_recent_count')
        by_id[source_id] = {'source_id': source_id, 'status': status,
                            'recent_count': obs.get('recent_count', 0) if status == 'usable_dated_feed' else 0,
                            'can_promote': False}
    rows = [by_id.get(source_id, {'source_id': source_id, 'status': 'unprobed',
                                 'recent_count': 0, 'can_promote': False}) for source_id in expected_source_ids]
    return {'schema': 'aggregateit-v2-b15-watch/1', 'sources': rows,
            'healthy_count': sum(r['status'] == 'usable_dated_feed' for r in rows),
            'unknown_count': sum(r['status'] in ('network_error', 'blocked', 'unprobed') for r in rows),
            'registry_unchanged': True, 'auto_replacement': False, 'delivery_authorized': False}
