"""B34: bounded GitHub-hosted original-byte RSS comparison; no publication.

Fetches only four pre-registered publisher HTTPS feeds. Observations remain
candidate/parser evidence, not article verification or redistribution rights.
Raw publisher bodies are never written to logs, artifacts, or repository.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import socket
import ssl
from urllib.error import HTTPError

from v2_b33_capture_comparison import compare_imported_capture
from v2_secure_transport import pinned_https_fetch

SOURCES = (
    ("english", "bbc-world", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("english", "bbc-middle-east", "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml"),
    ("arabic", "aljazeera-ar", "https://www.aljazeera.net/aljazeerarss/ar/all.xml"),
    ("arabic", "france24-ar", "https://www.france24.com/ar/rss"),
)
MAX_BYTES = 1_000_000


def _error_type(exc: Exception) -> str:
    if isinstance(exc, HTTPError):
        return f"http_{exc.code}"
    if isinstance(exc, socket.gaierror):
        return "dns_resolution_failed"
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "network_timeout"
    if isinstance(exc, ssl.SSLError):
        return "tls_verification_failed"
    if isinstance(exc, ValueError):
        return "unsafe_or_invalid_source"
    if isinstance(exc, OSError):
        return "network_io_failed"
    return "parser_or_runtime_failed"


def probe(product: str, label: str, url: str) -> dict:
    """One bounded network attempt; complete comparison on the *same* bytes."""
    row = {"product": product, "source_label": label, "feed_url": url,
           "status": "hold", "raw_body_artifact": False,
           "article_body_verified": False, "publisher_rights_verified": False,
           "discord_sent": False, "production_change": False}
    try:
        packet = pinned_https_fetch(
            url, timeout=9, max_bytes=MAX_BYTES, max_redirects=1,
            headers={"Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
        raw = packet["body"]
        if not isinstance(raw, bytes) or not 1 <= len(raw) <= MAX_BYTES:
            raise ValueError("invalid_feed_byte_budget")
        observed_at = datetime.now(timezone.utc).isoformat()
        receipt = {"schema": "aggregateit-v2-b33-import/1",
                   "capture_kind": "unattested_external_bytes",
                   "product": product, "feed_url": packet["final_url"],
                   "observed_at": observed_at, "sha256": sha256(raw).hexdigest(),
                   "size_bytes": len(raw)}
        result = compare_imported_capture(raw, receipt=receipt)
        independent = result["stdlib_feedparser"]
        exact = result["v1_v2_same_input"]
        row.update({
            "status": "compared", "observed_at": observed_at,
            "https_tls_hostname_checked": True, "pinned_public_ip": True,
            "http_status": packet["status"], "content_type": packet["content_type"],
            "final_url": packet["final_url"], "original_body_sha256": receipt["sha256"],
            "original_body_size": len(raw), "same_exact_input_bytes": True,
            "v1_reference_blob_verified": exact["v1_parser_blob_verified"],
            "v1_extracted_count": exact["v1_extracted_count"],
            "v1_eligible_count": exact["v1_window_eligible"],
            "v2_eligible_count": exact["v2_window_eligible"],
            "v1_v2_matching_count": exact["matching_items"],
            "v1_only_hash_count": len(exact["v1_only"]),
            "v2_only_hash_count": len(exact["v2_only"]),
            "v1_v2_parser_alignment": exact["parser_alignment"],
            "feedparser_candidate_count": independent["feedparser_count"],
            "stdlib_candidate_count": independent["stdlib_count"],
            "feedparser_difference_count": (
                len(independent["missing_from_feedparser"]) +
                len(independent["extra_in_feedparser"])),
            "independent_parser_parity": independent["parity_passed"],
            "external_publisher_signature": False,
            "full_edition_or_delivery_comparable": False,
        })
    except Exception as exc:
        row.update({"status": "hold", "failure_class": _error_type(exc)})
    return row


def run() -> dict:
    rows = [probe(product, label, url) for product, label, url in SOURCES]
    complete = all(any(r["product"] == p and r["status"] == "compared"
                       for r in rows) for p in ("english", "arabic"))
    return {"schema": "aggregateit-v2-b34-runner-capture/1",
            "runner": "github-hosted-ubuntu", "dry_run": True,
            "source_count": len(rows), "results": rows,
            "english_arabic_capture_available": complete,
            "original_bytes_retained": False,
            "publisher_rights_cleared": False,
            "full_v1_v2_delivery_comparison": False,
            "operational_acceptance": "HOLD",
            "discord_sent": False, "database_mutated": False}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ns = ap.parse_args()
    report = run()
    dest = Path(ns.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print(json.dumps({"schema": report["schema"],
                      "languages_complete": report["english_arabic_capture_available"],
                      "source_status": [{"label": r["source_label"], "status": r["status"],
                                         "reason": r.get("failure_class")}
                                        for r in report["results"]]}))
    return 0 if report["english_arabic_capture_available"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
