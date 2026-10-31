"""Bounded additive publisher catalog sourced from V2 registry, not inferred identities.

Only approved feed IDs with native-language article bodies are included. The
existing primary/fallback pair stays first for compatibility. Each additional
publisher is checked against the registry at import time.
"""
import json
from pathlib import Path
from urllib.parse import urlsplit

REGISTRY=Path(__file__).resolve().parent/"config"/"v2"/"source_registry.json"
ENGLISH_IDS=("en-004","en-018","en-019","en-020","en-021","en-022")
ARABIC_IDS=("ar-s004","ar-s026","ar-s033","ar-s039","ar-s045","ar-s048","ar-s068","ar-s081","ar-s095")

def extra_sources(product, existing=()):
    if product not in ("english","arabic"):
        raise ValueError("invalid_product")
    registry=json.loads(REGISTRY.read_text(encoding="utf8"))
    records={row["id"]:row for row in registry["sources"]}
    selected=ENGLISH_IDS if product=="english" else ARABIC_IDS
    known_urls={row["feed_url"] for row in existing}
    known_ids={row["source_id"] for row in existing}
    result=[]
    for source_id in selected:
        row=records.get(source_id)
        if row is None or row.get("entrypoint_type")!="feed" or row.get("stream")!=product:
            raise ValueError("invalid_registry_source")
        if row.get("language")!=("en" if product=="english" else "ar"):
            continue
        url=row["entrypoint"]
        parts=urlsplit(url)
        host=row.get("host_candidate","").lower().removeprefix("www.")
        if parts.scheme!="https" or not parts.hostname or not host or "." not in host:
            raise ValueError("invalid_registry_source_url")
        if url in known_urls or source_id in known_ids:
            continue
        # Source hostname is an explicit registry value; no arbitrary redirect host.
        hosts=frozenset((host,"www."+host))
        result.append({"publisher_id":source_id,"source_id":source_id,
                       "feed_url":url,"hosts":hosts,"language":row["language"]})
        known_urls.add(url)
        known_ids.add(source_id)
    return tuple(result)
