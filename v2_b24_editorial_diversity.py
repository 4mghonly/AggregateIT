"""B24 represented-region and topic balance without fabricated coverage."""
from __future__ import annotations

from collections import Counter


def coverage_diagnostic(digest: dict, *, target_regions: list[str], max_source_share: float = .5) -> dict:
    if not isinstance(digest, dict) or digest.get('schema') != 'aggregateit-v2-b18-private-digest/1':
        raise ValueError('invalid_diversity_digest')
    if not isinstance(target_regions, list) or len(target_regions) != len(set(target_regions)):
        raise ValueError('invalid_target_regions')
    if type(max_source_share) not in (float, int) or not 0 < max_source_share <= 1:
        raise ValueError('invalid_max_source_share')
    rows = digest['stories']
    regions = Counter(row['region'] for row in rows)
    topics = Counter(row['topic'] for row in rows)
    sources = Counter(row['source_id'] for row in rows)
    missing = [region for region in target_regions if regions[region] == 0]
    source_share = max(sources.values()) / len(rows) if rows else None
    return {'schema': 'aggregateit-v2-b24-editorial-coverage/1',
            'product': digest['product'], 'represented_regions': sorted(regions),
            'missing_target_regions': missing, 'topic_counts': dict(sorted(topics.items())),
            'distinct_sources': len(sources), 'max_source_share': source_share,
            'source_concentration_warning': source_share is not None and source_share > max_source_share,
            'coverage_complete': not missing and bool(rows),
            'publisher_independence_verified': False, 'delivery_authorized': False}
