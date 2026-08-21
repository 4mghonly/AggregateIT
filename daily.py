"""daily.py — end-of-day digest embed (Phase 4)."""
import os, json, requests
from datetime import datetime, timezone
from storage import SQLiteStore
import market

def main():
    wh = os.environ.get("DISCORD_WEBHOOK")
    if not wh: print("FATAL: DISCORD_WEBHOOK missing"); return
    store = SQLiteStore()
    rows = store.recent_all_events(hours=24)
    pulse = market.load_market_pulse() or {}
    macro = market.load_macro_pulse() or {}
    regime = market.compute_regime(macro) if macro else {}
    by_status = {}
    for r in rows: by_status[r.get("status", "NEW")] = by_status.get(r.get("status", "NEW"), 0) + 1
    rolls = {"bullish": 0, "neutral": 0, "bearish": 0}
    for r in rows:
        s = (r.get("sentiment") or "").lower()
        if s in rolls: rolls[s] += 1
    heads = sorted(rows, key=lambda x: -(x.get("last_updated") or 0))[:5]
    im = {i["name"]: i for i in macro.get("instruments", [])}
    spx = im.get("S&P 500", {})
    fields = [
        {"name": "📊 Events by status", "value": ", ".join("%s: %d" % (k, v) for k, v in sorted(by_status.items())) or "—", "inline": False},
        {"name": " Latest headlines", "inline": False,
         "value": "\n".join("%s — %s" % (datetime.fromtimestamp(r["last_updated"], timezone.utc).strftime("%H:%M"), (r.get("title") or "")[:70]) for r in heads) or "—"},
        {"name": " Sentiment", "value": "🟢 %d · ⚪ %d · 🔴 %d" % (rolls["bullish"], rolls["neutral"], rolls["bearish"]), "inline": True},
        {"name": "🏛️ S&P 500", "value": "%+.2f%%" % spx.get("pct", 0) if spx.get("pct") is not None else "—", "inline": True},
        {"name": "🎯 VIX", "value": regime.get("vix", "—"), "inline": True},
    ]
    embed = {"title": "📅 DAILY DIGEST — %s" % datetime.now(timezone.utc).strftime("%a %Y-%m-%d"),
             "color": 0x34495E, "fields": fields,
             "footer": {"text": "AggregateIT Intelligence Terminal"},
             "timestamp": datetime.now(timezone.utc).isoformat()}
    r = requests.post(wh, json={"embeds": [embed]})
    r.raise_for_status()
    print("✅ Daily digest delivered!")

if __name__ == "__main__":
    main()
