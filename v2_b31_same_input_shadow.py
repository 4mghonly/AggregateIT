"""B31 exact-input V1/V2 *parser* comparison, no collection or publication.

The V1 parser functions are invoked unmodified with their network functions
replaced by an in-memory feed. SHA-1 Git blob identities pin the actual code
to the read-only main snapshot independently checked on 26 October 2026.
This does not compare model decisions, rendered pages or delivery outcomes.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from hashlib import sha1, sha256
from html import unescape
from pathlib import Path
import re
from unittest.mock import AsyncMock, patch

from v2_feed_items import extract_candidates
from v2_feed_probe import _date, _url_safe

V1_REFERENCE_COMMIT = 'cb10eb38c056755903434d1327de878b0d1d0b38'
V1_MAIN_BLOB = '6c7915ab5b46ee6220bc59657e28a2fb08d1ad86'
V1_AR_COLLECT_BLOB = 'ddbcd27d959b0aea07e269b925539906c90ef340'


def _git_blob(relpath: str) -> str:
    raw = (Path(__file__).resolve().parent / relpath).read_bytes()
    return sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()


def _verified_v1_code() -> bool:
    return (_git_blob('main.py') == V1_MAIN_BLOB and
            _git_blob('arabic_newsletter/collect.py') == V1_AR_COLLECT_BLOB)


async def _english_v1(feed_bytes: bytes, feed_url: str, now: datetime) -> list[dict]:
    # V1 main creates data/report directories at import time. Suppress those
    # unrelated side effects; this harness exercises fetch_rss only.
    with patch('os.makedirs'), patch('storage.SQLiteStore', return_value=None):
        import main
    source = {'Source_name': 'B31 exact-input reference', 'Category': 'Controlled RSS',
              '_url': feed_url}
    with (patch.object(main, 'fetch_text', new=AsyncMock(return_value=feed_bytes)),
          patch.object(main.audit, 'is_muted', return_value=False),
          patch.object(main.audit, 'record'),
          patch.object(main, 'HEALTH', {'rss_fail': 0, 'rss_ok': 0, 'rss_empty': 0}),
          patch.object(main.time, 'time', return_value=now.timestamp())):
        return await main.fetch_rss(None, source, asyncio.Semaphore(1))


def _arabic_v1(feed_bytes: bytes, feed_url: str) -> list[dict]:
    import arabic_newsletter.collect as legacy
    source = {'id': 'b31-input', 'name': 'B31 exact-input reference',
              'region': 'gcc', 'country': 'AE', 'language': 'ar',
              'affiliation': 'unverified', 'feed': feed_url,
              'website': feed_url, 'social': []}
    with patch.object(legacy, 'fetch', return_value=feed_bytes):
        items, _status = legacy.collect_source(source, discover=False)
    return items


def _fingerprint(url: str, title: str, published: datetime) -> str:
    norm_title = re.sub(r'\s+', ' ', unescape(title)).strip()
    return sha256((url.strip() + '\n' + norm_title + '\n' +
                   published.astimezone(timezone.utc).isoformat()).encode('utf8')).hexdigest()


def compare_exact_input(feed_bytes: bytes, *, feed_url: str, observed_at: str,
                        product: str, max_age_hours: int = 72) -> dict:
    """Run both parser versions on one unchanged buffer, with zero live I/O.

    Provenance and actual transport success cannot be certified by a caller
    handing us bytes; the result stays offline/unsendable even if aligned.
    """
    if product not in ('english', 'arabic'):
        raise ValueError('unknown_product')
    if not isinstance(feed_bytes, bytes) or not 1 <= len(feed_bytes) <= 1_000_000:
        raise ValueError('invalid_exact_input_bytes')
    _url_safe(feed_url)
    now = _date(observed_at)
    if now is None:
        raise ValueError('invalid_observation_window')
    if type(max_age_hours) is not int or not 1 <= max_age_hours <= 168:
        raise ValueError('invalid_window_length')
    if not _verified_v1_code():
        raise ValueError('v1_parser_code_drift')
    if product == 'english':
        legacy_rows = asyncio.run(_english_v1(feed_bytes, feed_url, now))
        cap = 5  # exact V1 main.MAX_PER_SOURCE, pinned above
    else:
        legacy_rows = _arabic_v1(feed_bytes, feed_url)
        cap = 35  # exact V1 Arabic collect_source entries cap
    v2 = extract_candidates(feed_bytes, feed_url=feed_url, observed_at=now.isoformat(),
                            max_items=cap, max_age_hours=max_age_hours, max_bytes=1_000_000)
    v1_keys: set[str] = set()
    v1_excluded = {'undated': 0, 'outside_window': 0, 'unsafe_link_or_title': 0}
    for row in legacy_rows:
        timestamp = row.get('ts') if product == 'english' else row.get('published')
        if not isinstance(timestamp, (int, float)) or isinstance(timestamp, bool):
            v1_excluded['undated'] += 1
            continue
        published = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        age = (now - published).total_seconds()
        if not -300 <= age <= max_age_hours * 3600:
            v1_excluded['outside_window'] += 1
            continue
        url = row.get('url', '')
        title = row.get('title', '')
        try:
            _url_safe(url)
        except ValueError:
            v1_excluded['unsafe_link_or_title'] += 1
            continue
        if not isinstance(title, str) or not 5 <= len(title.strip()) <= 300:
            v1_excluded['unsafe_link_or_title'] += 1
            continue
        v1_keys.add(_fingerprint(url, title, published))
    v2_keys = set(_fingerprint(row['article_url'], row['title'],
                               _date(row['published_at'])) for row in v2['items'])
    return {'schema': 'aggregateit-v2-b31-same-input-v1-v2/1',
            'product': product, 'v1_reference_commit': V1_REFERENCE_COMMIT,
            'v1_parser_blob_verified': True, 'input_sha256': sha256(feed_bytes).hexdigest(),
            'input_bytes': len(feed_bytes), 'observation_window_at': now.isoformat(),
            'max_age_hours': max_age_hours, 'v1_extracted_count': len(legacy_rows),
            'v1_window_eligible': len(v1_keys), 'v1_excluded': v1_excluded,
            'v2_window_eligible': len(v2_keys), 'v2_rejected': v2['rejected'],
            'matching_items': len(v1_keys & v2_keys),
            'v1_only': sorted(v1_keys - v2_keys), 'v2_only': sorted(v2_keys - v1_keys),
            'parser_alignment': v1_keys == v2_keys,
            'genuine_source_capture_proven': False,
            'model_or_delivery_comparable': False,
            'production_change': False, 'discord_sent': False}
