"""B18 private bilingual brief from source-linked excerpts; never sends."""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256

AR_TOPICS = frozenset({'geopolitics', 'military', 'security', 'diplomacy',
                       'humanitarian_conflict', 'political_stability', 'sanctions',
                       'strategic_infrastructure'})
EN_TOPICS = AR_TOPICS | frozenset({'markets', 'finance', 'macro', 'energy', 'trade', 'policy', 'cyber'})


def _slot(value):
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (AttributeError, ValueError) as exc:
        raise ValueError('invalid_slot') from exc
    if parsed.utcoffset() is None:
        raise ValueError('naive_slot')
    return parsed.isoformat()


def make_private_digest(*, product: str, slot_id: str, stories: list[dict],
                        missing_regions: list[str] | None = None) -> dict:
    if product not in ('english', 'arabic') or not isinstance(stories, list) or len(stories) > 30:
        raise ValueError('invalid_digest')
    if not isinstance(missing_regions or [], list) or any(not isinstance(x, str) for x in (missing_regions or [])):
        raise ValueError('invalid_coverage_gaps')
    rows = []
    seen = set()
    required_lang = 'en' if product == 'english' else 'ar'
    topics = EN_TOPICS if product == 'english' else AR_TOPICS
    for story in stories:
        if not isinstance(story, dict) or story.get('original_language') != required_lang:
            raise ValueError('unverified_native_language')
        if story.get('topic') not in topics:
            raise ValueError('topic_not_allowed_for_product')
        fields = ('candidate_id', 'excerpt_id', 'source_id', 'article_url', 'title', 'quote', 'region')
        if any(not isinstance(story.get(f), str) or not story[f].strip() for f in fields):
            raise ValueError('missing_evidence_fields')
        if story['candidate_id'] in seen:
            raise ValueError('duplicate_story')
        seen.add(story['candidate_id'])
        if len(story['title']) > 300 or len(story['quote']) > 900:
            raise ValueError('story_exceeds_review_budget')
        rows.append({key: story[key] for key in (*fields, 'topic', 'original_language')})
    return {'schema': 'aggregateit-v2-b18-private-digest/1', 'product': product,
            'slot_id': _slot(slot_id), 'stories': rows, 'missing_regions': list(missing_regions or []),
            'truth_verified': False, 'model_analysis': 'not_performed',
            'private_only': True, 'delivery_authorized': False, 'discord_sent': False}


def digest_fingerprint(digest: dict) -> str:
    if digest.get('schema') != 'aggregateit-v2-b18-private-digest/1':
        raise ValueError('untrusted_digest')
    from json import dumps
    return sha256(dumps(digest, sort_keys=True, ensure_ascii=False,
                        separators=(',', ':')).encode('utf8')).hexdigest()
