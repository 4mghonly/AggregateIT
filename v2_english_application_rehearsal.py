"""Safe V2-to-real-English-renderer rehearsal; exclusively synthetic and NO-POST.

This bridge deliberately does not import ``slide.py``: its executable entry
point collects live data, invokes a model and sends a Discord webhook.  The
same genuine English page renderer is called with the evidence-gated B4 plan
and explicitly unavailable market/social data.  This is NOT a live edition.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import socket
from unittest.mock import patch

from PIL import Image

from v2_offline_rehearsal import run_offline_rehearsal


_ANALYSIS = {
    "headline": "SYNTHETIC TEST: source-attributed observations only",
    "lead": "This is an offline synthetic source-rehearsal. All source statements are unverified. No market or model data was supplied.",
    "geopol_read": "Displayed synthetic statements are attributed to fixture sources. Their truth and publisher independence have not been established.",
    "market_read": "Market snapshots were not provided. Price moves, market breadth and correlations are unavailable.",
    "social_read": "Social-platform observations were not provided. No sentiment conclusion can be drawn.",
    "cross_asset": "No verified financial observations are available to compare asset classes.",
    "outlook": "This test cannot establish a live outlook. Source recency and coverage require independent verification.",
    "key_risk": "No current reporting or market data has been independently verified.",
    "delta": "No authenticated previous edition exists for this synthetic test.",
}


def synthetic_fixture() -> dict:
    """Deterministic, explicitly non-publisher data; offsets are code points."""
    stamp = "2026-10-23T08:00:00+00:00"

    def row(source, language, text, event, region, country):
        return {
            "source_id": source,
            "url": "https://fixture.invalid/" + source,
            "original_text": text,
            "original_language": language,
            "retrieved_at": stamp,
            "published_at": stamp,
            "excerpt_start": 0,
            "excerpt_end": len(text),
            "claim_statement": "Synthetic statement: " + text,
            "explicit_event_key": event,
            "region": region,
            "subject_country": country,
            "topic_english": "geopolitics",
            "topic_arabic": "security",
            "priority": 80,
        }

    return {
        "schema": "aggregateit-v2-offline-rehearsal/1",
        "synthetic": True,
        "as_of": stamp,
        "slot_id": "2026-10-23T12:00:00+04:00",
        "documents": [
            row("en-001", "en", "A fictional port authority announced a simulated maritime safety drill.", "simulated-port", "gcc", "AE"),
            row("ar-s001", "ar", "أعلنت هيئة ميناء خيالية عن تدريب تجريبي للسلامة البحرية.", "simulated-port", "gcc", "AE"),
            row("en-002", "en", "A fictional diplomatic mission published a simulated consultation notice.", "simulated-diplomacy", "levant", "JO"),
            row("en-003", "en", "A fictional cyber response team completed an entirely simulated exercise.", "simulated-cyber", "gcc", "AE"),
            row("ar-s019", "fa", "این گزارش صرفاً برای آزمایش است.", "simulated-foreign", "iran", "IR"),
        ],
    }


def _render_data(plan: dict) -> dict:
    if plan.get("product") != "english" or plan.get("delivery_authorized") is not False:
        raise ValueError("unapproved_english_editorial_plan")
    items = plan.get("items", [])
    if not items:
        raise ValueError("no_native_english_excerpt_to_render")
    events = []
    for item in items:
        source = item["evidence"]
        if source["original_language"].split("-")[0] != "en":
            raise ValueError("non_english_source_not_admitted")
        if item["reporting_status"] != "publisher_attributed_not_independently_verified":
            raise ValueError("unverified_reporting_status_changed")
        events.append({
            "event_id": item["event_id"],
            "title": source["quote"],
            "source": source["source_id"],
            "severity": "Unrated",
            "status": "UNVERIFIED",
            "confidence": None,
            "source_count": 1,
            "ts": datetime.fromisoformat(source["source_date"]).timestamp(),
            "tickers": [],
            "sentiment": "unknown",
        })
    return {
        "sample": True,
        "store": None,
        "events": events,
        "geo_events": list(events),
        "headlines": list(events),
        "sources_active": sorted({e["source"] for e in events}),
        "event_window_h": 48,
        "pulse": {"valid": False, "updated": None},
        "macro": {"valid": False, "updated": None},
        "regime": {},
        "sector_tape": [],
        "curve_pts": {},
        "yield_hist": [],
        "themes": {},
        "st_radar": [],
        "reddit": {},
        "social_pulse": {},
        "previous_edition": None,
    }


def rehearse_english(fixture: dict, registry: dict) -> dict:
    """Render two actual V1-format English pages to RAM, with egress blocked.

    The B3/B4/B5/B6 gate is exercised first, and the rendered event list is
    derived only from its admitted native-English evidence. No caller-supplied
    prose or market figures can bypass that admission step.
    """
    with patch.object(socket, "socket", side_effect=RuntimeError("offline_network_forbidden")):
        rehearsal = run_offline_rehearsal(fixture, registry)
        plan = rehearsal["products"]["english"]["plan"]
        data = _render_data(plan)
        # Import only the safe renderer, never slide.collect/analyze/send.
        from gazette_render import render_p1, render_p2
        pages = []
        for page_number, renderer in enumerate((render_p1, render_p2), start=1):
            buffer = BytesIO()
            renderer(data, dict(_ANALYSIS), False, buffer)
            raw = buffer.getvalue()
            with Image.open(BytesIO(raw)) as image:
                if image.format != "PNG" or image.size != (3840, 2160):
                    raise ValueError("unexpected_english_page_format")
                image.verify()
            pages.append({
                "page_number": page_number,
                "png": raw,
                "sha256": sha256(raw).hexdigest(),
                "dimensions": [3840, 2160],
            })
    return {
        "schema": "aggregateit-v2-english-application-rehearsal/1",
        "synthetic": True,
        "publisher_rights": "unverified",
        "independent_reporting": "unverified",
        "live_collector_called": False,
        "live_model_called": False,
        "discord_sent": False,
        "database_written": False,
        "market_data": "unavailable",
        "language": "en",
        "selected": plan["selected"],
        "source_ids": data["sources_active"],
        "held_reasons": plan["held_reasons"],
        "evidence_receipt": rehearsal["journal"],
        "pages": pages,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic English Gazette render; no fetch/model/Discord")
    parser.add_argument("--output", type=Path, required=True,
                        help="Existing directory for two new sample PNG files (no overwrite)")
    args = parser.parse_args(argv)
    output = args.output
    if not output.is_dir() or output.is_symlink():
        parser.error("--output must be an existing, non-symlink directory")
    targets = [output / f"english-v2-synthetic-page-{i}.png" for i in (1, 2)]
    if any(path.exists() or path.is_symlink() for path in targets):
        parser.error("output page path already exists; refusing to overwrite")
    registry_path = Path(__file__).parent / "config/v2/source_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    receipt = rehearse_english(synthetic_fixture(), registry)
    for path, page in zip(targets, receipt["pages"]):
        with path.open("xb") as f:
            f.write(page["png"])
    print(json.dumps({
        k: ([{"page_number": p["page_number"], "sha256": p["sha256"],
              "dimensions": p["dimensions"], "path": str(path)}
             for p, path in zip(receipt["pages"], targets)] if k == "pages" else v)
        for k, v in receipt.items()
    }, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
