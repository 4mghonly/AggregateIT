"""B5 experimental deterministic layout admission, not a raster renderer.

Three Arabic command-brief frames and two English Gazette pages remain fixed.
Overflow is explicitly withheld, never cropped or silently moved across products.
"""
from __future__ import annotations

import hashlib

from v2_editorial import PAGE_COUNTS

REGION_PAGE_AR = {
    "gcc": 0, "oman": 0,
    "iran": 1, "turkey": 1, "iraq": 1, "yemen": 1,
    "levant": 1, "palestine_israel": 1, "jordan": 1,
    "egypt": 2, "sudan": 2, "sahel": 2, "north_africa": 2,
    "pakistan": 2, "afghanistan": 2, "horn": 2, "somalia": 2,
}
EN_FINANCE_PAGE = {"markets", "finance", "macro", "energy"}
PAGE_CARD_CAP = {"arabic": (4, 6, 6), "english": (6, 6)}
PAGE_TEXT_CAP = {"arabic": (760, 1000, 1000), "english": (1200, 1200)}
PAGE_LABELS = {
    "arabic": ("الإمارات والخليج", "التطورات الإقليمية", "المسرح الإقليمي الممتد"),
    "english": ("SECURITY & GEOPOLITICS", "MARKETS & ECONOMY"),
}
STYLE = {
    "arabic": {
        "canvas": "3840x2160", "direction": "rtl",
        "background": "#101820", "card": "#1C2B35", "ink": "#F4F1E8",
        "accent": "#B69B6E", "font_preference": "Siraj Noir",
    },
    "english": {
        "canvas": "2480x3508", "direction": "ltr",
        "background": "#F5F0E6", "card": "#FFFFFF", "ink": "#24211D",
        "accent": "#783C35", "font_preference": "DejaVu Sans",
    },
}


def layout_plan(plan: dict, ledger) -> dict:
    if not isinstance(plan, dict) or plan.get("schema") != "aggregateit-editorial-plan/1":
        raise ValueError("untrusted_editorial_contract")
    product = plan.get("product")
    if product not in PAGE_COUNTS or plan.get("page_count") != PAGE_COUNTS[product]:
        raise ValueError("wrong_product_page_budget")
    if plan.get("delivery_authorized") is not False or plan.get("synthetic_or_unverified") is not True:
        raise ValueError("non_isolated_editorial_payload")
    if not isinstance(plan.get("items"), list) or len(plan["items"]) > 30:
        raise ValueError("invalid_items")
    pages = [
        {"page_number": i+1, "heading": heading, "items": [],
         "characters": 0, "cards_limit": PAGE_CARD_CAP[product][i],
         "character_limit": PAGE_TEXT_CAP[product][i]}
        for i, heading in enumerate(PAGE_LABELS[product])
    ]
    omitted = []
    seen = set()
    for item in plan["items"]:
        try:
            event_id = item["event_id"]
            version_id = item["version_id"]
            evidence = item["evidence"]
            excerpt_id = evidence["excerpt_id"]
            quote = evidence["quote"]
            if event_id in seen or not isinstance(quote, str):
                raise ValueError("duplicate_or_invalid_item")
            seen.add(event_id)
            history = ledger._events.get(event_id)
            excerpt = ledger._excerpts.get(excerpt_id)
            if not history or history[-1]["version_id"] != version_id or excerpt is None:
                raise ValueError("stale_or_missing_evidence")
            if quote != excerpt["literal"] or hashlib.sha256(quote.encode("utf-8")).hexdigest() != evidence["literal_sha256"]:
                raise ValueError("quote_integrity_mismatch")
            if evidence["claim_id"] not in history[-1]["claim_ids"] or excerpt_id not in ledger._claims[evidence["claim_id"]]["excerpt_ids"]:
                raise ValueError("source_linkage_mismatch")
            source = ledger._source_revisions[(excerpt["source_id"], excerpt["revision_id"])]
            if (evidence["source_url"] != source["canonical_url"] or
                    evidence["source_id"] != source["source_id"] or
                    evidence["revision_id"] != source["revision_id"] or
                    evidence["article_id"] != source["article_id"]):
                raise ValueError("source_url_or_identity_mismatch")
            if excerpt["original_language"].split("-")[0] != plan["language"]:
                raise ValueError("untranslated_quote")
            if product == "arabic":
                page_idx = 0 if item["is_uae"] else REGION_PAGE_AR[item["region"]]
            else:
                page_idx = 1 if item["topic"] in EN_FINANCE_PAGE else 0
            page = pages[page_idx]
            if len(page["items"]) >= page["cards_limit"]:
                omitted.append({"event_id": event_id, "reason": "page_card_limit", "page": page_idx+1})
                continue
            if len(quote) > 240 or page["characters"] + len(quote) > page["character_limit"]:
                omitted.append({"event_id": event_id, "reason": "page_text_budget", "page": page_idx+1})
                continue
            page["items"].append({
                "event_id": event_id, "version_id": version_id,
                "quote": quote, "excerpt_id": excerpt_id,
                "source_url": evidence["source_url"], "source_id": evidence["source_id"],
                "source_date": evidence["source_date"],
                "change": item["change"], "status": item["reporting_status"],
                "region": item["region"], "subject_country": item["subject_country"],
            })
            page["characters"] += len(quote)
        except (KeyError, TypeError, IndexError) as exc:
            raise ValueError("invalid_layout_input") from exc
    return {
        "schema": "aggregateit-layout-contract/1",
        "product": product, "slot_id": plan["slot_id"],
        "page_count": len(pages), "pages": pages,
        "style": STYLE[product],
        "omissions": omitted, "rendered_items": sum(len(p["items"]) for p in pages),
        "review_status": "synthetic_layout_contract_only",
        "scaled_image_qa": "not_run",
        "delivery_authorized": False,
    }
