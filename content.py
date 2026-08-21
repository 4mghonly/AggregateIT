"""context.py — project-wide ACTIVE STORYLINES brief for all LLM touchpoints."""
from datetime import datetime, timezone
from storage import SQLiteStore
import market

def build_context_brief(max_events=8):
    store = SQLiteStore()
    lines = ["ACTIVE STORYLINES:"]
    for ev in store.recent_all_events(hours=72, limit=max_events):
        ts = datetime.fromtimestamp(ev.get("last_updated") or 0, timezone.utc).strftime("%m-%d %H:%M")
        n = 0
        try: n = store.get_claim_count(ev["event_id"])
        except Exception: pass
        claim = f" · {n} claims" if n else ""
        lines.append(f"- [{ev.get('status')}/{ev.get('severity')}] {(ev.get('title') or '')[:80]} (upd {ts}{claim})")
    macro = market.load_macro_pulse() or {}
    regime = market.compute_regime(macro) if macro else {}
    if regime:
        lines.append("REGIME: " + ", ".join(f"{k}={v}" for k, v in regime.items()))
    return "\n".join(lines) if len(lines) > 1 else ""
