"""TradingView US market universe + movers.
Emulates the 'Load More' XHR loop of
https://www.tradingview.com/markets/stocks-usa/market-movers-all-stocks/
by paging the page's own scanner backend until totalCount is reached."""
import os, json, time, argparse
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE_DIR, "data")
os.makedirs(DATA, exist_ok=True)

SCAN_URL = "https://scanner.tradingview.com/america/scan"
CHUNK = 1000
COLS = ["ticker", "description", "sector", "market_cap_calc",
        "change_percent", "relative_volume_10d_calc", "volume"]

def _post(body):
    for attempt in (1, 2):
        try:
            r = requests.post(SCAN_URL, json=body, timeout=30,
                              headers={"User-Agent": "Mozilla/5.0 (personal research)"})
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt == 2: raise
            time.sleep(2)

def _row(row):
    d = row.get("d", [])
    return {"t": row.get("s", ""), "c": d[0] or "", "s": d[1] or "US Market",
            "mcap": d[2] or 0, "pct": d[3] or 0, "relvol": d[4] or 0, "vol": d[5] or 0}

def fetch_universe(post_fn=_post):
    """'Load More' until the end: page by CHUNK until totalCount reached."""
    out = []; start = 0; total = 0
    while True:
        resp = post_fn({"columns": COLS, "options": {"lang": "en"}, "markets": ["america"],
                        "sort": {"sortBy": "market_cap_calc", "sortOrder": "desc"},
                        "range": [start, start + CHUNK]})
        total = resp.get("totalCount", 0)
        rows = resp.get("data", [])
        out += [_row(r) for r in rows]
        start += CHUNK
        if not rows or start >= total: break
        time.sleep(0.75)  # politeness
    return out, total

def fetch_movers(post_fn=_post, cap=300):
    """Today's gainers / losers / unusual volume = 'the market is voting'."""
    movers = {}
    jobs = [
        ([{"left": "change_percent", "operation": "greater", "right": 4}], ("change_percent", "desc")),
        ([{"left": "change_percent", "operation": "less", "right": -4}], ("change_percent", "asc")),
        ([{"left": "relative_volume_10d_calc", "operation": "greater", "right": 2}], ("relative_volume_10d_calc", "desc")),
    ]
    for flt, sort in jobs:
        try:
            resp = post_fn({"columns": COLS, "options": {"lang": "en"}, "markets": ["america"],
                            "filter": flt, "sort": {"sortBy": sort[0], "sortOrder": sort[1]},
                            "range": [0, cap]})
            for r in resp.get("data", []):
                m = _row(r); movers[m["t"]] = {"pct": m["pct"], "relvol": m["relvol"], "mcap": m["mcap"]}
        except Exception as e:
            print("TV movers scan err:", type(e).__name__)
        time.sleep(0.5)
    return movers

def save(name, obj):
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as f: json.dump(obj, f)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", action="store_true")
    ap.add_argument("--movers", action="store_true")
    ap.add_argument("--search", nargs="+")
    args = ap.parse_args()

    if args.universe:
        try:
            uni, total = fetch_universe()
            save("tv_universe.json", {"updated": time.time(), "total": total, "rows": uni})
            print(f"TV UNIVERSE OK: {len(uni)} rows (totalCount {total})")
        except Exception as e:
            print("TV UNIVERSE FAIL:", type(e).__name__, str(e)[:120])

    if args.movers:
        try:
            mv = fetch_movers()
            save("movers.json", {"updated": time.time(), "movers": mv})
            print(f"TV MOVERS OK: {len(mv)} movers")
        except Exception as e:
            print("TV MOVERS FAIL:", type(e).__name__, str(e)[:120])

    if args.search:
        q = " ".join(args.search).lower()
        p = os.path.join(DATA, "tv_universe.json")
        if not os.path.exists(p):
            print("No universe file yet. Run the 'TradingView Universe Refresh' workflow first.")
            return
        uni = json.load(open(p, encoding="utf-8"))["rows"]
        pm = os.path.join(DATA, "movers.json")
        mv = json.load(open(pm, encoding="utf-8"))["movers"] if os.path.exists(pm) else {}
        hits = [r for r in uni if q in r["t"].lower() or q in r["c"].lower()][:20]
        if not hits: print(f"No matches for '{q}'.")
        for r in hits:
            flag = " 🔥 MOVER" if r["t"] in mv else ""
            print(f"{r['t']:8} | {r['c'][:36]:38} | {str(r['s'])[:16]:16} | mcap {r['mcap']/1e9:8.1f}B | {r['pct']:+6.2f}% | relvol {r['relvol']:5.2f}{flag}")

if __name__ == "__main__":
    main()
