"""B1/B4/B5 native-Arabic V2 evidence -> actual 3-slide renderer, NO POST.

Every displayed event quotation is a literal source-bound synthetic Arabic
span. No translation, editorial inference, severity rating or LLM call is
permitted. The production Arab newsletter collector/sender is never imported.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import socket
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image

from v2_english_application_rehearsal import synthetic_fixture
from v2_offline_rehearsal import run_offline_rehearsal


def arabic_synthetic_fixture() -> dict:
    """A three-country synthetic roster; no host resolves to a publisher."""
    fixture = synthetic_fixture()
    reference = fixture["documents"][1]
    for source_id, event_key, text, region, country in (
        ("ar-s002", "simulated-iran", "نشرت جهة خيالية بياناً تجريبياً بشأن مناورة افتراضية للسلامة الإقليمية.", "iran", "IR"),
        ("ar-s003", "simulated-iraq", "أعلنت مؤسسة تجريبية عن تمرين محاكاة لتبادل المعلومات الأمنية.", "iraq", "IQ"),
    ):
        fixture["documents"].append({
            **reference,
            "source_id": source_id,
            "url": f"https://fixture.invalid/{source_id}",
            "original_text": text,
            "excerpt_end": len(text),
            "claim_statement": "بيان اصطناعي منسوب: " + text,
            "explicit_event_key": event_key,
            "region": region,
            "subject_country": country,
            "topic_english": "security",
        })
    return fixture


def _render_brief(plan: dict, fixture: dict) -> dict:
    if (fixture.get("synthetic") is not True or plan.get("product") != "arabic"
            or plan.get("delivery_authorized") is not False):
        raise ValueError("unapproved_arabic_editorial_plan")
    items = plan.get("items", [])
    if not items:
        raise ValueError("no_native_arabic_excerpt_to_render")
    from v2_b118_layout_gate import prioritize_uae
    events = []
    for item in prioritize_uae(items):
        source = item["evidence"]
        if (source["original_language"].split("-")[0] != "ar"
                or item["reporting_status"] != "publisher_attributed_not_independently_verified"
                or item["analysis_status"] != "abstained_unverified"):
            raise ValueError("unverified_arabic_source_not_admitted")
        quote = source["quote"]
        events.append({
            "fingerprint": item["event_id"],
            "region": item["region"],
            "title_ar": quote.split("،", 1)[0][:100].rstrip(" .،") or quote[:100],
            "summary_ar": quote,
            "assessment_ar": "", "watch_ar": "", "status_ar": "غير متحقق",
            "severity": "unknown",
            "sources": [{
                "source": source["source_id"], "url": source["source_url"],
                "language": "ar", "country": item["subject_country"],
                "published": datetime.fromisoformat(source["source_date"]).timestamp(),
            }],
        })
    end = datetime.fromisoformat(fixture["slot_id"])
    return {
        "sample": True,
        "window_start": (end - timedelta(hours=6)).isoformat(),
        "window_end": end.isoformat(),
        "window_hours": 6, "morning": False,
        "events": events,
        "previous_events": [],
        "analysis": {},
        "coverage": {"event_source_count": len({s["source"] for e in events for s in e["sources"]}),
                     "event_source_languages": {"ar": len(events)}},
        "source_health": {"regions": {}},
        "health": [],
    }


def rehearse_arabic(fixture: dict, registry: dict) -> dict:
    """Generate true 4K Arabic PNGs, safely inside a disposable directory."""
    with patch.object(socket, "socket", side_effect=RuntimeError("offline_network_forbidden")):
        rehearsal = run_offline_rehearsal(fixture, registry)
        plan = rehearsal["products"]["arabic"]["plan"]
        brief = _render_brief(plan, fixture)
        # Render Pages uses only PIL/RAQM, not a collector, LLM or sender.
        from arabic_layout.render_pages import render
        with TemporaryDirectory(prefix="aggregateit-v2-arabic-rehearsal-") as directory:
            paths, clipped = render(brief, directory)
            pages = []
            for i, path in enumerate(paths, start=1):
                raw = path.read_bytes()
                with Image.open(BytesIO(raw)) as image:
                    if image.format != "PNG" or image.size != (3840, 2160):
                        raise ValueError("unexpected_arabic_page_format")
                    image.verify()
                pages.append({"page_number": i, "png": raw, "sha256": sha256(raw).hexdigest(),
                              "dimensions": [3840, 2160]})
    return {
        "schema": "aggregateit-v2-arabic-application-rehearsal/1",
        "synthetic": True, "language": "ar", "source_ids": sorted({s["source"] for e in brief["events"] for s in e["sources"]}),
        "selected": plan["selected"], "held_reasons": plan["held_reasons"],
        "clipped_items": clipped, "publisher_rights": "unverified",
        "independent_reporting": "unverified", "translation": "not_attempted",
        "analysis": "abstained_unverified", "real_collector_called": False,
        "live_model_called": False, "discord_sent": False, "database_written": False,
        "evidence_receipt": rehearsal["journal"], "pages": pages,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic Arabic V2 3-slide rehearsal; NO POST")
    parser.add_argument("--output", type=Path, required=True,
                        help="Existing directory for three new synthetic PNG files")
    args = parser.parse_args(argv)
    output = args.output
    if not output.is_dir() or output.is_symlink():
        parser.error("--output must be an existing, non-symlink directory")
    targets = [output / f"arabic-v2-synthetic-page-{i}.png" for i in (1, 2, 3)]
    if any(path.exists() or path.is_symlink() for path in targets):
        parser.error("output page path already exists; refusing to overwrite")
    registry = json.loads((Path(__file__).parent / "config/v2/source_registry.json").read_text(encoding="utf-8"))
    result = rehearse_arabic(arabic_synthetic_fixture(), registry)
    for target, page in zip(targets, result["pages"]):
        with target.open("xb") as stream:
            stream.write(page["png"])
    print(json.dumps({
        k: ([{"page_number": page["page_number"], "sha256": page["sha256"],
              "dimensions": page["dimensions"], "path": str(target)}
             for page, target in zip(result["pages"], targets)] if k == "pages" else v)
        for k, v in result.items()
    }, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
