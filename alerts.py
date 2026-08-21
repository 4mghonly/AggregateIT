"""alerts.py — custom alert rules with per-rule webhook routing."""
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
        if rt == "importance" and a.get("importance") == r.get("value"): hits.append(r)
        elif rt == "ticker" and (r.get("value") or "").upper() in tickers: hits.append(r)
        elif rt == "keyword" and (r.get("value") or "").lower() in (a.get("event") or "").lower(): hits.append(r)
    return hits

def route_alerts(digest_items, rules=None):
    """Bucket alert lines by target webhook env name."""
    rules = rules or load_rules()
    buckets = {}
    for x in digest_items:
        for r in match_rules(x["analysis"], x["cluster"], rules):
            env = r.get("webhook_env") or "DISCORD_WEBHOOK"
            b = buckets.setdefault(env, {"lines": [], "mention": False})
            b["lines"].append("🚨 [%s:%s] %s" % (r.get("type"), r.get("value"), x["analysis"].get("event", "")[:100]))
            b["mention"] = b["mention"] or bool(r.get("mention"))
    return buckets
