"""weekly.py — weekly intelligence review posted to Discord."""
import os, requests
from datetime import datetime, timezone
from storage import SQLiteStore

def build_weekly(store, hours=168):
    rows = store.recent_all_events(hours=hours, limit=500)
    if not rows: return None
    by_status = {}; entities = {}
    for r in rows:
        st = r.get("status", "NEW")
        by_status[st] = by_status.get(st, 0) + 1
        entities[r.get("entity", "GEN")] = entities.get(r.get("entity", "GEN"), 0) + 1
    confirmed = by_status.get("CONFIRMED", 0)
    top_entities = sorted(entities.items(), key=lambda x: -x[1])[:6]
    top_conf = sorted(rows, key=lambda r: -(r.get("confidence") or 0))[:5]
    return {"title": "📅 Weekly Intelligence Review", "color": 0x9B59B6,
            "description": f"{len(rows)} events tracked over the last {hours // 24} days · {confirmed} confirmed",
            "fields": [
                {"name": "📊 Events by status", "value": ", ".join(f"{k}: {v}" for k, v in sorted(by_status.items())) or "—", "inline": False},
                {"name": "🔥 Most active entities", "value": ", ".join(f"{k} ({v})" for k, v in top_entities) or "—", "inline": False},
                {"name": "✅ Highest-confidence events",
                 "value": "\n".join(f"• {(r.get('title') or '')[:70]} — {r.get('confidence')}%" for r in top_conf) or "—", "inline": False}],
            "footer": {"text": "AggregateIT Intelligence Terminal"},
            "timestamp": datetime.now(timezone.utc).isoformat()}

def main():
    wh = os.environ.get("DISCORD_WEBHOOK")
    if not wh:
        print("FATAL: DISCORD_WEBHOOK secret is not set."); return
    embed = build_weekly(SQLiteStore())
    if not embed:
        print("No events this week - skipping."); return
    r = requests.post(wh, json={"embeds": [embed]})
    r.raise_for_status()
    print("✅ Weekly review delivered!")

if __name__ == "__main__":
    main()
