"""B3 append-only in-memory provenance graph. No database, network, or publication.

All commands require records created through v2_evidence, then revalidate them
against retained source bytes and existing graph nodes. This is a prototype, not
a durable or publisher-authenticated ledger.
"""
from __future__ import annotations

from copy import deepcopy
from collections import defaultdict

from v2_evidence import (
    _verify_article_record, make_excerpt, make_claim, make_event, event_delta,
)


class EvidenceLedger:
    def __init__(self, *, max_observations: int = 20_000):
        if not 1 <= max_observations <= 20_000:
            raise ValueError("invalid_observation_limit")
        self.max_observations = max_observations
        self._observations: dict[str, dict] = {}
        self._source_revisions: dict[tuple[str, str], dict] = {}
        self._excerpts: dict[str, dict] = {}
        self._claims: dict[str, dict] = {}
        self._events: dict[str, list[dict]] = {}
        self._relations: dict[tuple[str, str, str, str], dict] = {}

    @staticmethod
    def _same_or_add(mapping: dict, key, record: dict) -> bool:
        if key in mapping:
            if mapping[key] != record:
                raise ValueError("identity_conflict")
            return False
        mapping[key] = deepcopy(record)
        return True

    def observe(self, article: dict) -> bool:
        _verify_article_record(article)
        obs_id = article["observation_id"]
        if obs_id not in self._observations and len(self._observations) >= self.max_observations:
            raise ValueError("observation_ceiling")
        key = (article["source_id"], article["revision_id"])
        # Existing revision with equal source but a different retrieval timestamp is fine.
        if key in self._source_revisions:
            old = self._source_revisions[key]
            if (
                old["article_id"] != article["article_id"]
                or old["original_text"] != article["original_text"]
                or old["canonical_url"] != article["canonical_url"]
            ):
                raise ValueError("revision_identity_conflict")
        added = self._same_or_add(self._observations, obs_id, article)
        self._source_revisions.setdefault(key, deepcopy(article))
        return added

    def attach_excerpt(self, excerpt: dict) -> bool:
        key = (excerpt.get("source_id"), excerpt.get("revision_id"))
        source = self._source_revisions.get(key)
        if source is None:
            raise ValueError("excerpt_without_stored_revision")
        try:
            expected = make_excerpt(source, excerpt["start_cp"], excerpt["end_cp"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("invalid_excerpt") from None
        if excerpt != expected:
            raise ValueError("excerpt_does_not_match_stored_source")
        return self._same_or_add(self._excerpts, excerpt["excerpt_id"], excerpt)

    def attach_claim(self, claim: dict) -> bool:
        if not isinstance(claim, dict) or not claim.get("excerpt_ids"):
            raise ValueError("claim_without_evidence")
        try:
            excerpts = [self._excerpts[eid] for eid in claim["excerpt_ids"]]
        except (KeyError, TypeError):
            raise ValueError("claim_references_missing_excerpt") from None
        try:
            expected = make_claim(statement=claim["statement"], excerpts=excerpts, kind=claim["kind"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("invalid_claim") from None
        if claim != expected:
            raise ValueError("claim_integrity_or_revision_mismatch")
        return self._same_or_add(self._claims, claim["claim_id"], claim)

    def upsert_event(self, event: dict) -> str:
        if not isinstance(event, dict) or not event.get("claim_ids"):
            raise ValueError("event_without_claims")
        try:
            claims = [self._claims[cid] for cid in event["claim_ids"]]
        except (KeyError, TypeError):
            raise ValueError("event_references_missing_claim") from None
        try:
            expected = make_event(
                key=event["explicit_key"], claims=claims, status=event["status"],
                closure_claim_id=event["closure_claim_id"],
            )
        except (KeyError, TypeError, ValueError):
            raise ValueError("invalid_event") from None
        if event != expected:
            raise ValueError("event_integrity_mismatch")
        history = self._events.setdefault(event["event_id"], [])
        latest = history[-1] if history else None
        delta = event_delta(latest, event)
        if delta != "unchanged":
            history.append(deepcopy(event))
        return delta

    def relate(self, *, event_id: str, kind: str, first_claim_id: str,
               second_claim_id: str, rationale: str) -> bool:
        """Explicit analyst-supplied correction/contradiction, not text similarity."""
        if kind not in {"correction", "contradiction"}:
            raise ValueError("invalid_relation_kind")
        if first_claim_id == second_claim_id or first_claim_id not in self._claims or second_claim_id not in self._claims:
            raise ValueError("relation_requires_two_known_claims")
        history = self._events.get(event_id, [])
        linked = set().union(*(set(v["claim_ids"]) for v in history)) if history else set()
        if first_claim_id not in linked or second_claim_id not in linked:
            raise ValueError("relation_claims_not_in_event")
        if not isinstance(rationale, str) or not rationale.strip() or len(rationale) > 2000:
            raise ValueError("relation_requires_rationale")
        key = (event_id, kind, first_claim_id, second_claim_id)
        return self._same_or_add(self._relations, key, {
            "event_id": event_id, "kind": kind, "first_claim_id": first_claim_id,
            "second_claim_id": second_claim_id, "rationale": rationale.strip(),
            "review_status": "explicit_but_unverified",
        })

    def counters(self) -> dict:
        """Summary only. Never leaks URLs, original text, excerpts or reasoning text."""
        by_article = defaultdict(set)
        for obs in self._observations.values():
            by_article[obs["article_id"]].add(obs["source_id"])
        return {
            "observations": len(self._observations),
            "unique_articles": len(by_article),
            "duplicate_article_observations": len(self._observations) - len(by_article),
            "excerpts": len(self._excerpts),
            "claims": len(self._claims),
            "events": len(self._events),
            "event_versions": sum(len(v) for v in self._events.values()),
            "explicit_relations": len(self._relations),
            "publisher_independence": "not_verified",
        }
