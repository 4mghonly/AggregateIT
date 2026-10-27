"""B7 same-window, no-post comparison of explicitly supplied run metrics.

No live collector, newsletter renderer, model, Discord or cloud integration.
No quality metric may claim independent-source trust or editorial truthfulness.
"""
from __future__ import annotations

from datetime import datetime, timezone

from v2_evidence import _time

METRIC_KEYS = frozenset({
    "sources_attempted", "sources_usable", "events_selected",
    "items_cited", "items_rendered", "translation_attempted",
    "translation_succeeded", "layout_omissions", "clipped_items",
})
HIGHER_IS_BETTER = frozenset({
    "sources_usable", "items_cited", "items_rendered", "translation_succeeded",
})
LOWER_IS_BETTER = frozenset({"layout_omissions", "clipped_items"})


def validate_run(row: dict) -> dict:
    if not isinstance(row, dict) or set(row) != {
        "product", "window_start", "window_end", "code_revision",
        "metrics", "region_counts", "delivery_status",
    }:
        raise ValueError("invalid_run_manifest")
    if row["product"] not in {"english", "arabic"}:
        raise ValueError("bad_product")
    begin, end = _time(row["window_start"]), _time(row["window_end"])
    from datetime import datetime
    if datetime.fromisoformat(begin) >= datetime.fromisoformat(end):
        raise ValueError("invalid_run_window")
    revision = row["code_revision"]
    if not isinstance(revision, str) or not 7 <= len(revision) <= 64 or not all(
            c in "0123456789abcdef" for c in revision):
        raise ValueError("invalid_revision")
    # This offline manifest has no authenticated receipt evidence field. Never
    # accept a bare caller assertion of externally confirmed delivery.
    if row["delivery_status"] not in {"not_attempted", "unknown", "confirmed_unverified"}:
        raise ValueError("bad_delivery_status")
    m = row["metrics"]
    if not isinstance(m, dict) or set(m) != METRIC_KEYS or any(
            type(v) is not int or v < 0 for v in m.values()):
        raise ValueError("bad_metric_counts")
    if (m["sources_usable"] > m["sources_attempted"] or
        m["items_cited"] > m["events_selected"] or
        m["items_rendered"] > m["events_selected"] or
        m["items_rendered"] > m["items_cited"] or
        m["clipped_items"] > m["items_rendered"] or
        m["layout_omissions"] > m["events_selected"] or
        m["translation_succeeded"] > m["translation_attempted"]):
        raise ValueError("contradictory_metric_counts")
    geo = row["region_counts"]
    if not isinstance(geo, dict) or len(geo) > 40 or any(
            not isinstance(k, str) or len(k) > 40 or
            type(v) is not int or v < 0 for k, v in geo.items()):
        raise ValueError("invalid_region_counts")
    return row


def _window_identity(row: dict) -> tuple:
    """Compare real UTC instants, not different spellings of the same slot."""
    return (
        row["product"],
        datetime.fromisoformat(_time(row["window_start"])).astimezone(timezone.utc),
        datetime.fromisoformat(_time(row["window_end"])).astimezone(timezone.utc),
    )


def compare_runs(v1: dict, v2: dict) -> dict:
    a, b = validate_run(v1), validate_run(v2)
    if _window_identity(a) != _window_identity(b):
        return {"comparable": False, "reason": "different_product_or_window"}
    changes = {}
    for key in sorted(METRIC_KEYS):
        before, after = a["metrics"][key], b["metrics"][key]
        direction = ("higher" if key in HIGHER_IS_BETTER else
                     "lower" if key in LOWER_IS_BETTER else "diagnostic_only")
        label = "unchanged"
        if direction == "higher" and after != before:
            label = "improved" if after > before else "regressed"
        if direction == "lower" and after != before:
            label = "improved" if after < before else "regressed"
        if direction == "diagnostic_only" and after != before:
            label = "changed_no_quality_inference"
        changes[key] = {
            "v1": before, "v2": after, "delta": after-before,
            "direction": direction, "assessment": label,
        }
    old_regions = set(k for k, v in a["region_counts"].items() if v)
    new_regions = set(k for k, v in b["region_counts"].items() if v)
    return {
        "schema": "aggregateit-shadow-scorecard/1",
        "comparable": True, "product": a["product"],
        "window_start": a["window_start"], "window_end": a["window_end"],
        "v1_revision": a["code_revision"], "v2_revision": b["code_revision"],
        "metrics": changes,
        "regions_gained": sorted(new_regions-old_regions),
        "regions_lost": sorted(old_regions-new_regions),
        "delivery_v1": a["delivery_status"],
        "delivery_v2": b["delivery_status"],
        "source_rights": "unverified", "publisher_independence": "unverified",
        "factual_accuracy": "not_measured",
        "status": "offline_comparison_only",
        "delivery_authorized": False,
    }
