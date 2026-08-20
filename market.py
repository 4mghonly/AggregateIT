"""market.py — shared market pulse reader + embed builder.
Single source of truth for market presentation; consumed by the hourly digest
(main.py) AND the executive briefings (briefing.py). Honesty-gated:
never presents zeros as live, never presents stale snapshots as fresh."""
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
