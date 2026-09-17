"""Conservative event analysis used only when the configured LLM is unavailable."""
import re


def build(cluster, prior, reason, valid_tickers, social_types):
    first = cluster["items"][0]
    title = (first.get("title") or "Untitled event").strip()[:300]
    text = " ".join((item.get("title", "") + " " + item.get("text", ""))
                    for item in cluster["items"])
    low = text.lower()
    event_type = "other"
    if any(word in low for word in ("cyber", "malware", "ransomware", "vulnerability", "cve-")):
        event_type = "security"
    elif any(word in low for word in ("central bank", "federal reserve", "inflation", "interest rate", "gdp")):
        event_type = "macro"
    elif any(word in low for word in ("war", "missile", "sanction", "ceasefire", "military")):
        event_type = "geopolitical"
    elif any(word in low for word in ("earnings", "revenue", "profit", "guidance")):
        event_type = "earnings"
    elif any(word in low for word in ("regulator", "regulation", "lawsuit", "sec ", "antitrust")):
        event_type = "regulation"
    elif any(word in low for word in ("shares", "stock", "market", "futures", "yield", "bitcoin")):
        event_type = "market_move"

    social_only = all(item.get("source_type") in social_types for item in cluster["items"])
    source_count = int(cluster.get("independent_sources", 0))
    corroboration = ("multi-source" if source_count >= 2 and not social_only
                     else "single-source" if source_count else "none")
    tickers = sorted({match.group(1).upper() for match in re.finditer(r"\$([A-Za-z]{1,6})\b", text)
                      if match.group(1).upper() in valid_tickers})[:10]
    return {
        "event": title,
        "event_type": event_type,
        "facts": [title + " [1]"],
        "assessment": "Automated fallback: configured source and keyword rules matched this event; no unsupported inference was added.",
        "what_changed": "Additional source coverage was detected." if prior else "A newly matched event was detected.",
        "importance": "Medium" if first.get("score", 0) >= 8 else "Low",
        "confidence": 20 if social_only else (45 if source_count >= 2 else 30),
        "sentiment": "na",
        "entities": [cluster["entity"]] if cluster.get("entity") else [],
        "tickers": tickers,
        "evidence": [title + " [1]"],
        "corroboration": corroboration,
        "source_reliability": "Low" if social_only else "Medium",
        "gaps": ["LLM unavailable: " + (reason or "unknown")[:160],
                 "Requires analyst review before escalation."],
        "claims": [{"claim": title, "indices": [1]}],
        "analysis_mode": "deterministic_fallback",
    }
