"""B33 exact-byte capture intake and dual V1/V2 parser evidence receipt.

This is an *offline import* interface. A matching SHA proves byte integrity
relative to the supplied receipt, not the publisher or collection provenance.
No network access or production publication is performed here.
"""
from __future__ import annotations

from hashlib import sha256

from v2_b26_parser_shadow import compare_parser_outputs
from v2_b31_same_input_shadow import compare_exact_input
from v2_feed_probe import _date, _url_safe, inspect_feed_bytes


def compare_imported_capture(raw: bytes, *, receipt: dict) -> dict:
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= 1_000_000:
        raise ValueError('invalid_capture_byte_budget')
    if not isinstance(receipt, dict) or receipt.get('schema') != 'aggregateit-v2-b33-import/1':
        raise ValueError('invalid_capture_receipt')
    if receipt.get('product') not in ('english', 'arabic'):
        raise ValueError('unknown_capture_product')
    if receipt.get('capture_kind') not in ('synthetic_fixture', 'unattested_external_bytes'):
        raise ValueError('invalid_capture_kind')
    url = receipt.get('feed_url')
    _url_safe(url)
    observed = _date(receipt.get('observed_at'))
    if observed is None:
        raise ValueError('invalid_capture_time')
    digest = sha256(raw).hexdigest()
    if receipt.get('sha256') != digest or receipt.get('size_bytes') != len(raw):
        raise ValueError('capture_integrity_mismatch')
    parser = compare_parser_outputs(raw, feed_url=url,
                observed_at=observed.isoformat(), input_provenance='synthetic')
    v1_v2 = compare_exact_input(raw, feed_url=url,
                 observed_at=observed.isoformat(), product=receipt['product'])
    observation = inspect_feed_bytes(raw, now=observed.isoformat(), max_bytes=1_000_000)
    return {'schema': 'aggregateit-v2-b33-import-comparison/1',
            'product': receipt['product'], 'feed_url': url,
            'input_sha256': digest, 'input_bytes': len(raw),
            'observation': observation, 'stdlib_feedparser': parser,
            'v1_v2_same_input': v1_v2,
            'import_integrity_verified': True,
            'external_provenance_authenticated': False,
            'live_retrieval_performed': False,
            'can_publish': False, 'discord_sent': False}
