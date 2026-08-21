"""TradingView universe + pulse + macro. v19: 1-hour movers computed against
the previous snapshot (persisted map); macro categories split into
index_futures vs cash indices vs commodities (capped)."""
import os, json, time, argparse
import requests
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE_DIR, "data")
os.makedirs(DATA, exist_ok=True)

SCAN_URL = "https://scanner.tradingview.com/america/scan"
MACRO_SCAN_URL = "https://scanner.tradingview.com/global/scan"
CHUNK = 1000
MIN_PRICE = 0.5
COLS = ["ticker", "description", "sector", "market_cap_calc", "change_percent",
        "relative_volume_10d_calc", "volume", "is_primary", "change", "close", "type"]
MACRO_COLS = ["description", "change", "close"]
MACRO_CATS = ("indices", "index_futures", "commodities", "forex", "bonds")

def _norm_sym(s): return (s or "").rstrip("!")

def _post(body, url=SCAN_URL):
    for attempt in (1, 2):
        try:
            r = requests.post(url, json=body, timeout=30,
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
    raw_pct = data.get("change")
    pct = float(raw_pct) if isinstance(raw_pct, (int, float)) else None
    return {"t": ticker, "c": data.get("description") or ticker, "s": data.get("sector") or "US Market",
            "mcap": data.get("market_cap_calc") or 0, "pct": pct,
            "price": float(data["close"]) if isinstance(data.get("close"), (int, float)) else 0.0,
            "relvol": data.get("relative_volume_10d_calc") or 0, "vol": data.get("volume") or 0,
            "primary": bool(data.get("is_primary", 1)), "type": (data.get("type") or "stock")}

def _ok(m): return m["primary"] and m.get("type", "stock") == "stock"

def us_session_open(ts=None):
    dt = datetime.fromtimestamp(ts or time.time(), timezone.utc)
    if dt.weekday() > 4: return False
    el = dt - dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return timedelta(hours=13, minutes=30) <= el < timedelta(hours=20)

def fetch_universe(post_fn=_post):
    out = []; start = 0; total = 0
    while True:
        resp = post_fn({"columns": COLS, "options": {"lang": "en"}, "markets": ["america"],
                        "sort": {"sortBy": "market_cap_calc", "sortOrder": "desc"}, "range": [start, start + CHUNK]})
        total = resp.get("totalCount", 0); rows = resp.get("data", [])
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
        print("TV scan err:", type(e).__name__); return []

def fetch_movers(post_fn=_post, cap=300):
    movers = {}
    def add(m): movers[m["t"]] = {"pct": m["pct"], "relvol": m["relvol"], "mcap": m["mcap"]}
    for m in _top(post_fn, ("change_percent", "desc"), cap, lambda x: x["pct"] is not None and x["price"] >= MIN_PRICE and x["pct"] >= 4): add(m)
    for m in _top(post_fn, ("change_percent", "asc"), cap, lambda x: x["pct"] is not None and x["price"] >= MIN_PRICE and x["pct"] <= -4): add(m)
    for m in _top(post_fn, ("relative_volume_10d_calc", "desc"), cap, lambda x: x["price"] >= MIN_PRICE and x["relvol"] >= 2): add(m)
    return movers

def fetch_pulse(post_fn=_post, cap=20):
    mega = []; sample = {}
    resp = post_fn({"columns": COLS, "options": {"lang": "en"}, "markets": ["america"],
                    "sort": {"sortBy": "market_cap_calc", "sortOrder": "desc"}, "range": [0, cap * 3]})
    rows = resp.get("data", [])
    if rows: sample = dict(zip(COLS, rows[0].get("d", [])))
    for r in rows:
        m = _row(r)
        if _ok(m) and m["pct"] is not None: mega.append(m)
        if len(mega) >= cap: break
    pool = _top(post_fn, ("volume", "desc"), 400, lambda x: x.get("vol", 0) > 0)
    gainers = sorted([m for m in pool if m["pct"] is not None and m["pct"] > 0 and m["price"] >= MIN_PRICE], key=lambda x: -x["pct"])[:5]
    losers = sorted([m for m in pool if m["pct"] is not None and m["pct"] < 0 and m["price"] >= MIN_PRICE], key=lambda x: x["pct"])[:5]
    sig = {}
    def add_sig(m): sig[m["t"]] = {"pct": m["pct"], "relvol": m["relvol"], "mcap": m["mcap"]}
    for m in _top(post_fn, ("change_percent", "desc"), 150, lambda x: x["pct"] is not None and x["price"] >= MIN_PRICE and x["pct"] >= 3): add_sig(m)
    for m in _top(post_fn, ("change_percent", "asc"), 150, lambda x: x["pct"] is not None and x["price"] >= MIN_PRICE and x["pct"] <= -3): add_sig(m)
    for m in _top(post_fn, ("relative_volume_10d_calc", "desc"), 150, lambda x: x["price"] >= MIN_PRICE and x["relvol"] >= 2): add_sig(m)

    # ---- 1-hour movers vs previous snapshot ----
    prev_map = {}
    try:
        with open(os.path.join(DATA, "prev_pct.json")) as f: prev_map = json.load(f)
    except Exception: pass
    hour_movers = []
    for m in pool:
        if m["pct"] is None or m["price"] < MIN_PRICE: continue
        prev = prev_map.get(m["t"])
        if prev is None: continue
        hchg = m["pct"] - prev
        if abs(hchg) >= 1.0:
            hour_movers.append({"t": m["t"], "c": m["c"], "mcap": m["mcap"], "pct": m["pct"], "hour_chg": hchg})
    hour_movers.sort(key=lambda x: -x["mcap"])
    hour_movers = hour_movers[:5]
    try:
        with open(os.path.join(DATA, "prev_pct.json"), "w") as f:
            json.dump({m["t"]: m["pct"] for m in pool if m["pct"] is not None}, f)
    except Exception: pass

    deltas = {}
    for m in pool:
        if m["pct"] is not None and m["t"] in prev_map:
            deltas[m["t"]] = m["pct"] - prev_map[m["t"]]
    valid = any(m["pct"] is not None and abs(m["pct"]) > 0.005 for m in mega)
    return {"updated": time.time(), "valid": valid, "session_open": us_session_open(),
            "mega_caps": mega, "gainers": gainers, "losers": losers, "sig": sig,
            "sample": sample, "hour_movers": hour_movers, "deltas": deltas}

def fetch_macro(post_fn=None):
    try:
        with open(os.path.join(BASE_DIR, "config", "macro.json"), encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        return {"updated": time.time(), "valid": False, "instruments": [], "raw_sample": {}, "rows_returned": 0, "missing": []}
    symbols = []; index = {}
    for cat in MACRO_CATS:
        for item in cfg.get(cat, []):
            symbols.append(item["sym"]); index[_norm_sym(item["sym"])] = item
    if not symbols:
        return {"updated": time.time(), "valid": False, "instruments": [], "raw_sample": {}, "rows_returned": 0, "missing": []}
    if post_fn is None:
        resp = _post({"symbols": {"tickers": symbols}, "columns": MACRO_COLS, "options": {"lang": "en"}}, url=MACRO_SCAN_URL)
        rows = resp.get("data", [])
        got = {_norm_sym(r.get("s", "")) for r in rows}
        leftovers = [s for s in symbols if _norm_sym(s) not in got]
        if leftovers:
            rows = rows + _post({"symbols": {"tickers": leftovers}, "columns": MACRO_COLS, "options": {"lang": "en"}}).get("data", [])
    else:
        rows = post_fn({"symbols": {"tickers": symbols}, "columns": MACRO_COLS, "options": {"lang": "en"}}).get("data", [])
    instruments = []
    for r in rows:
        data = dict(zip(MACRO_COLS, r.get("d", [])))
        meta = index.get(_norm_sym(r.get("s", "")))
        if not meta: continue
        raw_pct = data.get("change")
        pct = float(raw_pct) if isinstance(raw_pct, (int, float)) else None
        price = float(data["close"]) if isinstance(data.get("close"), (int, float)) else None
        instruments.append({"sym": meta["sym"], "name": meta["name"], "type": meta["type"], "pct": pct, "price": price})
    returned = {_norm_sym(i["sym"]) for i in instruments}
    missing = [s for s in symbols if _norm_sym(s) not in returned]
    valid = len(instruments) > 0 and any(i["pct"] is not None for i in instruments)
    sample = dict(zip(MACRO_COLS, rows[0].get("d", []))) if rows else {}
    return {"updated": time.time(), "valid": valid, "instruments": instruments,
            "raw_sample": sample, "rows_returned": len(rows), "missing": missing}

def save(name, obj):
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as f: json.dump(obj, f)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", action="store_true")
    ap.add_argument("--movers", action="store_true")
    ap.add_argument("--pulse", action="store_true")
    ap.add_argument("--macro", action="store_true")
    ap.add_argument("--search", nargs="+")
    args = ap.parse_args()
    if args.universe:
        try:
            uni, total = fetch_universe()
            save("tv_universe.json", {"updated": time.time(), "total": total, "rows": uni})
            print("TV UNIVERSE OK: %d primary stock rows (totalCount %d)" % (len(uni), total))
        except Exception as e: print("TV UNIVERSE FAIL:", type(e).__name__, str(e)[:120])
    if args.movers:
        try:
            mv = fetch_movers(); save("movers.json", {"updated": time.time(), "movers": mv})
            print("TV MOVERS OK: %d movers" % len(mv))
        except Exception as e: print("TV MOVERS FAIL:", type(e).__name__, str(e)[:120])
    if args.pulse:
        try:
            pulse = fetch_pulse()
            save("market_pulse.json", pulse)
            save("movers.json", {"updated": pulse["updated"], "movers": pulse.get("sig", {})})
            state = "INVALID (no reliable data)" if not pulse["valid"] else ("OK (LIVE session)" if pulse["session_open"] else "OK (previous session data)")
            present = sum(1 for m in pulse["mega_caps"] if m["pct"] is not None)
            print("TV PULSE %s: %d mega caps, %d gainers, %d losers, %d sig, %d 1h-movers, pct coverage %d/%d" % (
                state, len(pulse["mega_caps"]), len(pulse["gainers"]), len(pulse["losers"]),
                len(pulse.get("sig", {})), len(pulse.get("hour_movers", [])), present, len(pulse["mega_caps"])))
            if pulse["mega_caps"] and present == 0:
                print("RAW SAMPLE ROW:", json.dumps(pulse.get("sample", {}))[:400])
        except Exception as e: print("TV PULSE FAIL:", type(e).__name__, str(e)[:120])
    if args.macro:
        try:
            macro = fetch_macro(); save("macro_pulse.json", macro)
            state = "OK" if macro["valid"] else "INVALID (no reliable data)"
            miss = macro.get("missing", [])
            print("TV MACRO %s: %d instruments (%d rows)%s" % (state, len(macro["instruments"]),
                  macro.get("rows_returned", 0), (" | missing: " + ", ".join(miss)) if miss else ""))
        except Exception as e: print("TV MACRO FAIL:", type(e).__name__, str(e)[:120])
    if args.search:
        q = " ".join(args.search).lower()
        p = os.path.join(DATA, "tv_universe.json")
        if not os.path.exists(p): print("No universe file yet."); return
        uni = json.load(open(p, encoding="utf-8"))["rows"]
        pm = os.path.join(DATA, "movers.json")
        mv = json.load(open(pm, encoding="utf-8"))["movers"] if os.path.exists(pm) else {}
        hits = [r for r in uni if q in r["t"].lower() or q in r["c"].lower()][:20]
        if not hits: print("No matches for '%s'." % q)
        for r in hits:
            flag = " MOVER" if r["t"] in mv else ""
            pct_s = "%+6.2f%%" % r["pct"] if r["pct"] is not None else "   n/a"
            print("%-8s | %-38s | %-16s | mcap %8.1fB | $%7.2f | %s | relvol %5.2f%s" % (
                r["t"], r["c"][:36], str(r["s"])[:16], r["mcap"] / 1e9, r["price"], pct_s, r["relvol"], flag))

if __name__ == "__main__":
    main()
