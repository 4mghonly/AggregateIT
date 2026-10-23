"""B6 experimental analytics controls. No D1 connection, deletion, or schedule.

Only bounded operational metadata is accepted. Dry-run retention never mutates
its input and never returns a command that executes deletion.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

ALLOWED_KINDS = frozenset({
    "source_probe", "model_attempt", "translation", "edition",
    "render", "delivery",
})
ALLOWED_STATUS = frozenset({
    "ok", "failed", "degraded", "withheld", "unknown",
})
ALLOWED_FIELDS = frozenset({
    "idempotency_key", "kind", "product", "source_id", "at",
    "status", "duration_ms", "attempts", "units",
})
DETAIL_RETENTION_DAYS = 30
AGGREGATE_RETENTION_DAYS = 365
WARN_BYTES = 250_000_000
THROTTLE_BYTES = 300_000_000
STOP_BYTES = 350_000_000
WRITE_DAY_LIMIT = 20_000
READ_DAY_TARGET = 250_000


def _date(stamp: str):
    if not isinstance(stamp, str):
        raise ValueError("bad_timestamp")
    try:
        dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("bad_timestamp") from None
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("bad_timestamp")
    return dt.astimezone(timezone.utc)


def validate_telemetry(event: dict) -> dict:
    if not isinstance(event, dict) or not set(event).issubset(ALLOWED_FIELDS):
        raise ValueError("telemetry_contains_unapproved_fields")
    if not {"idempotency_key", "kind", "product", "at", "status"}.issubset(event):
        raise ValueError("telemetry_missing_fields")
    if (event["kind"] not in ALLOWED_KINDS or event["status"] not in ALLOWED_STATUS
            or event["product"] not in {"arabic", "english"}):
        raise ValueError("invalid_telemetry_enums")
    key = event["idempotency_key"]
    if not isinstance(key, str) or not 5 <= len(key) <= 120 or not all(c.isalnum() or c in "-_:." for c in key):
        raise ValueError("invalid_idempotency_key")
    _date(event["at"])
    sid = event.get("source_id")
    if sid is not None and (not isinstance(sid, str) or len(sid) > 20 or
                            not (sid.startswith("ar-s") or sid.startswith("en-"))):
        raise ValueError("invalid_telemetry_source")
    for name in ("duration_ms", "attempts", "units"):
        value = event.get(name)
        if value is not None and (type(value) is not int or value < 0 or value > 1_000_000):
            raise ValueError("invalid_telemetry_quantity")
    return dict(event)


def budget_decision(*, db_size_bytes: int | None, account_writes_today: int | None,
                    account_reads_today: int | None, proposed_writes: int,
                    proposed_reads: int, detail: bool = True) -> dict:
    if any(type(x) is not int or x < 0 for x in (proposed_writes, proposed_reads)):
        raise ValueError("invalid_proposed_usage")
    if any(x is None for x in (db_size_bytes, account_writes_today, account_reads_today)):
        return {"action": "hold_unverified_account_headroom", "permitted": False}
    if any(type(x) is not int or x < 0 for x in (db_size_bytes, account_writes_today, account_reads_today)):
        raise ValueError("invalid_current_usage")
    if db_size_bytes >= STOP_BYTES:
        return {"action": "stop_optional_analytics", "permitted": False}
    if (account_writes_today + proposed_writes > WRITE_DAY_LIMIT or
            account_reads_today + proposed_reads > READ_DAY_TARGET):
        return {"action": "stop_usage_budget", "permitted": False}
    if db_size_bytes >= THROTTLE_BYTES and detail:
        return {"action": "throttle_detail", "permitted": False}
    return {
        "action": "warn_and_aggregate" if db_size_bytes >= WARN_BYTES else "allow",
        "permitted": True, "write_remaining": WRITE_DAY_LIMIT - account_writes_today - proposed_writes,
        "read_remaining": READ_DAY_TARGET - account_reads_today - proposed_reads,
    }


def retention_preview(rows: list[dict], *, as_of: str) -> dict:
    now = _date(as_of)
    if not isinstance(rows, list) or len(rows) > 50_000:
        raise ValueError("invalid_retention_input")
    candidates = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "at", "retention_class"}:
            raise ValueError("invalid_retention_row")
        if not isinstance(row["id"], str) or not row["id"] or len(row["id"]) > 120:
            raise ValueError("invalid_row_id")
        kind = row["retention_class"]
        if kind not in {"detail", "daily_aggregate"}:
            raise ValueError("invalid_retention_class")
        days = DETAIL_RETENTION_DAYS if kind == "detail" else AGGREGATE_RETENTION_DAYS
        age_days = (now - _date(row["at"])).total_seconds() / 86400
        if age_days > days:
            candidates.append(row["id"])
    return {
        "mode": "DRY_RUN_ONLY", "candidate_ids": sorted(set(candidates)),
        "candidate_count": len(set(candidates)),
        "scheduled_hour_uae": "04:30",
        "backup_state": "manual_export_not_verified",
        "delete_authorized": False,
        "requires": ["verified_export_checksum", "tested_restore", "explicit_owner_approval"],
    }


def export_manifest(rows: list[dict], *, as_of: str) -> dict:
    """Manifest of exact telemetry JSON, not a Drive upload or backup itself."""
    _date(as_of)
    records = [validate_telemetry(row) for row in rows]
    serialized = json.dumps(records, ensure_ascii=False, sort_keys=True,
                            separators=(",", ":"), allow_nan=False).encode("utf-8")
    return {
        "format": "aggregateit-telemetry-export/1",
        "as_of": as_of, "records": len(records),
        "sha256": hashlib.sha256(serialized).hexdigest(),
        "verified_restore": False,
        "google_drive_uploaded": False,
    }
