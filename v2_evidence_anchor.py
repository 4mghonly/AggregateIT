"""B3 offline HMAC checkpoint for a *separately retained* journal receipt.

The signing key must be supplied by the caller and never stored here.  This
does not authenticate a news publisher and does not itself store an anchor
off-host.  Rollback detection only works when a more recent authenticated
anchor is preserved outside the journal owner's control.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json
import re


_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_KEY_ID = re.compile(r"^[a-zA-Z0-9_.:-]{1,64}$")


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _check_key(secret):
    if not isinstance(secret, bytes) or len(secret) < 32:
        raise ValueError("anchor_requires_32_byte_secret")


def _check_receipt(receipt):
    if not isinstance(receipt, dict) or set(receipt) != {
        "format", "seq", "head_sha256", "journal_bytes", "counters"
    } or receipt["format"] != "v2-evidence-jsonl/1":
        raise ValueError("invalid_anchor_receipt")
    if (type(receipt["seq"]) is not int or receipt["seq"] < 0
            or type(receipt["journal_bytes"]) is not int or receipt["journal_bytes"] < 0
            or not isinstance(receipt["head_sha256"], str)
            or not _HEX64.fullmatch(receipt["head_sha256"])):
        raise ValueError("invalid_anchor_receipt")
    counters = receipt["counters"]
    expected_counts = {"observations", "unique_articles", "duplicate_article_observations",
                       "excerpts", "claims", "events", "event_versions", "explicit_relations"}
    if (not isinstance(counters, dict)
            or set(counters) != expected_counts | {"publisher_independence"}
            or counters["publisher_independence"] != "not_verified"
            or any(type(counters[name]) is not int or counters[name] < 0 for name in expected_counts)):
        raise ValueError("invalid_anchor_receipt")
    _canonical(receipt)


def _issued_at(value):
    try:
        time = datetime.fromisoformat(value)
        if time.tzinfo is None:
            raise ValueError
        return time.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("invalid_anchor_issue_time") from exc


def sign_anchor(receipt, *, secret: bytes, key_id: str, issued_at: str,
                previous_anchor_sha256: str | None = None):
    """Return a portable signed checkpoint for independent offline retention."""
    _check_key(secret)
    _check_receipt(receipt)
    if not isinstance(key_id, str) or not _KEY_ID.fullmatch(key_id):
        raise ValueError("invalid_anchor_key_id")
    if previous_anchor_sha256 is not None and (
        not isinstance(previous_anchor_sha256, str)
        or not _HEX64.fullmatch(previous_anchor_sha256)
    ):
        raise ValueError("invalid_previous_anchor_digest")
    body = {
        "schema": "aggregateit-v2-evidence-anchor/1",
        "key_id": key_id,
        "issued_at_utc": _issued_at(issued_at),
        "previous_anchor_sha256": previous_anchor_sha256,
        "receipt": json.loads(_canonical(receipt)),
        "attestation": "operator_checkpoint_not_publisher_proof",
    }
    return {**body, "mac_sha256": hmac.new(secret, _canonical(body), sha256).hexdigest()}


def _authenticated_record(anchor, *, secret: bytes, expected_key_id: str):
    _check_key(secret)
    if not isinstance(anchor, dict) or set(anchor) != {
        "schema", "key_id", "issued_at_utc", "previous_anchor_sha256",
        "receipt", "attestation", "mac_sha256"
    }:
        raise ValueError("invalid_anchor_record")
    if anchor["schema"] != "aggregateit-v2-evidence-anchor/1" or anchor["attestation"] != "operator_checkpoint_not_publisher_proof":
        raise ValueError("invalid_anchor_record")
    if not isinstance(expected_key_id, str) or anchor["key_id"] != expected_key_id:
        raise ValueError("anchor_key_id_mismatch")
    if _issued_at(anchor["issued_at_utc"]) != anchor["issued_at_utc"]:
        raise ValueError("noncanonical_anchor_time")
    _check_receipt(anchor["receipt"])
    parent = anchor["previous_anchor_sha256"]
    if parent is not None and (not isinstance(parent, str) or not _HEX64.fullmatch(parent)):
        raise ValueError("invalid_previous_anchor_digest")
    if not isinstance(anchor["mac_sha256"], str) or not _HEX64.fullmatch(anchor["mac_sha256"]):
        raise ValueError("invalid_anchor_mac")
    body = {k: v for k, v in anchor.items() if k != "mac_sha256"}
    expected_mac = hmac.new(secret, _canonical(body), sha256).hexdigest()
    if not hmac.compare_digest(anchor["mac_sha256"], expected_mac):
        raise ValueError("anchor_mac_mismatch")
    return anchor


def verify_anchor(anchor, receipt, *, secret: bytes,
                  expected_key_id: str, previous_anchor: dict | None = None):
    """Require an authenticated, byte-consistent chain link and current head."""
    _check_receipt(receipt)
    _authenticated_record(anchor, secret=secret, expected_key_id=expected_key_id)
    if anchor["receipt"] != receipt:
        raise ValueError("external_anchor_receipt_mismatch")
    if previous_anchor is None:
        if anchor["previous_anchor_sha256"] is not None:
            raise ValueError("previous_external_anchor_required")
    else:
        # An independently retained previous anchor must itself be authenticated.
        _authenticated_record(previous_anchor, secret=secret,
                              expected_key_id=expected_key_id)
        previous_digest = sha256(_canonical(previous_anchor)).hexdigest()
        if anchor["previous_anchor_sha256"] != previous_digest:
            raise ValueError("anchor_chain_mismatch")
        if receipt["seq"] < previous_anchor["receipt"]["seq"]:
            raise ValueError("anchor_sequence_rollback")
        if (receipt["seq"] == previous_anchor["receipt"]["seq"]
                and receipt != previous_anchor["receipt"]):
            raise ValueError("anchor_same_sequence_fork")
    return True
