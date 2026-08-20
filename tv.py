"""TradingView US market universe + pulse.
v6: session-aware labeling, client-side mover sorting, stock-only filtering."""
import os, json, time, argparse
import requests
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE_DIR, "data")
os.makedirs(DATA, exist_ok=True)

SCAN_URL = "https://scanner.tradingview.com/america/scan"
CHUNK = 1000
COLS = ["ticker", "description", "sector", "market_cap_calc", "change_percent",
        "relative_volume_10d_calc", "volume", "is_primary", "change", "close", "type"]

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
    data = dict(zip(COLS, d))
    ticker = row.get("s", "").split(":")[-1]
    pct = data.get("change_percent") or 0
    chg = data.get("change") or 0
    cls = data.get("close") or 0
    if pct == 0 and chg and cls and (cls - chg) != 0:
        pct = (chg / (cls - chg)) * 100
    return {
        "t": ticker,
        "c": data.get("description") or ticker,
        "s": data.get("sector") or "US Market",
        "mcap": data.get("market_cap_calc") or 0,
        "pct": pct,
        "relvol": data.get("relative_volume_10d_calc") or 0,
        "vol": data.get("volume") or 0,
        "primary": bool(data.get("is_primary", 1)),
        "type": (data.get("type") or "stock"),
    }

def _ok(m):
    """Primary listing AND common stock (no ETFs/funds/warrants)."""
    return m["primary"] and m.get("type", "stock") == "stock"

def us_session_open(ts=None):
    """Mon-Fri 13:30-20:00 UTC (ignores holidays; acceptable for POC)."""
    dt = datetime.fromtimestamp(ts or time.time(), timezone.utc)
    if dt.weekday() > 4: return False
    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elapsed = dt - midnight
    return timedelta(hours=13, minutes=30) <= elapsed < timedelta(hours=20)

def fetch_universe(post_fn=_post):
    out = []; start = 0; total = 0
    while True:
        resp = post_fn({"columns": COLS, "options": {"lang": "en"}, "markets": ["america"],
                        "sort": {"sortBy": "market_cap_calc", "sortOrder": "desc"},
                        "range": [start, start + CHUNK]})
        total = resp.get("totalCount", 0)
        rows = resp.get("data", [])
        for r in rows:
            m = _row(r)
            if _ok(m): out.append(m)
        start += CHUNK
        if not rows or start >= total: break
        time.sleep(0.75)
    return out, total

def _top(post_fn, sort, cap, pred):
    try:
        resp = post_fn({"columns": COLS, "options": {"lang": "en"}, "markets": ["america"],
                        "sort": {"sortBy": sort[0], "sortOrder": sort[1]}, "range": [0, cap * 4]})
        out = []
        for r in resp.get("data", []):
            m = _row(r)
            if _ok(m) and pred(m): out.append(m)
            if len(out) >= cap: break
        return out
    except Exception as e:
        print("TV scan err:", type(e).__name__)
        return []

def fetch_movers(post_fn=_post, cap=300):
    movers = {}
    def add(m): movers[m["t"]] = {"pct": m["pct"], "relvol": m["relvol"], "mcap": m["mcap"]}
    for m in _top(post_fn, ("change_percent", "desc"), cap, lambda x: x["pct"] >= 4): add(m)
    for m in _top(post_fn, ("change_percent", "asc"), cap, lambda x: x["pct"] <= -4): add(m)
    for m in _top(post_fn, ("relative_volume_10d_calc", "desc"), cap, lambda x: x["relvol"] >= 2): add(m)
    return movers

def fetch_pulse(post_fn=_post, cap=20):
    """Session snapshot with honest labeling and client-side mover sorting."""
    mega = []
    resp = post_fn({"columns": COLS, "options": {"lang": "en"}, "markets": ["america"],
                    "sort": {"sortBy": "market_cap_calc", "sortOrder": "desc"},
                    "range": [0, cap * 3]})
    for r in resp.get("data", []):
        m = _row(r)
        if _ok(m): mega.append(m)
        if len(mega) >= cap: break
    # Movers: pool = most-traded stocks, then sort CLIENT-side on computed pct
    pool = _top(post_fn, ("volume", "desc"), 400, lambda x: x.get("vol", 0) > 0)
    gainers = sorted([m for m in pool if m["pct"] > 0], key=lambda x: -x["pct"])[:5]
    losers = sorted([m for m in pool if m["pct"] < 0], key=lambda x: x["pct"])[:5]
    sig = {}
    def add_sig(m): sig[m["t"]] = {"pct": m["pct"], "relvol": m["relvol"], "mcap": m["mcap"]}
    for m in _top(post_fn, ("change_percent", "desc"), 150, lambda x: x["pct"] >= 3): add_sig(m)
    for m in _top(post_fn, ("change_percent", "asc"), 150, lambda x: x["pct"] <= -3): add_sig(m)
    for m in _top(post_fn, ("relative_volume_10d_calc", "desc"), 150, lambda x: x["relvol"] >= 2): add_sig(m)
    valid = any(abs(m["pct"]) > 0.005 for m in mega)
    return {"updated": time.time(), "valid": valid, "session_open": us_session_open(),
            "mega_caps": mega, "gainers": gainers, "losers": losers, "sig": sig}

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
            print(f"TV UNIVERSE OK: {len(uni)} primary stock rows (totalCount {total})")
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
            save("movers.json", {"updated": pulse["updated"], "movers": pulse.get("sig", {})})
            if not pulse["valid"]:
                state = "INVALID (no reliable data)"
            elif pulse["session_open"]:
                state = "OK (LIVE session)"
            else:
                state = "OK (previous session data)"
            print(f"TV PULSE {state}: {len(pulse['mega_caps'])} mega caps, "
                  f"{len(pulse['gainers'])} gainers, {len(pulse['losers'])} losers, "
                  f"{len(pulse.get('sig', {}))} significant movers")
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
