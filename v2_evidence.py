"""V2 B3 evidence-core prototype: source-bound, deterministic, entirely in memory.

The module does not fetch articles, call models, persist raw text or publish.
Text spans count Unicode code points (Python str indices), never byte or UTF-16 offsets.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SOURCE_ID = re.compile(r"^(?:en-\d{3}|ar-s\d{3})$")
EVENT_KEY = re.compile(r"^[a-z0-9][a-z0-9._:-]{3,99}$")
LANGUAGE = re.compile(r"^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$|^und$")
TRACKERS = frozenset({"fbclid", "gclid", "mc_cid", "mc_eid", "igshid"})


def _sha(*parts: str) -> str:
    h = hashlib.sha256()
    for part in parts:
        encoded = part.encode("utf-8")
        h.update(len(encoded).to_bytes(8, "big"))
        h.update(encoded)
    return h.hexdigest()[:24]


def canonical_article_url(url: str) -> str:
    """Trim known tracking query keys. Never erase source-significant query keys."""
    if not isinstance(url, str) or len(url) > 4096:
        raise ValueError("invalid_url")
    try:
        parsed = urlsplit(url.strip())
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        raise ValueError("invalid_url") from None
    if parsed.scheme.lower() not in {"https", "http"} or not hostname or parsed.username or parsed.password:
        raise ValueError("invalid_url")
    if hostname in {"localhost"} or hostname.endswith(".local"):
        raise ValueError("non_public_url")
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("invalid_port")
    hostname = hostname.lower()
    if ":" in hostname:
        hostname = f"[{hostname}]"
    default_port = (parsed.scheme.lower() == "https" and port == 443) or (
        parsed.scheme.lower() == "http" and port == 80
    )
    netloc = hostname + (f":{port}" if port and not default_port else "")
    query = [
        (key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKERS
    ]
    return urlunsplit((
        parsed.scheme.lower(), netloc,
        parsed.path.rstrip("/") or "/",
        urlencode(query, doseq=True), ""
    ))


def _time(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("timestamp_must_be_iso8601_offset_aware")
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("timestamp_must_be_iso8601_offset_aware") from None
    if t.tzinfo is None or t.utcoffset() is None:
        raise ValueError("timestamp_must_be_iso8601_offset_aware")
    return t.isoformat()


def make_article(*, source_id: str, url: str, original_text: str,
                 original_language: str, retrieved_at: str,
                 published_at: str | None = None) -> dict:
    if not SOURCE_ID.fullmatch(source_id):
        raise ValueError("unregistered_source_identity_format")
    if not isinstance(original_text, str) or not original_text.strip() or len(original_text) > 250_000:
        raise ValueError("invalid_original_text")
    if not isinstance(original_language, str) or not LANGUAGE.fullmatch(original_language):
        raise ValueError("invalid_language_tag")
    canonical = canonical_article_url(url)
    retrieved = _time(retrieved_at)
    published = _time(published_at) if published_at else None
    # One URL can be seen through both product collectors; the observations remain separate.
    article_id = "art_" + _sha(canonical)
    revision_id = "rev_" + _sha(canonical, original_text)
    observation_id = "obs_" + _sha(article_id, revision_id, source_id, retrieved)
    return {
        "article_id": article_id, "revision_id": revision_id,
        "observation_id": observation_id, "source_id": source_id,
        "canonical_url": canonical, "original_language": original_language,
        "original_text": original_text, "text_sha256": hashlib.sha256(original_text.encode("utf-8")).hexdigest(),
        "published_at": published, "retrieved_at": retrieved,
    }


def _verify_article_record(article: dict) -> None:
    try:
        canonical = canonical_article_url(article["canonical_url"])
        original = article["original_text"]
        ok = (
            canonical == article["canonical_url"]
            and article["article_id"] == "art_" + _sha(canonical)
            and article["revision_id"] == "rev_" + _sha(canonical, original)
            and article["text_sha256"] == hashlib.sha256(original.encode("utf-8")).hexdigest()
            and SOURCE_ID.fullmatch(article["source_id"]) is not None
            and article["observation_id"] == "obs_" + _sha(
                article["article_id"], article["revision_id"], article["source_id"], article["retrieved_at"]
            )
            and _time(article["retrieved_at"]) == article["retrieved_at"]
            and (article["published_at"] is None or _time(article["published_at"]) == article["published_at"])
            and LANGUAGE.fullmatch(article["original_language"]) is not None
        )
    except (TypeError, KeyError, AttributeError, ValueError):
        ok = False
    if not ok:
        raise ValueError("invalid_article_integrity")


def make_excerpt(article: dict, start: int, end: int) -> dict:
    _verify_article_record(article)
    text = article["original_text"]
    if type(start) is not int or type(end) is not int or not (0 <= start < end <= len(text)) or end-start > 4000:
        raise ValueError("invalid_excerpt_offsets")
    literal = text[start:end]
    return {
        "excerpt_id": "exc_" + _sha(article["revision_id"], article["source_id"], str(start), str(end), literal),
        "article_id": article["article_id"], "revision_id": article["revision_id"],
        "source_id": article["source_id"], "start_cp": start, "end_cp": end,
        "original_language": article["original_language"], "literal": literal,
        "literal_sha256": hashlib.sha256(literal.encode("utf-8")).hexdigest(),
    }


def make_claim(*, statement: str, excerpts: list[dict],
               kind: str = "publisher_assertion") -> dict:
    if kind not in {"publisher_assertion", "analyst_inference"}:
        raise ValueError("claim_kind_not_allowed")
    if not isinstance(statement, str) or not statement.strip() or len(statement) > 2000:
        raise ValueError("invalid_claim")
    if not isinstance(excerpts, list) or not excerpts:
        raise ValueError("claim_requires_source_excerpt")
    excerpt_ids = []
    for excerpt in excerpts:
        if not isinstance(excerpt, dict) or not isinstance(excerpt.get("excerpt_id"), str) or not re.fullmatch(r"exc_[a-f0-9]{24}", excerpt["excerpt_id"]):
            raise ValueError("invalid_excerpt_reference")
        try:
            valid = (
                excerpt["excerpt_id"] == "exc_" + _sha(
                    excerpt["revision_id"], excerpt["source_id"], str(excerpt["start_cp"]),
                    str(excerpt["end_cp"]), excerpt["literal"]
                )
                and excerpt["literal_sha256"] == hashlib.sha256(excerpt["literal"].encode("utf-8")).hexdigest()
                and type(excerpt["start_cp"]) is int and type(excerpt["end_cp"]) is int
                and excerpt["end_cp"] > excerpt["start_cp"]
                and excerpt["end_cp"]-excerpt["start_cp"] == len(excerpt["literal"])
                and re.fullmatch(r"rev_[a-f0-9]{24}", excerpt["revision_id"]) is not None
            )
        except (TypeError, KeyError, AttributeError, ValueError):
            valid = False
        if not valid:
            raise ValueError("excerpt_integrity_failed")
        excerpt_ids.append(excerpt["excerpt_id"])
    excerpt_ids = sorted(set(excerpt_ids))
    statement = statement.strip()
    return {
        "claim_id": "clm_" + _sha(kind, statement, *excerpt_ids),
        "kind": kind, "statement": statement, "excerpt_ids": excerpt_ids,
        "release_status": "attributed_only" if kind == "publisher_assertion" else "not_a_reported_fact",
    }


def make_event(*, key: str, claims: list[dict], status: str = "open",
               closure_claim_id: str | None = None) -> dict:
    # Key is assigned upstream by a separately reviewed entity/event mapping.
    # No automatic merge based on the language, headline, or source host.
    if not isinstance(key, str) or not EVENT_KEY.fullmatch(key):
        raise ValueError("event_requires_explicit_key")
    if status not in {"open", "closed"} or not claims:
        raise ValueError("invalid_event")
    claim_ids = []
    for claim in claims:
        if not isinstance(claim, dict) or not isinstance(claim.get("claim_id"), str) or not re.fullmatch(r"clm_[a-f0-9]{24}", claim["claim_id"]):
            raise ValueError("invalid_claim_reference")
        try:
            valid = (
                claim["kind"] in {"publisher_assertion", "analyst_inference"}
                and claim["statement"].strip() == claim["statement"]
                and claim["excerpt_ids"] == sorted(set(claim["excerpt_ids"]))
                and claim["claim_id"] == "clm_" + _sha(
                    claim["kind"], claim["statement"], *claim["excerpt_ids"]
                )
                and bool(claim["excerpt_ids"])
            )
        except (TypeError, KeyError, AttributeError, ValueError):
            valid = False
        if not valid:
            raise ValueError("claim_integrity_failed")
        claim_ids.append(claim["claim_id"])
    claim_ids = sorted(set(claim_ids))
    if status == "closed" and closure_claim_id not in claim_ids:
        raise ValueError("closure_requires_cited_claim")
    if status != "closed" and closure_claim_id is not None:
        raise ValueError("unexpected_closure_claim")
    event_id = "evt_" + _sha(key)
    return {
        "event_id": event_id, "explicit_key": key, "status": status,
        "claim_ids": claim_ids, "closure_claim_id": closure_claim_id,
        "version_id": "evr_" + _sha(event_id, status, closure_claim_id or "", *claim_ids),
        "publisher_independence": "unverified",
    }


def event_delta(before: dict | None, after: dict) -> str:
    if before is None:
        return "new"
    if before["event_id"] != after["event_id"]:
        raise ValueError("cannot_compare_different_events")
    if before["version_id"] == after["version_id"]:
        return "unchanged"
    if before["status"] != "closed" and after["status"] == "closed":
        return "explicitly_closed"
    return "changed"


def make_translation(*, article: dict, target_language: str, candidate_text: str,
                     engine_id: str) -> dict:
    """Candidate translation is not factual evidence until separately validated."""
    _verify_article_record(article)
    if not isinstance(target_language, str) or not LANGUAGE.fullmatch(target_language) or not isinstance(candidate_text, str) or not candidate_text.strip():
        raise ValueError("invalid_translation")
    if not isinstance(engine_id, str) or not re.fullmatch(r"[A-Za-z0-9._-]{3,80}", engine_id):
        raise ValueError("invalid_translation_engine")
    return {
        "translation_id": "trn_" + _sha(article["revision_id"], target_language, candidate_text, engine_id),
        "source_article_id": article["article_id"], "source_revision_id": article["revision_id"],
        "source_language": article["original_language"], "target_language": target_language,
        "candidate_text": candidate_text, "engine_id": engine_id,
        "verification": "unverified_candidate",
    }
