"""B4 isolated, evidence-gated edition planning. Does not generate prose or publish.

One immutable event/evidence graph feeds distinct English and Arabic selection
policies. Source quotations are displayed verbatim; translation or analytical
claims are NEVER silently promoted from model candidates to facts.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone

from v2_evidence import _time

AR_REGIONS = frozenset({
    "gcc", "oman", "iran", "turkey", "iraq", "yemen", "egypt",
    "sudan", "sahel", "north_africa", "pakistan", "afghanistan",
    "horn", "somalia", "levant", "palestine_israel", "jordan",
})
AR_TOPICS = frozenset({
    "diplomacy", "military", "security", "political_stability",
    "humanitarian_conflict", "sanctions", "strategic_infrastructure",
})
EN_TOPICS = frozenset({
    "markets", "finance", "geopolitics", "security", "energy",
    "trade", "cyber", "policy", "macro",
})
PAGE_COUNTS = {"english": 2, "arabic": 3}
LANGUAGES = {"english": "en", "arabic": "ar"}


def _date(value: str) -> datetime:
    return datetime.fromisoformat(_time(value)).astimezone(timezone.utc)


def _validated_annotation(item: dict, product: str) -> dict:
    if not isinstance(item, dict) or set(item) != {
        "event_id", "region", "subject_country", "topic", "priority"
    }:
        raise ValueError("invalid_editorial_annotation")
    if not isinstance(item["event_id"], str) or not item["event_id"].startswith("evt_"):
        raise ValueError("invalid_event_id")
    if item["region"] not in AR_REGIONS:
        raise ValueError("invalid_region")
    country = item["subject_country"]
    if not isinstance(country, str) or len(country) != 2 or not country.isalpha() or not country.isupper():
        raise ValueError("invalid_subject_country")
    if type(item["priority"]) is not int or not 0 <= item["priority"] <= 100:
        raise ValueError("invalid_priority")
    if item["topic"] not in (AR_TOPICS if product == "arabic" else EN_TOPICS):
        raise ValueError("topic_excluded_by_product")
    return item


def _native_excerpt(ledger, event: dict, language: str, now: datetime,
                    max_age_hours: int) -> tuple[dict | None, str]:
    """Returns a *verbatim* usable source span or a specific abstention reason."""
    candidates = []
    reason = "no_native_language_source"
    for claim_id in event["claim_ids"]:
        claim = ledger._claims[claim_id]
        if claim["kind"] != "publisher_assertion":
            continue
        for excerpt_id in claim["excerpt_ids"]:
            excerpt = ledger._excerpts[excerpt_id]
            if excerpt["original_language"].split("-")[0] != language:
                continue
            source = ledger._source_revisions[(excerpt["source_id"], excerpt["revision_id"])]
            dated_at = source["published_at"] or source["retrieved_at"]
            age = (now - _date(dated_at)).total_seconds()
            if age < -300 or age > max_age_hours * 3600:
                reason = "stale_or_future_source"
                continue
            literal = excerpt["literal"]
            if len(literal) > 240 or len(literal.strip()) < 4:
                reason = "quote_exceeds_safe_text_budget"
                continue
            candidates.append({
                "quote": literal, "literal_sha256": excerpt["literal_sha256"],
                "excerpt_id": excerpt_id, "claim_id": claim_id,
                "source_id": excerpt["source_id"],
                "article_id": excerpt["article_id"], "revision_id": excerpt["revision_id"],
                "source_url": source["canonical_url"],
                "original_language": excerpt["original_language"],
                "source_date": dated_at,
            })
    if not candidates:
        return None, reason
    # Source date primary; stable IDs resolve ties. No pseudo-independent count.
    candidates.sort(key=lambda c: (_date(c["source_date"]), c["excerpt_id"]), reverse=True)
    return candidates[0], "accepted"


def plan_edition(*, ledger, annotations: list[dict], product: str,
                 slot_id: str, as_of: str, previous_versions: dict | None = None,
                 max_age_hours: int = 48, max_items: int = 15) -> dict:
    if product not in PAGE_COUNTS:
        raise ValueError("unknown_product")
    now = _date(as_of)
    _date(slot_id)
    if not isinstance(annotations, list) or len(annotations) > 2000:
        raise ValueError("invalid_annotation_batch")
    if type(max_age_hours) is not int or not 1 <= max_age_hours <= 168:
        raise ValueError("invalid_freshness_window")
    if type(max_items) is not int or not 1 <= max_items <= 30:
        raise ValueError("invalid_item_budget")
    if previous_versions is not None and not isinstance(previous_versions, dict):
        raise ValueError("invalid_previous_versions")
    seen, accepted, held = set(), [], Counter()
    for untrusted in annotations:
        try:
            ann = _validated_annotation(untrusted, product)
        except (ValueError, TypeError) as exc:
            held[str(exc)] += 1
            continue
        event_id = ann["event_id"]
        if event_id in seen:
            held["duplicate_event_annotation"] += 1
            continue
        seen.add(event_id)
        history = ledger._events.get(event_id)
        if not history:
            held["event_not_in_evidence_ledger"] += 1
            continue
        event = history[-1]
        source, reason = _native_excerpt(ledger, event, LANGUAGES[product],
                                         now, max_age_hours)
        if source is None:
            held[reason] += 1
            continue
        previous = (previous_versions or {}).get(event_id)
        delta = "unknown_no_baseline" if previous_versions is None else (
            "new" if previous is None else (
                "unchanged" if previous == event["version_id"] else "updated"
            )
        )
        accepted.append({
            "event_id": event_id, "version_id": event["version_id"],
            "status": event["status"], "region": ann["region"],
            "subject_country": ann["subject_country"], "topic": ann["topic"],
            "priority": ann["priority"],
            "is_uae": ann["subject_country"] == "AE",
            "change": delta, "evidence": source,
            "reporting_status": "publisher_attributed_not_independently_verified",
            "publisher_independence": "unverified",
            "analysis_status": "abstained_unverified",
            "translation_status": "not_required_original_quote",
        })
    accepted.sort(key=lambda x: (-x["priority"], x["event_id"]))
    chosen = []
    if product == "arabic":
        # The UAE panel is deliberate; never classify country via publisher host.
        uae = [x for x in accepted if x["is_uae"]]
        chosen.extend(uae[:min(4, max_items)])
        remaining = [x for x in accepted if x not in chosen]
        # Geography-first coverage: one per other represented region, then fill.
        regions_seen = set()
        for x in remaining:
            if len(chosen) >= max_items:
                break
            if x["region"] not in regions_seen:
                chosen.append(x)
                regions_seen.add(x["region"])
        for x in remaining:
            if len(chosen) >= max_items:
                break
            if x not in chosen:
                chosen.append(x)
    else:
        chosen = accepted[:max_items]
    held["eligible_over_page_budget"] += len(accepted) - len(chosen)
    represented = sorted({x["region"] for x in chosen})
    return {
        "schema": "aggregateit-editorial-plan/1",
        "synthetic_or_unverified": True,
        "product": product, "slot_id": slot_id, "as_of": as_of,
        "page_count": PAGE_COUNTS[product],
        "items": chosen, "selected": len(chosen),
        "eligible": len(accepted),
        "held_reasons": dict(sorted((k, v) for k, v in held.items() if v)),
        "represented_regions": represented,
        "missing_target_regions": sorted(AR_REGIONS.difference(represented)) if product == "arabic" else [],
        "language": LANGUAGES[product],
        "coverage_status": "unverified_source_registry",
        "analysis_status": "withheld_without_verified_analysis",
        "delivery_authorized": False,
    }
