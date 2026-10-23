"""Offline-only validator for V2's versioned source inventory.

Does not fetch URLs, mutate registries, publish briefings, or write a database.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent


def _host(url: str | None) -> str | None:
    if not url:
        return None
    try:
        return (urlsplit(url).hostname or "").lower().removeprefix("www.") or None
    except ValueError:
        return None


def _canonical_feed(url: str) -> str:
    split = urlsplit(url.strip())
    return f"{split.scheme.lower()}://{split.netloc.lower()}{split.path.rstrip('/')}" + (
        f"?{split.query}" if split.query else ""
    )


def _coverage(region: str, rows: list[dict], target: int) -> dict:
    compatible = [r for r in rows if (r.get("observed") or {}).get("compatible") is True]
    dated = [r for r in compatible if r["observed"]["dated_72h"] > 0]
    hosts = {_host(r.get("publisher_site") or r.get("entrypoint")) for r in dated}
    hosts.discard(None)
    gaps = ["independent_publishers_not_verified"]
    if len(compatible) < target:
        gaps.append("historical_compatible_below_floor")
    if len(dated) < target:
        gaps.append("historical_dated_recent_below_floor")
    if len(hosts) < target:
        gaps.append("distinct_host_candidates_below_floor")
    return {
        "region": region,
        "goal_independent_families": target,
        "configured": len(rows),
        "legacy_enabled": sum(r["legacy_state"] == "claimed_active" for r in rows),
        "historical_adapter_compatible": len(compatible),
        "historical_dated_recent": len(dated),
        "distinct_host_candidates_with_dated_recent": len(hosts),
        "verified_independent_families": 0,
        "historical_dated_source_ids": [r["id"] for r in dated],
        "gaps": gaps,
    }


def validate_registry(registry: dict, english: list[dict], arabic: list[dict], audit: dict) -> list[str]:
    """Compare the immutable inventory to its three local source-of-record files."""
    errors: list[str] = []
    def check(ok: bool, code: str) -> None:
        if not ok:
            errors.append(code)

    entries = registry.get("sources", [])
    check(registry.get("schema_version") == "2.0.0-preview", "schema_version")
    check(registry.get("sources_of_record", {}).get("arabic_audit_checked_at") == audit.get("checked_at"), "audit_date_drift")
    check(len(entries) == len(english) + len(arabic), "source_count")
    ids = [r.get("id") for r in entries]
    check(len(set(ids)) == len(ids), "duplicate_ids")
    by_id = {r.get("id"): r for r in entries}
    check(all(x.get("independence_status") is None for x in entries), "unapproved_independence_certification")
    check(all(x.get("rights_status") is None for x in entries), "unapproved_rights_certification")
    check("not reviewed" in registry.get("interpretation", {}).get("rights", ""), "rights_policy_missing")
    check("unverified" in registry.get("interpretation", {}).get("independence", ""), "independence_policy_missing")

    for row in english:
        sid = f"en-{int(row['Id']):03d}"
        item = by_id.get(sid)
        if item is None:
            errors.append(f"english_missing:{sid}")
            continue
        state = "disabled" if row.get("enabled") is False else (
            "claimed_active" if row.get("Verification_status") == "Active" else "unverified"
        )
        is_repo = urlsplit(row["Url"]).hostname == "github.com" and (
            (urlsplit(row["Url"]).path.rstrip("/").count("/") == 2)
        )
        check(item.get("stream") == "english", f"english_stream:{sid}")
        check(item.get("legacy_id") == row["Id"] and item.get("name") == row["Source_name"], f"english_identity:{sid}")
        check(item.get("entrypoint") == row["Url"] and item.get("legacy_state") == state, f"english_source_drift:{sid}")
        check(item.get("entrypoint_type") == ("discovery_only" if is_repo else "feed"), f"english_adapter:{sid}")
        check("region" not in item and "language" not in item, f"english_unjustified_enrichment:{sid}")

    audit_by_id = {r["id"]: r for r in audit["sources"]}
    for row in arabic:
        sid = f"ar-{row['id']}"
        item = by_id.get(sid)
        if item is None:
            errors.append(f"arabic_missing:{sid}")
            continue
        p = audit_by_id.get(row["id"])
        check(item.get("stream") == "arabic", f"arabic_stream:{sid}")
        check(item.get("legacy_id") == row["id"] and item.get("name") == row["name"], f"arabic_identity:{sid}")
        check(item.get("entrypoint") == (row.get("feed") or row.get("website")), f"arabic_source_drift:{sid}")
        check(item.get("legacy_state") == ("claimed_active" if row.get("enabled") else "disabled"), f"arabic_enable_drift:{sid}")
        check(
            item.get("region") == row.get("region") and item.get("country") == row.get("country")
            and item.get("language") == row.get("language"),
            f"arabic_geo_lang:{sid}",
        )
        check(item.get("publisher_site") == row.get("website"), f"arabic_publisher_site:{sid}")
        expected_adapter = "html_headlines" if row.get("adapter") == "html_headlines" else (
            "feed" if row.get("feed") else "unverified"
        )
        check(item.get("entrypoint_type") == expected_adapter, f"arabic_adapter:{sid}")
        if p:
            obs = item.get("observed") or {}
            check(obs.get("compatible") is p.get("production_compatible"), f"probe_compatible:{sid}")
            check(obs.get("entries") == p.get("entries"), f"probe_entries:{sid}")
            check(obs.get("dated_72h") == p.get("recent_72h"), f"probe_recent:{sid}")
            check(obs.get("reason") == p.get("reason"), f"probe_reason:{sid}")
            check(obs.get("http") == p.get("feed_http"), f"probe_http:{sid}")
        else:
            check("observed" not in item, f"unexpected_probe:{sid}")

    cross = defaultdict(list)
    for item in entries:
        if item.get("entrypoint_type") != "feed":
            continue
        cross[_canonical_feed(item["entrypoint"])].append(item["id"])
    overlaps = [{"url": url, "source_ids": group} for url, group in cross.items() if len(group) > 1]
    check(overlaps == registry.get("shared_feed_urls"), "shared_feed_urls_drift")

    observed_regions = [x["region"] for x in registry.get("coverage", {}).get("arabic_regions", [])]
    check(set(observed_regions) == set(audit.get("regions", {})), "region_keys_drift")
    for cov in registry.get("coverage", {}).get("arabic_regions", []):
        region = cov["region"]
        target = 3 if region == "gcc" else 2
        expected = _coverage(region, [r for r in entries if r.get("stream") == "arabic" and r.get("region") == region], target)
        check(cov == expected, f"region_coverage_drift:{region}")
    uae = _coverage("AE", [r for r in entries if r.get("stream") == "arabic" and r.get("country") == "AE"], 3)
    check(registry.get("coverage", {}).get("uae_country") == uae, "uae_coverage_drift")
    check(registry.get("coverage", {}).get("english_geo") == "unmapped_from_legacy_list", "english_geo_claim")
    return errors


def load_inputs(root: Path = ROOT) -> tuple[dict, list[dict], list[dict], dict]:
    def read(p: str):
        return json.loads((root / p).read_text(encoding="utf-8"))
    return (
        read("config/v2/source_registry.json"),
        read("config/sources.json"),
        read("arabic_newsletter/sources.json"),
        read("arabic_newsletter/SOURCE_AUDIT.json"),
    )


def main() -> int:
    registry, en, ar, audit = load_inputs()
    errors = validate_registry(registry, en, ar, audit)
    if errors:
        for err in errors:
            print(f"FAIL {err}")
        return 1
    print(
        f"PASS: {len(registry['sources'])} source records; "
        f"{len(registry['shared_feed_urls'])} shared feeds; "
        f"{len(registry['coverage']['arabic_regions'])} Arabic regions; "
        "live health, rights and independence NOT certified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
