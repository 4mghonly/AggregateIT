"""Bounded, no-send proof that externally viewed web excerpts reach B3/B4 safely.

Not a collector. It accepts manually transferred short, literal web excerpts with
explicit provenance. It does not verify the public page's bytes, publisher
independence, article completeness, copyright reuse, or factual truth.
"""
from __future__ import annotations

from datetime import date, datetime
from urllib.parse import urlsplit

from v2_evidence import _time, make_article, make_excerpt, make_claim, make_event
from v2_evidence_ledger import EvidenceLedger
from v2_editorial import AR_TOPICS, EN_TOPICS, _validated_annotation, plan_edition
from v2_product_compiler import compile_daily
from v2_feed_probe import _url_safe

_MAX_CAPTURE_ITEMS = 20
_CAPTURE_FIELDS = frozenset({
    'source_id', 'article_url', 'verbatim_excerpt', 'original_language',
    'published_date', 'capture_method', 'explicit_event_key', 'region',
    'subject_country', 'topic', 'priority',
})


def _host_matches_registry(item: dict, by_id: dict) -> None:
    _url_safe(item['article_url'])
    # The configured source identity is a candidate, not independently verified
    # company ownership or a license to republish a source's article.
    observed_host = urlsplit(item['article_url']).hostname.lower().rstrip('.')
    expected_host = by_id[item['source_id']].get('host_candidate')
    if not isinstance(expected_host, str) or not expected_host:
        raise ValueError('source_host_not_in_registry')
    expected_host = expected_host.lower().rstrip('.')
    if observed_host != expected_host and not observed_host.endswith('.' + expected_host):
        raise ValueError('publisher_host_mismatch')


def compile_web_captures(captures: list[dict], *, registry: dict,
                         observed_at: str, slot_id: str) -> dict:
    """Intake of *partial* externally observed text only; never live delivery.

    A capture proves only that specified text was supplied by the external web
    observation. No automated publisher retrieval and no attribution beyond
    registry-host alignment is inferred. Editorial event keys are explicit.
    """
    observed_at = _time(observed_at)
    slot_id = _time(slot_id)
    now = datetime.fromisoformat(observed_at)
    if (not isinstance(registry, dict) or
            registry.get('schema_version') != '2.0.0-preview' or
            not isinstance(registry.get('sources'), list)):
        raise ValueError('pinned_registry_required')
    if not isinstance(captures, list) or not 1 <= len(captures) <= _MAX_CAPTURE_ITEMS:
        raise ValueError('capture_count_out_of_range')
    by_id = {row['id']: row for row in registry['sources']}
    ledger = EvidenceLedger(max_observations=40)
    grouped: dict[str, list[dict]] = {}
    annotations: dict[str, dict] = {}
    receipts = []
    for raw in captures:
        if not isinstance(raw, dict) or set(raw) != _CAPTURE_FIELDS:
            raise ValueError('invalid_capture_shape')
        if raw['source_id'] not in by_id:
            raise ValueError('unregistered_source')
        _host_matches_registry(raw, by_id)
        if raw['capture_method'] != 'public_web_page_read_manual_transfer':
            raise ValueError('unapproved_capture_provenance')
        text = raw['verbatim_excerpt']
        if (not isinstance(text, str) or not text.strip() or
                len(text) > 240 or len(text.split()) > 25 or len(text.strip()) < 10):
            raise ValueError('unsupported_quote_size')
        language = raw['original_language']
        product = 'english' if language == 'en' else 'arabic' if language == 'ar' else None
        if product is None or by_id[raw['source_id']].get('stream') != product:
            raise ValueError('mismatched_registered_stream_or_language')
        if raw['topic'] not in (EN_TOPICS if product == 'english' else AR_TOPICS):
            raise ValueError('excluded_product_topic')
        if not isinstance(raw['published_date'], str):
            raise ValueError('published_day_required')
        try:
            pub_day = date.fromisoformat(raw['published_date'])
        except ValueError as exc:
            raise ValueError('published_day_required') from exc
        # Source only gave calendar-day precision. Do not invent a clock time;
        # reject very old or future dated observations before article admission.
        age_days = (now.date() - pub_day).days
        if age_days < 0 or age_days > 2:
            raise ValueError('stale_or_future_publication_day')
        source = make_article(
            source_id=raw['source_id'], url=raw['article_url'],
            original_text=text, original_language=language,
            retrieved_at=observed_at, published_at=None,
        )
        excerpt = make_excerpt(source, 0, len(text))
        claim = make_claim(statement=text, excerpts=[excerpt])
        ledger.observe(source)
        ledger.attach_excerpt(excerpt)
        ledger.attach_claim(claim)
        key = raw['explicit_event_key']
        grouped.setdefault(key, []).append(claim)
        common = {k:raw[k] for k in ('region','subject_country','priority')}
        if key in annotations:
            if {k:annotations[key][k] for k in common} != common:
                raise ValueError('conflicting_event_annotation')
        else:
            annotations[key] = {**common, 'topics': {}}
        if product in annotations[key]['topics']:
            raise ValueError('duplicate_language_event_annotation')
        annotations[key]['topics'][product] = raw['topic']
        receipts.append({
            'source_id':raw['source_id'], 'article_url':source['canonical_url'],
            'article_id':source['article_id'], 'revision_id':source['revision_id'],
            'excerpt_id':excerpt['excerpt_id'], 'text_sha256':source['text_sha256'],
            'capture_method':raw['capture_method'], 'published_date':raw['published_date'],
            'published_at':None, 'capture_time':observed_at,
            'partial_source_text':True,
        })
    for key, claims in grouped.items():
        ledger.upsert_event(make_event(key=key, claims=claims))
    editions = {}
    for product in ('english','arabic'):
        selected = []
        for key, claims in grouped.items():
            topic = annotations[key]['topics'].get(product)
            if topic is None:
                continue
            ann = annotations[key]
            selected.append(_validated_annotation({
                'event_id':make_event(key=key, claims=claims)['event_id'],
                'region':ann['region'], 'subject_country':ann['subject_country'],
                'topic':topic, 'priority':ann['priority'],
            }, product))
        plan = plan_edition(ledger=ledger,annotations=selected,product=product,
                            slot_id=slot_id,as_of=observed_at)
        edition = compile_daily(editorial_plan=plan)
        # The compiler always withholds delivery. This supplemental metadata
        # makes the incompleteness visible to downstream preview code.
        edition['source_capture_quality'] = 'partial_external_web_text_unconfirmed'
        editions[product] = edition
    return {
        'schema':'aggregateit-v2-external-capture-rehearsal/1',
        'capture_count':len(receipts), 'capture_receipts':receipts,
        'evidence_counters':ledger.counters(), 'products':editions,
        'source_provenance_status':'web_text_excerpt_observed_not_independently_verified',
        'web_collector_ran':False, 'llm_called':False, 'discord_sent':False,
        'delivery_authorized':False,
    }
