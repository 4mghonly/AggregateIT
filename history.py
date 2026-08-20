"""history.py — searchable event history + timelines from state.db."""
import os, json, argparse
from datetime import datetime, timezone
from storage import SQLiteStore

def fmt_ts(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def search_events(store, query="", ticker="", hours=168, limit=20):
    rows = store.recent_all_events(hours=hours, limit=500)
    q = (query or "").lower(); t = (ticker or "").upper()
    out = []
    for ev in rows:
        if t and t not in (ev.get("title") or "").upper() and t not in (ev.get("triggers_json") or "").upper() and t != (ev.get("entity") or "").upper():
            continue
        if q and q not in (ev.get("title") or "").lower() and q not in (ev.get("assessment") or "").lower():
            continue
        out.append(ev)
        if len(out) >= limit: break
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", nargs="+")
    ap.add_argument("--ticker")
    ap.add_argument("--hours", type=int, default=168)
    args = ap.parse_args()
    store = SQLiteStore()
    rows = search_events(store, " ".join(args.query or []), args.ticker or "", args.hours)
    if not rows:
        print("No events matched."); return
    for ev in rows:
        tl = store.get_event_timeline(ev["event_id"])
        print(f"\n[{ev.get('status', 'NEW')}] {ev.get('title', '')}")
        print(f"  entity={ev.get('entity')} sev={ev.get('severity')} conf={ev.get('confidence')} "
              f"sources={ev.get('source_count')} first={fmt_ts(ev['first_seen'])} updated={fmt_ts(ev['last_updated'])}")
        print(f"  assessment: {(ev.get('assessment') or '')[:200]}")
        for t in tl[-4:]:
            print(f"    {fmt_ts(t['ts'])} - {t['type']}")

if __name__ == "__main__":
    main()
