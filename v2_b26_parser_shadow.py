"""B26 exact-input RSS/Atom shadow: stdlib candidate output vs feedparser.

No source fetch, model call or destination mutation. Captures digest and drift,
but synthetic input is not presented as genuine production parity evidence.
"""
from __future__ import annotations

from hashlib import sha256
from html import unescape
import re

from v2_feed_items import extract_candidates
from v2_feed_probe import _date


def _normalized(title, link, published):
    date = _date(published)
    if date is None:
        return None
    return (re.sub(r'\s+', ' ', unescape(title)).strip(), link, date.isoformat())


def compare_parser_outputs(feed_bytes: bytes, *, feed_url: str, observed_at: str,
                           input_provenance: str = 'synthetic', max_items: int = 30) -> dict:
    if input_provenance not in ('synthetic', 'authenticated_capture'):
        raise ValueError('invalid_parser_provenance')
    if not isinstance(feed_bytes, bytes):
        raise ValueError('invalid_feed_bytes')
    if type(max_items) is not int or not 1 <= max_items <= 50:
        raise ValueError('invalid_parser_budget')
    std = extract_candidates(feed_bytes, feed_url=feed_url, observed_at=observed_at,
                             max_items=max_items)
    try:
        import feedparser
    except ImportError as exc:
        raise RuntimeError('feedparser_dependency_missing') from exc
    other = feedparser.parse(feed_bytes)
    now = _date(observed_at)
    if now is None:
        raise ValueError('invalid_observation_time')
    third_party = set()
    excluded = 0
    for entry in other.entries:
        stamp = entry.get('published') or entry.get('updated')
        normalized = _normalized(entry.get('title', ''), entry.get('link', ''), stamp)
        if normalized is None or not 5 <= len(normalized[0]) <= 300 or not normalized[1].startswith('https://'):
            excluded += 1
            continue
        dt = _date(normalized[2])
        if not -300 <= (now - dt).total_seconds() <= 72 * 3600:
            excluded += 1
            continue
        if len(third_party) < max_items:
            third_party.add(normalized)
    first_party = set((r['title'], r['article_url'], r['published_at']) for r in std['items'])
    missing = sorted(first_party - third_party)
    extra = sorted(third_party - first_party)
    return {'schema': 'aggregateit-v2-b26-parser-shadow/1',
            'source_sha256': sha256(feed_bytes).hexdigest(),
            'input_provenance': input_provenance, 'same_input_verified': True,
            'stdlib_count': len(first_party), 'feedparser_count': len(third_party),
            'feedparser_excluded': excluded, 'missing_from_feedparser': missing,
            'extra_in_feedparser': extra, 'parity_passed': not missing and not extra,
            'live_parser_parity_proven': input_provenance == 'authenticated_capture' and not missing and not extra,
            'delivery_authorized': False}
