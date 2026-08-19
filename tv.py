"""TradingView US market universe + pulse.
Emulates the 'Load More' XHR loop of the TradingView market-movers page.
v3: fixed column mapping (volume idx 6, is_primary idx 7) + volume-aware validity gate."""
import os, json, time, argparse
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE_DIR, "data")
os.makedirs(DATA, exist_ok=True)

SCAN_URL = "https://scanner.tradingview.com/america/scan"
CHUNK = 1000
COLS = ["ticker", "description", "sector", "market_cap_calc",
        "change_percent", "relative_volume_10d_calc", "volume", "is_primary"]

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
    ticker = row.get("s", "").split(":")[-1]  # strip exchange prefix
    def g(i, default):
        return d[i] if len(d) > i and d[i] is not None else default
    return {"t": ticker, "c": g(1, ""), "s": g(2, "") or "US Market",
            "mcap": g(3, 0), "pct": g(4, 0), "relvol": g(5, 0),
            "vol": g(6, 0),
            "primary": bool(g(7, 1))}

def fetch_universe(post_fn=_post):
    """'Load More' until the end; primary listings only."""
    out = []; start = 0; total = 0
    while True:
        resp = post_fn({"columns": COLS, "options": {"lang": "en"}, "markets": ["america"],
                        "sort": {"sortBy": "market_cap_calc", "sortOrder": "desc"},
                        "range": [start, start + CHUNK]})
        total = resp.get("totalCount", 0)
        rows = resp.get("data", [])
        for r in rows:
            m = _row(r)
            if m["primary"]: out.append(m)
        start += CHUNK
        if not rows or start >= total: break
        time.sleep(0.75)
    return out, total

def _scan(post_fn, flt, sort, cap):
    try:
        resp = post_fn({"columns": COLS, "options": {"lang": "en"}, "markets": ["america"],
                        "filter": flt, "sort": {"sortBy": sort[0], "sortOrder": sort[1]},
                        "range": [0, cap * 3]})
        out = []
        for r in resp.get("data", []):
            m = _row(r)
            if m["primary"]: out.append(m)
            if len(out) >= cap: break
        return out
    except Exception as e:
        print("TV scan err:", type(e).__name__)
        return []

def fetch_movers(post_fn=_post, cap=300):
    movers = {}
    jobs = [
        ([{"left": "change_percent", "operation": "greater", "right": 4}], ("change_percent", "desc")),
        ([{"left": "change_percent", "operation": "less", "right": -4}], ("change_percent", "asc")),
        ([{"left": "relative_volume_10d_calc", "operation": "greater", "right": 2}], ("relative_volume_10d_calc", "desc")),
    ]
    for flt, sort in jobs:
        for m in _scan(post_fn, flt, sort, cap):
            movers[m["t"]] = {"pct": m["pct"], "relvol": m["relvol"], "mcap": m["mcap"]}
        time.sleep(0.5)
    return movers

def fetch_pulse(post_fn=_post, cap=20):
    """Session snapshot: mega-cap board + top gainers/losers + validity gate."""
    mega = []
    resp = post_fn({"columns": COLS, "options": {"lang": "en"}, "markets": ["america"],
                    "sort": {"sortBy": "market_cap_calc", "sortOrder": "desc"},
                    "range": [0, cap * 3]})
    for r in resp.get("data", []):
        m = _row(r)
        if m["primary"]: mega.append(m)
        if len(mega) >= cap: break
    gainers = _scan(post_fn, [{"left": "change_percent", "operation": "greater", "right": 3}], ("change_percent", "desc"), 5)
    losers = _scan(post_fn, [{"left": "change_percent", "operation": "less", "right": -3}], ("change_percent", "asc"), 5)
    # Valid if there is price movement OR real trading volume (market open)
    valid = any(abs(m["pct"]) > 0.005 or m.get("vol", 0) > 1000 for m in mega)
    return {"updated": time.time(), "valid": valid,
            "mega_caps": mega, "gainers": gainers, "losers": losers}

def save(name, obj):
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as f: json.dump(obj, f)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", action="store_true")
    ap.add_argument("--movers", action="store_true")
    ap.add_argument("--pulse", action="store_true")
    ap.add_argument("--search", nargs="+")
    args = ap.parse_args()

    if args.universe:
        try:
            uni, total = fetch_universe()
            save("tv_universe.json", {"updated": time.time(), "total": total, "rows": uni})
            print(f"TV UNIVERSE OK: {len(uni)} primary rows (totalCount {total})")
        except Exception as e:
            print("TV UNIVERSE FAIL:", type(e).__name__, str(e)[:120])

    if args.movers:
        try:
            mv = fetch_movers()
            save("movers.json", {"updated": time.time(), "movers": mv})
            print(f"TV MOVERS OK: {len(mv)} movers")
        except Exception as e:
            print("TV MOVERS FAIL:", type(e).__name__, str(e)[:120])

    if args.pulse:
        try:
            pulse = fetch_pulse()
            save("market_pulse.json", pulse)
            movers = {m["t"]: {"pct": m["pct"], "relvol": m["relvol"], "mcap": m["mcap"]}
                      for m in pulse["gainers"] + pulse["losers"]}
            save("movers.json", {"updated": pulse["updated"], "movers": movers})
            state = "OK" if pulse["valid"] else "INVALID (market likely closed)"
            print(f"TV PULSE {state}: {len(pulse['mega_caps'])} mega caps, "
                  f"{len(pulse['gainers'])} gainers, {len(pulse['losers'])} losers")
        except Exception as e:
            print("TV PULSE FAIL:", type(e).__name__, str(e)[:120])

    if args.search:
        q = " ".join(args.search).lower()
        p = os.path.join(DATA, "tv_universe.json")
        if not os.path.exists(p):
            print("No universe file yet. Run the refresh workflow first.")
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
