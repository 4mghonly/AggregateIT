"""AggregateIT V2 integrated *offline synthetic* no-post rehearsal.

A single bounded entry point exercises registered source IDs -> exact excerpts ->
B3 journal/replay -> B4 independent editors -> B5 layout -> B6 telemetry,
budget and unsent delivery reservations. No network, file, API or Discord I/O.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import io
import json
from urllib.parse import urlsplit

from v2_evidence import make_article, make_excerpt, make_claim, make_event, _time
from v2_evidence_journal import EvidenceJournal
from v2_editorial import plan_edition
from v2_layout import layout_plan
from v2_analytics_controls import validate_telemetry, budget_decision
from v2_delivery_gate import ReceiptGate, DESTINATION_KEYS

_ALLOWED_DOCUMENT_FIELDS = {
    "source_id", "url", "original_text", "original_language",
    "retrieved_at", "published_at", "excerpt_start", "excerpt_end",
    "claim_statement", "explicit_event_key", "region", "subject_country",
    "topic_english", "topic_arabic", "priority",
}


def _synthetic_url(url: str) -> bool:
    if not isinstance(url, str):
        return False
    host = urlsplit(url).hostname
    return bool(host and (
        host in {"example.org", "example.com", "example.net"}
        or host.endswith((".example", ".test", ".invalid"))
    ))


def _fixture_check(fixture: dict, registered: set[str]) -> None:
    if not isinstance(fixture, dict) or set(fixture) != {
        "schema", "synthetic", "as_of", "slot_id", "documents"
    } or fixture["schema"] != "aggregateit-v2-offline-rehearsal/1" or fixture["synthetic"] is not True:
        raise ValueError("rehearsal_requires_explicit_synthetic_contract")
    _time(fixture["as_of"])
    _time(fixture["slot_id"])
    docs = fixture["documents"]
    if not isinstance(docs, list) or not 1 <= len(docs) <= 40:
        raise ValueError("rehearsal_document_ceiling")
    for item in docs:
        if not isinstance(item, dict) or set(item) != _ALLOWED_DOCUMENT_FIELDS:
            raise ValueError("unapproved_document_fields")
        if item["source_id"] not in registered:
            raise ValueError("fixture_source_not_in_versioned_registry")
        if not _synthetic_url(item["url"]):
            raise ValueError("rehearsal_prohibits_real_article_urls")
        text = item["original_text"]
        if not isinstance(text, str) or not 4 <= len(text) <= 5_000:
            raise ValueError("invalid_fixture_text_budget")
        if type(item["excerpt_start"]) is not int or type(item["excerpt_end"]) is not int:
            raise ValueError("invalid_fixture_excerpt_offsets")
        if not 0 <= item["excerpt_start"] < item["excerpt_end"] <= len(text):
            raise ValueError("invalid_fixture_excerpt_offsets")
        if not isinstance(item["claim_statement"], str) or not item["claim_statement"].strip():
            raise ValueError("missing_fixture_claim")
        if item["topic_english"] is not None and not isinstance(item["topic_english"], str):
            raise ValueError("invalid_english_topic")
        if item["topic_arabic"] is not None and not isinstance(item["topic_arabic"], str):
            raise ValueError("invalid_arabic_topic")


def run_offline_rehearsal(fixture: dict, registry: dict) -> dict:
    if not isinstance(registry, dict) or registry.get("schema_version") != "2.0.0-preview":
        raise ValueError("versioned_registry_required")
    rows = registry.get("sources")
    if not isinstance(rows, list) or len(rows) < 2:
        raise ValueError("invalid_registry")
    registered = {row["id"] for row in rows}
    _fixture_check(fixture, registered)

    journal = EvidenceJournal(max_observations=80)
    out = io.StringIO()
    claims_by_key: dict[str, list[dict]] = defaultdict(list)
    annotations: dict[str, dict] = {}

    # Explicit event keys and annotation fields come solely from the synthetic
    # fixture. No language/headline/host-based event clustering is inferred.
    for item in fixture["documents"]:
        article = make_article(
            source_id=item["source_id"], url=item["url"],
            original_text=item["original_text"],
            original_language=item["original_language"],
            retrieved_at=item["retrieved_at"], published_at=item["published_at"],
        )
        excerpt = make_excerpt(article, item["excerpt_start"], item["excerpt_end"])
        claim = make_claim(statement=item["claim_statement"], excerpts=[excerpt])
        journal.append(out, "observe", article, durable=False)
        journal.append(out, "excerpt", excerpt, durable=False)
        journal.append(out, "claim", claim, durable=False)
        key = item["explicit_event_key"]
        claims_by_key[key].append(claim)
        metadata = {k: item[k] for k in (
            "region", "subject_country", "topic_english", "topic_arabic", "priority"
        )}
        if key in annotations and annotations[key] != metadata:
            raise ValueError("conflicting_explicit_event_annotations")
        annotations[key] = metadata

    for key in sorted(claims_by_key):
        event = make_event(key=key, claims=claims_by_key[key])
        journal.append(out, "event", event, durable=False)

    recovered = EvidenceJournal.replay(out.getvalue(), expected_head=journal.head,
                                       max_observations=80)
    if recovered.receipt() != journal.receipt():
        raise ValueError("replay_receipt_mismatch")
    ledger = recovered.ledger
    editions = {}
    delivery = ReceiptGate(max_slots=2)
    for product in ("english", "arabic"):
        anns = []
        for key in sorted(claims_by_key):
            topic = annotations[key]["topic_"+product]
            if topic is not None:
                metadata = annotations[key]
                anns.append({
                    "event_id": make_event(key=key, claims=claims_by_key[key])["event_id"],
                    "region": metadata["region"],
                    "subject_country": metadata["subject_country"],
                    "topic": topic, "priority": metadata["priority"],
                })
        plan = plan_edition(ledger=ledger, annotations=anns, product=product,
                            slot_id=fixture["slot_id"], as_of=fixture["as_of"])
        layout = layout_plan(plan, ledger)
        payload = json.dumps(layout, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        destination_key = DESTINATION_KEYS[product]
        delivery.reserve(product=product, slot_id=fixture["slot_id"],
                         destination_key=destination_key, edition_digest=digest)
        telemetry = validate_telemetry({
            "idempotency_key": "synthetic:"+product+":edition",
            "kind": "edition", "product": product, "at": fixture["as_of"],
            "status": "withheld", "units": layout["rendered_items"],
        })
        editions[product] = {
            "plan": plan, "layout": layout,
            "reservation": delivery.snapshot(product=product,slot_id=fixture["slot_id"]),
            "telemetry": telemetry,
            "network_send_attempted": False,
        }

    budget = budget_decision(db_size_bytes=None, account_writes_today=None,
                             account_reads_today=None, proposed_writes=2,
                             proposed_reads=10)
    return {
        "schema": "aggregateit-v2-rehearsal-result/1",
        "synthetic": True, "offline_only": True,
        "journal": journal.receipt(), "replayed_journal": recovered.receipt(),
        "registry_id_count": len(registered),
        "products": editions, "analytics_budget": budget,
        "real_publisher_rights": "unreviewed",
        "real_publisher_independence": "unverified",
        "live_model_called": False, "live_source_fetched": False,
        "database_written": False, "discord_sent": False,
    }
