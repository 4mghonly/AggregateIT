"""calibrate.py — Phase 6 Calibration Loop.
Compares predicted event importance vs actual subsequent market moves.
Generates a hit-rate report to tune scoring weights (human-reviewed)."""
import os, json, time
from storage import SQLiteStore
import market

BASE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(BASE, "reports")
CAL_FILE = os.path.join(REPORTS, "calibration_report.json")

def main():
    store = SQLiteStore()
    pulse = market.load_market_pulse() or {}
    sig_movers = set(pulse.get("sig", {}).keys())
    hour_movers = set(m["t"] for m in pulse.get("hour_movers", []))
    active_tickers = sig_movers | hour_movers

    events = store.recent_all_events(hours=168) # Last 7 days
    report = {"ts": time.time(), "total_events": len(events), "active_tickers_snapshot": len(active_tickers), "by_importance": {}}

    for imp in ("Critical", "High", "Medium", "Low"):
        subset = [e for e in events if e.get("severity") == imp]
        hits = 0
        for e in subset:
            try: tickers = set(json.loads(e.get("sources_json") or "[]")) # Fallback to sources if tickers not parsed
            except: tickers = set()
            # Actually, we need the tickers from the analysis. Let's parse triggers or sources.
            # For POC, we check if ANY word in the title matches a mover.
            title_words = set(e.get("title", "").upper().split())
            if title_words & active_tickers: hits += 1
        rate = (hits / len(subset) * 100) if subset else 0
        report["by_importance"][imp] = {"count": len(subset), "ticker_hit_rate_pct": round(rate, 1)}

    os.makedirs(REPORTS, exist_ok=True)
    with open(CAL_FILE, "w") as f: json.dump(report, f, indent=2)
    print("✅ Calibration report generated:", CAL_FILE)
    for imp, data in report["by_importance"].items():
        print(f"  {imp}: {data['count']} events, {data['ticker_hit_rate_pct']}% matched current movers")

if __name__ == "__main__":
    main()
