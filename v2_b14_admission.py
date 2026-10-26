"""B14 deterministic candidate admission for private, non-sending reviews.

The admission proves internal evidence linkage, never claim accuracy or live
source availability. Rights clearance is not a gate in this V2 workstream.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from urllib.parse import urlsplit


def _stamp(value: str) -> datetime:
    try:
        stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (TypeError, AttributeError, ValueError) as exc:
        raise ValueError('invalid_evidence_timestamp') from exc
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError('timezone_required')
    return stamp


def admit_candidates(candidates: dict, captures: list[dict], *, max_age_hours: int = 72) -> dict:
    if candidates.get('schema') != 'aggregateit-v2-feed-candidates/1' or candidates.get('can_publish') is not False:
        raise ValueError('untrusted_candidate_roster')
    if not isinstance(captures, list) or type(max_age_hours) is not int or not 1 <= max_age_hours <= 168:
        raise ValueError('invalid_admission_input')
    by_url = {}
    for capture in captures:
        if not isinstance(capture, dict) or not isinstance(capture.get('article_url'), str):
            raise ValueError('invalid_capture')
        if capture['article_url'] in by_url:
            raise ValueError('duplicate_capture')
        by_url[capture['article_url']] = capture
    rows = []
    rejected = []
    seen = set()
    for candidate in candidates.get('items', []):
        if not isinstance(candidate, dict) or candidate.get('article_url') in seen:
            raise ValueError('duplicate_or_invalid_candidate')
        url = candidate.get('article_url')
        seen.add(url)
        capture = by_url.get(url)
        reason = None
        if not isinstance(url, str) or urlsplit(url).scheme != 'https':
            reason = 'invalid_candidate_url'
        elif not capture:
            reason = 'article_evidence_missing'
        elif capture.get('source_feed_url') != candidate.get('source_feed_url'):
            reason = 'source_mismatch'
        elif capture.get('title') != candidate.get('title'):
            reason = 'title_mismatch'
        elif (type(capture.get('verified_claims')) is not int or capture['verified_claims'] < 1
              or not isinstance(capture.get('excerpt_id'), str) or not capture['excerpt_id']):
            reason = 'source_claim_evidence_missing'
        elif capture.get('original_language') not in ('ar', 'en'):
            reason = 'language_unverified'
        else:
            observed = _stamp(candidate.get('observed_at'))
            published = _stamp(candidate.get('published_at'))
            captured = _stamp(capture.get('captured_at'))
            if not 0 <= (captured - published).total_seconds() <= max_age_hours * 3600 or captured < observed:
                reason = 'stale_or_out_of_order_evidence'
        if reason:
            rejected.append({'candidate_id': candidate.get('candidate_id'), 'reason': reason})
            continue
        rows.append({'candidate_id': candidate['candidate_id'], 'article_url': url,
                     'source_feed_url': candidate['source_feed_url'],
                     'excerpt_id': capture['excerpt_id'],
                     'original_language': capture['original_language'],
                     'evidence_digest': sha256((url + '\n' + capture['excerpt_id']).encode()).hexdigest(),
                     'admission': 'private_evidence_review_only'})
    return {'schema': 'aggregateit-v2-b14-admission/1', 'admitted': rows,
            'rejected': rejected, 'live_accuracy_verified': False,
            'can_publish': False, 'discord_sent': False}
