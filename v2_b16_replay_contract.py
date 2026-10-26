"""B16 exact-source offline replay manifest, independent of mutable URLs."""
from __future__ import annotations

from hashlib import sha256
from json import dumps


def build_replay_manifest(items: list[dict]) -> dict:
    if not isinstance(items, list) or not 1 <= len(items) <= 250:
        raise ValueError('invalid_replay_items')
    records = []
    keys = set()
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get('source_revision'), str) or not item['source_revision']:
            raise ValueError('missing_source_revision')
        if not isinstance(item.get('source_bytes'), bytes) or not item['source_bytes']:
            raise ValueError('missing_source_bytes')
        if not isinstance(item.get('source_id'), str) or not item['source_id']:
            raise ValueError('invalid_source_id')
        key = (item['source_id'], item['source_revision'])
        if key in keys:
            raise ValueError('duplicate_source_revision')
        keys.add(key)
        records.append({'source_id': key[0], 'source_revision': key[1],
                        'size_bytes': len(item['source_bytes']),
                        'sha256': sha256(item['source_bytes']).hexdigest()})
    records.sort(key=lambda r: (r['source_id'], r['source_revision']))
    encoded = dumps(records, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf8')
    return {'schema': 'aggregateit-v2-b16-exact-replay/1', 'records': records,
            'manifest_sha256': sha256(encoded).hexdigest(), 'replayable_if_bytes_retained': True,
            'source_bytes_embedded': False, 'delivery_authorized': False}


def verify_replay_manifest(manifest: dict, items: list[dict]) -> bool:
    if not isinstance(manifest, dict) or manifest.get('schema') != 'aggregateit-v2-b16-exact-replay/1':
        return False
    try:
        expected = build_replay_manifest(items)
    except (ValueError, TypeError):
        return False
    return manifest == expected
