"""B115: compare actual V1 deterministic editorial functions and V2 on one capture.

Called inside the collector before publisher bytes leave memory. This is an
article-attempt comparison, NOT a full V1 scheduled edition or model comparison.
The public receipt contains hashes, counts and decision deltas, never text/HTML.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit
import json

from v2_article_body_gate import extract_body
from v2_b31_same_input_shadow import _git_blob, V1_MAIN_BLOB
from v2_b46_live_editorial import SOURCE_CATALOG, compile_captured_articles
from v2_evidence import canonical_article_url, _time
from v2_feed_items import extract_candidates

V1_ARABIC_EDITORIAL_BLOB = "2b72640dc1ac792c71afa7cdb5fa67146d2b11ef"


def _identity(url: str) -> str:
    return sha256(canonical_article_url(url).encode("utf8")).hexdigest()


def _legacy_english(rows: list[dict]):
    # main.py has import-time filesystem and SQLite setup; neutralize both.
    # Scoring, clustering, floor and selection limits are the original V1 code.
    with patch("os.makedirs"), patch("storage.SQLiteStore", return_value=None):
        import main
    scored = []
    for row in rows:
        item = dict(row, source_name=row["source_name"], source_type="rss",
                    url=row["article_url"], text=row["body"], ts=row["published_ts"],
                    matched_categories=[])
        item["title"] = row["title"]
        score, labels = main.score_item(item)
        if score > 0:
            item.update(score=score, matched_categories=labels)
            scored.append(item)
    scored.sort(key=lambda x: -x["score"])
    front = [x for x in scored if x["score"] >= main.FRONT_PAGE_FLOOR][:main.MAX_ANALYZE]
    # V1 writes a diagnostics JSON as a side effect; redirect it to a path that
    # cannot exist and whose failure the original function already tolerates.
    with patch.object(main, "CLUSTER_METRICS_FILE", str(Path(__file__).parent / "__b115_no_such_dir__" / "metrics.json")):
        clusters = main.cluster_events(front)
    def is_fin(c):
        ids = {key for x in c["items"] for key in x.get("keyword_ids", [])}
        return any(k.split("-")[0] in main.FIN_KEYWORD_PREFIXES for k in ids)
    reserved = [c for c in clusters if is_fin(c)][:main.FIN_RESERVED_SLOTS]
    others = [c for c in clusters if c not in reserved]
    chosen = (reserved + others[:main.MAX_EVENTS - len(reserved)])
    selected = {_identity(x["url"]) for c in chosen for x in c["items"]}
    decisions = {_identity(x["url"]): {"score":x["score"],
        "trigger_ids": x.get("keyword_ids",[]), "selected":_identity(x["url"]) in selected}
        for x in scored}
    return selected, decisions, len(clusters)


def _legacy_arabic(rows: list[dict], observed: datetime):
    import arabic_live_v2 as legacy

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return observed.astimezone(tz or timezone.utc)

    eligible = []
    for row in rows:
        # The original V1 region/relevance/impact/select routines, with the
        # same captured title and body lead and no inferred publisher country.
        source = {"id": row["source_id"], "name": row["source_name"],
                  "region": "global", "country": None, "language": "ar",
                  "affiliation": "unverified"}
        item = legacy._item(source, row["title"], row["body"][:900],
                            row["article_url"], row["published_ts"])
        if item is not None:
            eligible.append(item)
    with patch.object(legacy, "datetime", FrozenDateTime):
        selected = legacy.select(eligible, limit=13)
        scores = {_identity(x["url"]): round(legacy.impact_score(x), 3) for x in eligible}
    regions={_identity(x["url"]):x["region"] for x in eligible}
    return {_identity(x["url"]) for x in selected}, scores, len(eligible), regions


def compare_same_capture(feeds: list[dict], pages: list[dict], *, observed_at: str) -> dict:
    """One bounded immutable set of captured RSS/HTML bytes to both processors."""
    observed = datetime.fromisoformat(_time(observed_at)).astimezone(timezone.utc)
    if _git_blob("main.py") != V1_MAIN_BLOB or _git_blob("arabic_live_v2.py") != V1_ARABIC_EDITORIAL_BLOB:
        raise ValueError("v1_editorial_code_drift")
    if not isinstance(feeds, list) or not 2 <= len(feeds) <= 16 or not isinstance(pages, list) or len(pages) > 64:
        raise ValueError("unbounded_same_capture")
    feed_map = {}
    feed_receipts = []
    for feed in feeds:
        product, source_id, data = feed["product"], feed["source_id"], feed["body"]
        source = next((s for s in SOURCE_CATALOG.get(product, ()) if s["source_id"] == source_id), None)
        if source is None or not isinstance(data, bytes) or not 1 <= len(data) <= 1_000_000 or (product, source_id) in feed_map:
            raise ValueError("untrusted_frozen_feed")
        parsed = extract_candidates(data, feed_url=source["feed_url"],
                      observed_at=observed_at, max_age_hours=48, max_items=30, max_bytes=1_000_000)
        feed_map[product, source_id] = {(x["article_url"], x["title"], x["published_at"]) for x in parsed["items"]}
        feed_receipts.append({"product": product, "source_id": source_id,
                              "sha256": sha256(data).hexdigest(), "bytes": len(data)})
    if {p for p, _ in feed_map} != {"english", "arabic"}:
        raise ValueError("missing_bilingual_frozen_feeds")

    sanitized = []
    eligible_rows = {"english": [], "arabic": []}
    seen = set()
    for page in pages:
        product, source_id = page["product"], page["source_id"]
        html = page["html_bytes"]
        if ((product, source_id) not in feed_map or not isinstance(html, bytes)
                or not 1 <= len(html) <= 850000):
            raise ValueError("untrusted_frozen_article")
        if (page["article_url"], page["title"], page["published_at"]) not in feed_map[product, source_id]:
            raise ValueError("article_not_in_frozen_feed")
        unique = (product, _identity(page["article_url"]))
        if unique in seen:
            raise ValueError("duplicate_frozen_article")
        seen.add(unique)
        source = next(s for s in SOURCE_CATALOG[product] if s["source_id"] == source_id)
        if urlsplit(page["article_url"]).hostname not in source["hosts"]:
            raise ValueError("mismatched_publisher_host")
        try:
            body = extract_body(html, source_url=page["article_url"], language=source["language"])["original_text"]
            body_status = "EXTRACTED"
        except ValueError as exc:
            body = ""; body_status = str(exc)[:80]
        eligible_rows[product].append({"article_url": page["article_url"],
             "source_id": source_id, "source_name": source["publisher_id"],
             "title": page["title"], "body": body,
             "published_ts": datetime.fromisoformat(_time(page["published_at"])).timestamp()})
        sanitized.append({"product": product, "source_id": source_id,
            "identity_sha256": unique[1], "html_sha256": sha256(html).hexdigest(),
            "body_extraction": body_status})

    # V2 receives exactly these article bytes, including its prior rejects.
    # V1 receives exactly the same attempted articles after body extraction.
    replay = compile_captured_articles(pages, as_of=observed_at, slot_id=observed_at)
    products = {}
    for product in ("english", "arabic"):
        rows = eligible_rows[product]
        if product == "english":
            v1_selected, decisions, v1_clusters = _legacy_english(rows)
            v1_scores={key:value['score'] for key,value in decisions.items()}
            v1_scope = {"clusters": v1_clusters}
            v1_regions={}
        else:
            v1_selected, v1_scores, eligible, v1_regions = _legacy_arabic(rows, observed)
            v1_scope = {"eligible": eligible}
            decisions={}
        plan = replay["products"][product]["editorial_plan"]
        v2_scores = {_identity(x["evidence"]["source_url"]): x["priority"] for x in plan["items"]}
        v2_labels = {_identity(x["evidence"]["source_url"]): {"region":x["region"],"topic":x["topic"]}
                     for x in plan["items"]}
        v2_selected = set(v2_scores)
        products[product] = {
            "attempted_article_pages": len(rows),
            "v1_selected": len(v1_selected), "v2_selected": len(v2_selected),
            "both_selected": len(v1_selected & v2_selected),
            "selection_disagreement_count": len(v1_selected ^ v2_selected),
            "region_disagreements_on_common_items": sum(
                v1_regions[x]!=v2_labels[x]['region'] for x in v1_selected & v2_selected
                if x in v1_regions),
            "v1_only_sha256": sorted(v1_selected - v2_selected),
            "v2_only_sha256": sorted(v2_selected - v1_selected),
            "v1_scored_count": len(v1_scores),
            "v2_held_reasons": replay["products"][product]["held_reasons"],
            "v1_scope": v1_scope,
            "per_article": [{"identity_sha256": x["identity_sha256"],
                "v1_score": v1_scores.get(x["identity_sha256"]),
                "v1_keyword_ids": decisions.get(x["identity_sha256"],{}).get("trigger_ids",[]),
                "v1_region": v1_regions.get(x["identity_sha256"]),
                "v2_priority": v2_scores.get(x["identity_sha256"]),
                "v2_region": v2_labels.get(x["identity_sha256"],{}).get("region"),
                "v2_topic": v2_labels.get(x["identity_sha256"],{}).get("topic"),
                "v1_selected": x["identity_sha256"] in v1_selected,
                "v2_selected": x["identity_sha256"] in v2_selected,
                "body_extraction": x["body_extraction"]}
                for x in sanitized if x["product"] == product],
        }
    canonical = json.dumps({"feeds": sorted(feed_receipts, key=lambda x:(x["product"],x["source_id"])),
                            "articles": sorted(sanitized,key=lambda x:(x["product"],x["identity_sha256"]))},
                           sort_keys=True, separators=(",", ":")).encode("utf8")
    return {"schema": "aggregateit-v2-b115-same-capture/1",
        "observed_at": observed_at, "utc_date": observed.date().isoformat(),
        "input_manifest_sha256": sha256(canonical).hexdigest(),
        "feeds": feed_receipts, "articles": sanitized, "products": products,
        "source_capture_identity_verified": True,
        "v1_deterministic_functions_executed": True,
        "v2_actual_editorial_compiler_executed": True,
        "comparison_scope": "fetched_article_attempts_only_not_complete_v1_feeds",
        "unverified": ["v1_complete_scheduled_editorial","historical_state_and_prior_event_delta",
                       "v1_v2_model_analysis_translation_fallback","rendered_product_quality",
                       "authenticated_v1_delivery_receipts","independent_factual_accuracy"],
        "publisher_bytes_persisted": False, "discord_sent": False,
        "can_release": False}
