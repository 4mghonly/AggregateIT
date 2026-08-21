"""market.py — pulse + macro readers and embed builders. v4: two dense
macro columns (indices·futures·commodities | forex·rates·regime)."""
import os, json, time
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
MAX_AGE_H = 20

def load_market_pulse():
    try:
        with open(os.path.join(DATA, "market_pulse.json"), encoding="utf-8") as f: return json.load(f)
    except Exception: return None

def load_macro_pulse():
    try:
        with open(os.path.join(DATA, "macro_pulse.json"), encoding="utf-8") as f: return json.load(f)
    except Exception: return None

def _fmt_row(m):
    p = m.get("pct")
    if p is None:
        rv = " · %.1fx" % m["relvol"] if m.get("relvol", 0) >= 1.5 else ""
        return "⚪ %s —%s" % (m["t"], rv)
    arrow = "🟢" if p > 0.005 else ("🔴" if p < -0.005 else "⚪")
    rv = " · %.1fx" % m["relvol"] if m.get("relvol", 0) >= 1.5 else ""
    return "%s %s %+.2f%%%s" % (arrow, m["t"], p, rv)

def build_pulse_embed(pulse, color=None):
    ts = datetime.fromtimestamp(pulse["updated"], timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    age_h = (time.time() - pulse.get("updated", 0)) / 3600.0
    if not pulse.get("valid"):
        return {"title": "💹 Market Pulse", "color": color or 0x95A5A6, "description": "🏛️ No reliable market data.\nLast snapshot: %s" % ts}
    if age_h > MAX_AGE_H:
        return {"title": "💹 Market Pulse", "color": color or 0x95A5A6, "description": "🏛️ Snapshot STALE (%.0fh old).\nLast snapshot: %s" % (age_h, ts)}
    label = ("Live US session snapshot · as of %s" % ts) if pulse.get("session_open") else ("US market closed — previous session data · as of %s" % ts)
    fields = [
        {"name": "🚀 Top Movers", "value": "\n".join(_fmt_row(m) for m in pulse.get("gainers", [])[:5]) or "—", "inline": True},
        {"name": "📉 Top Fallers", "value": "\n".join(_fmt_row(m) for m in pulse.get("losers", [])[:5]) or "—", "inline": True},
    ]
    hm = pulse.get("hour_movers", [])
    if hm:
        fields.append({"name": "⏱️ 1-Hour Movers (large caps)", "inline": False,
                       "value": "\n".join("%s %+.2f%% (1h) · sess %+.2f%%" % (m["t"], m["hour_chg"], m["pct"]) for m in hm[:5])})
    fields.append({"name": "🏛️ Mega-Cap Scoreboard (Top 20 stocks)", "inline": False,
                   "value": " | ".join(_fmt_row(m) for m in pulse.get("mega_caps", [])[:20]) or "—"})
    auto = 0x2ECC71 if pulse.get("session_open") else 0xF1C40F
    return {"title": "💹 Market Pulse", "color": color or auto, "description": label, "fields": fields}

def compute_regime(macro):
    regime = {}
    im = {i["sym"]: i for i in macro.get("instruments", [])}
    vix = im.get("CBOE:VIX")
    if vix and vix["price"] is not None:
        v = vix["price"]
        regime["vix"] = "complacent (<15)" if v < 15 else "normal (15-20)" if v < 20 else "elevated (20-30)" if v < 30 else "stress (>30)"
    u2, u10 = im.get("TVC:US02Y"), im.get("TVC:US10Y")
    if u2 and u10 and u2["price"] is not None and u10["price"] is not None:
        spread_bp = (u10["price"] - u2["price"]) * 100
        regime["curve_2s10s"] = "%+.1fbp" % spread_bp
        if spread_bp < 0: regime["curve_inverted"] = True
    dxy = im.get("TVC:DXY")
    if dxy and dxy["pct"] is not None:
        regime["dxy"] = "strong bid" if dxy["pct"] > 0.5 else "weak" if dxy["pct"] < -0.5 else "neutral"
    oil = im.get("NYMEX:CL1!")
    if oil and oil["pct"] is not None and abs(oil["pct"]) > 3.0:
        regime["oil_spike"] = "%+.1f%%" % oil["pct"]
    return regime

def _mline(i):
    p = i.get("pct")
    arrow = "🟢" if (p or 0) > 0 else ("🔴" if (p or 0) < 0 else "⚪")
    return "%s %s %s" % (arrow, i["name"], "%+.2f%%" % p if p is not None else "—")

def build_macro_embed(macro, regime=None, color=None):
    if not macro or not macro.get("valid"):
        return {"title": "🌐 Macro & Rates", "color": color or 0x95A5A6, "description": "No macro data available."}
    ts = datetime.fromtimestamp(macro["updated"], timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    groups = {}
    for i in macro.get("instruments", []): groups.setdefault(i.get("type", "other"), []).append(i)
    col1 = [_mline(i) for i in groups.get("index", [])[:6]]
    if groups.get("index_future"):
        col1 += ["— INDEX FUTURES —"] + [_mline(i) for i in groups.get("index_future", [])[:3]]
    col1 += ["— COMMODITIES —"] + [_mline(i) for i in groups.get("commodity", [])[:5]]
    col2 = [_mline(i) for i in groups.get("forex", [])[:4]]
    col2 += ["— RATES —"] + [_mline(i) for i in groups.get("bond", [])[:3]]
    if regime:
        col2 += ["— REGIME —"]
        if "vix" in regime: col2.append("VIX: %s" % regime["vix"])
        if "curve_2s10s" in regime: col2.append("2s10s: %s%s" % (regime["curve_2s10s"], " ⚠️ INVERTED" if regime.get("curve_inverted") else ""))
        if "dxy" in regime: col2.append("DXY: %s" % regime["dxy"])
        if "oil_spike" in regime: col2.append("Oil spike: %s" % regime["oil_spike"])
    return {"title": "🌐 Macro & Rates", "color": color or 0x9B59B6,
            "description": "Macro snapshot · as of %s" % ts,
            "fields": [
                {"name": "Indices · Index Futures · Commodities", "value": "\n".join(col1), "inline": True},
                {"name": "Forex · Rates · Regime", "value": "\n".join(col2), "inline": True}]}
