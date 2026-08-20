"""alerts.py — custom alert rules evaluated over analyzed events."""
import os, json

BASE = os.path.dirname(os.path.abspath(__file__))

def load_rules():
    try:
        with open(os.path.join(BASE, "config", "alerts.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"mention_role": None, "rules": []}

def match_rules(a, cluster, rules):
    hits = []
    tickers = [t.upper() for t in (a.get("tickers") or [])]
    for r in rules.get("rules", []):
        rt = r.get("type")
        if rt == "importance" and a.get("importance") == r.get("value"):
            hits.append(r)
        elif rt == "ticker" and (r.get("value") or "").upper() in tickers:
            hits.append(r)
        elif rt == "keyword" and (r.get("value") or "").lower() in (a.get("event") or "").lower():
            hits.append(r)
    return hits
