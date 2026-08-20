"""market.py — shared market pulse + macro reader and embed builders.
Honesty-gated: never presents zeros as live, never presents stale snapshots as fresh.
Macro panel renders by instrument type, so config symbol swaps never break it."""
import os, json, time
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
MAX_AGE_H = 20  # older than this = stale (pulse refreshes 3x/day on trading days)

def load_market_pulse():
    try:
        with open(os.path.join(DATA, "market_pulse.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def load_macro_pulse():
    try:
        with open(os.path.join(DATA, "macro_pulse.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _fmt_row(m):
    p = m.get("pct")
    if p is None:
        rv = f" · {m['relvol']:.1f}×" if m.get("relvol", 0) >= 1.5 else ""
        return f"⚪ {m['t']} —{rv}"
    arrow = "🟢" if p > 0.005 else ("🔴" if p < -0.005 else "⚪")
    rv = f" · {m['relvol']:.1f}×" if m.get("relvol", 0) >= 1.5 else ""
    return f"{arrow} {m['t']} {p:+.2f}%{rv}"

def build_pulse_embed(pulse, color=None):
    ts = datetime.fromtimestamp(pulse["updated"], timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    age_h = (time.time() - pulse.get("updated", 0)) / 3600.0
    if not pulse.get("valid"):
        return {"title": "💹 Market Pulse", "color": color or 0x95A5A6,
                "description": f"🏛️ No reliable market data.\nLast snapshot: {ts}"}
    if age_h > MAX_AGE_H:
        return {"title": "💹 Market Pulse", "color": color or 0x95A5A6,
                "description": f"🏛️ Snapshot STALE ({age_h:.0f}h old) — TV refresh not landing?\nLast snapshot: {ts}"}
    if pulse.get("session_open"):
        label = f"Live US session snapshot · as of {ts}"
    else:
        label = f"US market closed — previous session data · as of {ts}"
    fields = [
        {"name": "🚀 Top Movers", "value": "\n".join(_fmt_row(m) for m in pulse.get("gainers", [])[:5]) or "—", "inline": True},
        {"name": "📉 Top Fallers", "value": "\n".join(_fmt_row(m) for m in pulse.get("losers", [])[:5]) or "—", "inline": True},
    ]
    fields.append({"name": "🏛️ Mega-Cap Scoreboard (Top 20 stocks)",
                   "value": " | ".join(_fmt_row(m) for m in pulse.get("mega_caps", [])[:20]) or "—", "inline": False})
    auto = 0x2ECC71 if pulse.get("session_open") else 0xF1C40F
    return {"title": "💹 Market Pulse", "color": color or auto, "description": label, "fields": fields}

def compute_regime(macro):
    """Deterministic regime signals from macro data (zero tokens)."""
    regime = {}
    inst_map = {i["sym"]: i for i in macro.get("instruments", [])}

    vix = inst_map.get("CBOE:VIX")
    if vix and vix["price"] is not None:
        v = vix["price"]
        if v < 15: regime["vix"] = "complacent (<15)"
        elif v < 20: regime["vix"] = "normal (15-20)"
        elif v < 30: regime["vix"] = "elevated (20-30)"
        else: regime["vix"] = "stress (>30)"

    us2y = inst_map.get("TVC:US02Y")
    us10y = inst_map.get("TVC:US10Y")
    if us2y and us10y and us2y["price"] is not None and us10y["price"] is not None:
        spread_bp = (us10y["price"] - us2y["price"]) * 100
        regime["curve_2s10s"] = f"{spread_bp:+.1f}bp"
        if spread_bp < 0: regime["curve_inverted"] = True

    dxy = inst_map.get("TVC:DXY")
    if dxy and dxy["pct"] is not None:
        if dxy["pct"] > 0.5: regime["dxy"] = "strong bid"
        elif dxy["pct"] < -0.5: regime["dxy"] = "weak"
        else: regime["dxy"] = "neutral"

    oil = inst_map.get("NYMEX:CL1!")
    if oil and oil["pct"] is not None and abs(oil["pct"]) > 3.0:
        regime["oil_spike"] = f"{oil['pct']:+.1f}%"

    return regime

def build_macro_embed(macro, regime=None, color=None):
    """Macro panel rendered by instrument type — config-driven, symbol-agnostic."""
    if not macro or not macro.get("valid"):
        return {"title": "🌐 Macro & Rates", "color": color or 0x95A5A6,
                "description": "No macro data available."}

    ts = datetime.fromtimestamp(macro["updated"], timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    groups = {}
    for i in macro.get("instruments", []):
        groups.setdefault(i.get("type", "other"), []).append(i)

    def fmt_list(lst, n=4):
        out = []
        for inst in lst[:n]:
            p = inst.get("pct")
            if p is None:
                out.append(f"⚪ {inst['name']} —")
            else:
                arrow = "🟢" if p > 0 else ("🔴" if p < 0 else "⚪")
                out.append(f"{arrow} {inst['name']} {p:+.2f}%")
        return "\n".join(out) or "—"

    fields = [
        {"name": "📈 Indices", "value": fmt_list(groups.get("index", [])), "inline": True},
        {"name": "📊 Futures & Commodities", "value": fmt_list(groups.get("future", [])), "inline": True},
        {"name": "💱 Forex", "value": fmt_list(groups.get("forex", []), 3), "inline": True},
        {"name": "🏦 Rates", "value": fmt_list(groups.get("bond", []), 3), "inline": True},
    ]

    if regime:
        regime_lines = []
        if "vix" in regime: regime_lines.append(f"VIX: {regime['vix']}")
        if "curve_2s10s" in regime:
            inv = " ⚠️ INVERTED" if regime.get("curve_inverted") else ""
            regime_lines.append(f"2s10s: {regime['curve_2s10s']}{inv}")
        if "dxy" in regime: regime_lines.append(f"DXY: {regime['dxy']}")
        if "oil_spike" in regime: regime_lines.append(f"Oil spike: {regime['oil_spike']}")
        if regime_lines:
            fields.append({"name": "🎯 Regime Signals", "value": "\n".join(regime_lines), "inline": False})

    return {"title": "🌐 Macro & Rates", "color": color or 0x9B59B6,
            "description": f"Macro snapshot · as of {ts}", "fields": fields}
