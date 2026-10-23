"""Bounded, entirely offline B2 source-freshness and rights triage.

Only consumes the committed registry/historical audit. Does not probe URLs,
decide licensing, infer independent ownership or promote a source.
"""
from __future__ import annotations

from urllib.parse import urlsplit

_TARGET_REGIONS = ("somalia", "yemen", "egypt", "jordan", "uae")


def _status(row: dict) -> str:
    observed = row.get("observed") or {}
    if row.get("legacy_state") == "claimed_active" and observed.get("compatible") is True:
        if int(observed.get("dated_72h") or 0) > 0:
            return "historical_dated_recent"
        return "historical_compatible_without_dated_recent"
    return "historical_not_compatible_or_disabled"


def _entry(row: dict) -> dict:
    return {
        "id": row["id"], "name": row["name"],
        "host_candidate": row.get("host_candidate"),
        "entrypoint": row["entrypoint"],
        "status": _status(row),
        "rights": "unreviewed", "independent_publisher_family": "unverified",
        "live_probe": "not_attempted",
    }


def source_gate_report(registry: dict, *, max_live_candidates_per_area: int = 2) -> dict:
    if not isinstance(registry, dict) or registry.get("schema_version") != "2.0.0-preview":
        raise ValueError("source_gate_requires_pinned_registry")
    if type(max_live_candidates_per_area) is not int or not 1 <= max_live_candidates_per_area <= 2:
        raise ValueError("bounded_probe_limit_1_or_2")
    sources = registry.get("sources")
    coverage = registry.get("coverage")
    if not isinstance(sources, list) or not isinstance(coverage, dict):
        raise ValueError("invalid_source_registry")
    ids = [row["id"] for row in sources]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate_source_ids")
    by_id = {row["id"]: row for row in sources}
    geo = {c["region"]: c for c in coverage["arabic_regions"]}
    geo["uae"] = coverage["uae_country"]
    output = {}
    for area in _TARGET_REGIONS:
        summary = geo[area]
        region_rows = [
            row for row in sources
            if row["stream"] == "arabic" and (
                (row.get("region") == area if area != "uae" else row.get("country") == "AE")
            )
        ]
        known_fresh = sorted(
            (r for r in region_rows if _status(r) == "historical_dated_recent"),
            key=lambda r: (-int(r["observed"]["dated_72h"]), r["id"]),
        )
        candidates = []
        seen_hosts = set()
        for row in known_fresh + sorted(
            (r for r in region_rows if _status(r) == "historical_compatible_without_dated_recent"),
            key=lambda r: r["id"],
        ):
            host = row.get("host_candidate") or urlsplit(row["entrypoint"]).hostname
            if not host or host in seen_hosts:
                continue
            seen_hosts.add(host)
            candidates.append(_entry(row))
            if len(candidates) == max_live_candidates_per_area:
                break
        missing = sorted((r for r in region_rows if _status(r) == "historical_not_compatible_or_disabled"),
                         key=lambda r: r["id"])
        recent_hosts = {r.get("host_candidate") for r in known_fresh if r.get("host_candidate")}
        recorded = set(summary["historical_dated_source_ids"])
        computed = {r["id"] for r in known_fresh}
        if computed != recorded or len(recent_hosts) != summary["distinct_host_candidates_with_dated_recent"] or len(computed) != summary["historical_dated_recent"]:
            raise ValueError("coverage_snapshot_disagrees_with_source_rows:"+area)
        if summary["verified_independent_families"] != 0:
            raise ValueError("verified_family_evidence_not_supported")
        output[area] = {
            "goal_independent_families": summary["goal_independent_families"],
            "historical_dated_source_ids": sorted(computed),
            "historical_distinct_host_candidates": len(recent_hosts),
            "verified_independent_families": 0,
            "gap_flags": list(summary["gaps"]),
            "bounded_probe_queue": candidates,
            "manual_recovery_queue": [_entry(r) for r in missing[:2]],
            "ready": False,
            "closure_requires": ["current_live_adapter_and_freshness_probe",
                                 "publisher_identity_and_family_verification",
                                 "file_or_feed_specific_usage_rights_review"],
        }
    return {
        "schema": "aggregateit-v2-source-gate-offline/1",
        "audit_snapshot_as_of_utc": registry.get("as_of_utc"),
        "registry_source_ids": len(ids),
        "live_requests_made": 0,
        "sources_promoted": 0,
        "publisher_rights_verified": 0,
        "areas": output,
        "gate_status": "hold_unverified_live_rights_independence",
    }
