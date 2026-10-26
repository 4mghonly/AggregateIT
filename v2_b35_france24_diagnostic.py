"""B35 single-fetch France24 Arabic V1/V2 parser difference classifier.

This is a diagnostic, not a parser fix. It never preserves titles, links,
raw publisher bytes, article bodies, or text in the public report.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET

from arabic_newsletter.core import canonical
from v2_b31_same_input_shadow import (
    _arabic_v1, _fingerprint, compare_exact_input,
)
from v2_feed_items import _text, _atom_link, extract_candidates
from v2_feed_probe import _date, _url_safe
from v2_secure_transport import pinned_https_fetch

SOURCE = "https://www.france24.com/ar/rss"
MAX_BYTES = 1_000_000
CAP = 35


def _xml_decisions(raw: bytes, now: datetime) -> tuple[list[dict], dict]:
    """Re-evaluate V2 admission conditions for each XML entry in feed order."""
    root = ET.fromstring(raw)
    kind = root.tag.rsplit("}", 1)[-1].lower()
    if kind == "rss":
        entries = root.findall("./channel/item")
    elif kind == "feed":
        entries = [e for e in root if e.tag.rsplit("}", 1)[-1].lower() == "entry"]
    elif kind == "rdf":
        entries = [e for e in root if e.tag.rsplit("}", 1)[-1].lower() == "item"]
    else:
        raise ValueError("unsupported_feed_root")
    seen = set()
    accepted = 0
    rejected = {"missing_title": 0, "invalid_link": 0,
                "missing_or_stale_date": 0, "duplicate_link": 0,
                "over_budget": 0}
    mapped = []
    for entry in entries:
        title = re.sub(r"\s+", " ", unescape(_text(entry, "title"))).strip()
        url = _atom_link(entry) if kind == "feed" else _text(entry, "link")
        date_text = (_text(entry, "published") or _text(entry, "updated")
                     or _text(entry, "pubdate") or _text(entry, "date"))
        stamp = _date(date_text)
        decision = "admitted"
        if not 5 <= len(title) <= 300:
            decision = "missing_title"
        elif not url:
            decision = "invalid_link"
        else:
            try:
                _url_safe(url)
            except ValueError:
                decision = "invalid_link"
        if decision == "admitted":
            if stamp is None or not -300 <= (now - stamp).total_seconds() <= 72 * 3600:
                decision = "missing_or_stale_date"
            elif url in seen:
                decision = "duplicate_link"
            else:
                seen.add(url)
                if accepted >= CAP:
                    decision = "over_budget"
                else:
                    accepted += 1
        if decision != "admitted":
            rejected[decision] += 1
        mapped.append({"canonical_url": canonical(url) if url else "",
                       "literal_url": url, "title": title,
                       "timestamp": stamp, "decision": decision})
    return mapped, rejected


def diagnose_bytes(raw: bytes, *, observed_at: str) -> dict:
    """Compare actual legacy parser vs V2 on unchanged bytes, then classify drift."""
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= MAX_BYTES:
        raise ValueError("invalid_feed_bytes")
    now = _date(observed_at)
    if now is None:
        raise ValueError("invalid_observed_at")
    result = compare_exact_input(raw, feed_url=SOURCE, observed_at=now.isoformat(),
                                 product="arabic")
    v2 = extract_candidates(raw, feed_url=SOURCE, observed_at=now.isoformat(),
                            max_items=CAP, max_age_hours=72, max_bytes=MAX_BYTES)
    xml_rows, rejects = _xml_decisions(raw, now)
    if rejects != v2["rejected"] or sum(r["decision"] == "admitted" for r in xml_rows) != len(v2["items"]):
        raise ValueError("diagnostic_rejection_counts_disagree")
    v2_urls = {r["article_url"]: r for r in v2["items"]}
    v1_only = set(result["v1_only"])
    finding_rows = []
    for legacy in _arabic_v1(raw, SOURCE):
        when = legacy.get("published")
        if not isinstance(when, (float, int)) or isinstance(when, bool):
            continue
        when_dt = datetime.fromtimestamp(when, tz=timezone.utc)
        url, title = legacy.get("url", ""), legacy.get("title", "")
        if not -300 <= (now - when_dt).total_seconds() <= 72 * 3600:
            continue
        try:
            _url_safe(url)
        except ValueError:
            continue
        if not isinstance(title, str) or not 5 <= len(title.strip()) <= 300:
            continue
        key = _fingerprint(url, title, when_dt)
        if key not in v1_only:
            continue
        matched_v2 = v2_urls.get(url)
        matches = [r for r in xml_rows if r["canonical_url"] == url]
        # A URL can have an admitted entry and a later rejected duplicate.
        # Resolve an exact duplicate title/time before comparing to the
        # admitted entry, or the latter masks the actual rejection cause.
        exact_duplicates = [r for r in matches if r["decision"] == "duplicate_link"
                            and r["title"] == title and r["timestamp"] == when_dt]
        if exact_duplicates:
            classification = "duplicate_link"
            details = {"matching_xml_entries": len(matches),
                       "matched_rejected_duplicate": True}
        elif matched_v2 is not None:
            v2_dt = _date(matched_v2["published_at"])
            classification = "identity_title_or_timestamp_mismatch"
            details = {"title_same": title == matched_v2["title"],
                       "timestamp_same": when_dt == v2_dt}
        elif matches:
            failures = [r["decision"] for r in matches if r["decision"] != "admitted"]
            classification = failures[0] if failures else "canonicalization_or_identity_mismatch"
            details = {"matching_xml_entries": len(matches),
                       "v2_raw_url_same": any(r["literal_url"] == url for r in matches),
                       "v1_xml_title_equal": any(r["title"] == title for r in matches),
                       "v1_xml_timestamp_equal": any(r["timestamp"] == when_dt for r in matches)}
        else:
            classification = "no_equivalent_xml_link"
            details = {"matching_xml_entries": 0}
        finding_rows.append({"v1_item_fingerprint": key,
                             "classification": classification, **details})
    if len(finding_rows) != len(v1_only):
        raise ValueError("incomplete_drift_classification")
    return {
        "schema": "aggregateit-v2-b35-france24-diagnostic/1",
        "source": "france24-ar", "feed_url": SOURCE,
        "observed_at": now.isoformat(),
        "source_sha256": sha256(raw).hexdigest(),
        "source_bytes": len(raw),
        "v1_reference_blob_verified": result["v1_parser_blob_verified"],
        "v1_eligible": result["v1_window_eligible"],
        "v2_eligible": result["v2_window_eligible"],
        "matching_count": result["matching_items"],
        "v1_only": len(v1_only), "v2_only": len(result["v2_only"]),
        "v2_rejected": rejects,
        "difference_classifications": finding_rows,
        "reproduced_prior_one_item_difference": (
            len(v1_only) == 1 and not result["v2_only"]),
        "parity_on_new_capture": result["parser_alignment"],
        "historical_b34_bytes_replayed": False,
        "no_raw_feed_artifact": True, "article_rights_verified": False,
        "discord_sent": False, "production_changed": False,
        "can_publish": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    packet = pinned_https_fetch(
        SOURCE, timeout=9, max_bytes=MAX_BYTES, max_redirects=1,
        headers={"Accept": "application/rss+xml, application/xml, text/xml"})
    body = packet["body"]
    report = diagnose_bytes(body, observed_at=datetime.now(timezone.utc).isoformat())
    report["http_status"] = packet["status"]
    report["tls_host_validation"] = True
    report["same_host_redirect_only"] = True
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"classification_codes": [r["classification"] for r in report["difference_classifications"]],
                      "new_capture_parity": report["parity_on_new_capture"],
                      "v1_only": report["v1_only"], "v2_only": report["v2_only"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
