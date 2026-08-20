"""slide.py — PowerPoint-style intelligence slide (PNG) posted to Discord.
Tentative, machine-compiled summary of news + market moves."""
import os, json, textwrap, requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime, timezone
from storage import SQLiteStore
import market

BASE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(BASE, "reports")
OUT = os.path.join(REPORTS, "intel_slide.png")

BG, PANEL, TXT, MUT = "#1e1f22", "#2b2d31", "#dbdee1", "#949ba4"
GRN, RED, AMB, BLU = "#2ecc71", "#e74c3c", "#f1c40f", "#5865f2"
SEV_COLOR = {"Critical": RED, "High": AMB, "Medium": "#e67e22", "Low": MUT}

def _wrap(s, n): return textwrap.wrap(s or "", n) or [""]

def _qwen_summary(data_text):
    try:
        base = os.environ.get("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1").rstrip("/")
        r = requests.post(base + "/chat/completions",
            headers={"Authorization": "Bearer " + os.environ["QWEN_API_KEY"]},
            json={"model": os.environ.get("QWEN_MODEL", "qwen-plus"), "temperature": 0.3,
                  "messages": [
                      {"role": "system", "content": "You are an intelligence analyst. Output ONLY valid JSON."},
                      {"role": "user", "content": "Write a tentative 2-3 sentence executive summary of today's news AND market moves. Be quantitative. Output ONLY: {\"summary\": \"...\"}\n\nDATA:\n" + data_text}]},
            timeout=60)
        r.raise_for_status()
        obj = json.loads(r.json()["choices"][0]["message"]["content"].split("{", 1)[-1].rsplit("}", 1)[0].join(["{", "}"]))
        s = obj.get("summary", "")
        if 20 <= len(s) <= 400: return s
    except Exception:
        pass
    return None

def _fallback_summary(events, pulse, regime):
    parts = []
    g, l = pulse.get("gainers", []), pulse.get("losers", [])
    if g and l: parts.append(f"Equities: {g[0]['t']} +{g[0]['pct']:.1f}% leads, {l[0]['t']} {l[0]['pct']:.1f}% lags.")
    if regime.get("vix"): parts.append(f"VIX {regime['vix']}.")
    if regime.get("curve_2s10s"): parts.append(f"2s10s {regime['curve_2s10s']}.")
    if events: parts.append(f"{len(events)} events tracked; top: {(events[0].get('title') or '')[:70]}.")
    return " ".join(parts) or "Quiet session - no major signals."

def build_slide():
    store = SQLiteStore()
    pulse = market.load_market_pulse() or {}
    macro = market.load_macro_pulse() or {}
    regime = market.compute_regime(macro) if macro else {}
    events = store.recent_all_events(hours=24)[:5]

    data_text = "\n".join([f"- {e.get('title')} [{e.get('severity')}, {e.get('status')}]" for e in events] +
                          [f"- {m['t']} {m['pct']:+.2f}%" for m in (pulse.get('gainers', []) + pulse.get('losers', []))[:8]] +
                          [f"- {i['name']} {i['pct']:+.2f}%" for i in macro.get('instruments', []) if i.get('pct') is not None][:10])
    summary = _qwen_summary(data_text) or _fallback_summary(events, pulse, regime)

    fig = plt.figure(figsize=(16, 9), dpi=120)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    now = datetime.now(timezone.utc).strftime("%a %Y-%m-%d %H:%M UTC")
    session = "LIVE US SESSION" if pulse.get("session_open") else "PREVIOUS SESSION"
    ax.text(0.03, 0.95, "AGGREGATEIT - INTELLIGENCE BRIEF", color=TXT, fontsize=25, weight="bold")
    ax.text(0.97, 0.95, f"{now}  ·  {session}", color=MUT, fontsize=12, ha="right")
    ax.add_patch(plt.Rectangle((0.03, 0.925), 0.94, 0.01, color=BLU))

    ax.text(0.03, 0.895, "EXECUTIVE SUMMARY (TENTATIVE)", color=BLU, fontsize=14, weight="bold")
    y = 0.865
    for line in _wrap(summary, 110)[:3]:
        ax.text(0.03, y, line, color=TXT, fontsize=12.5); y -= 0.028

    # Column 1: events
    y = 0.76
    ax.text(0.03, y, "TOP EVENTS (24H)", color=BLU, fontsize=15, weight="bold"); y -= 0.04
    if not events: ax.text(0.03, y, "No tracked events in window.", color=MUT, fontsize=12)
    for ev in events:
        sev = ev.get("severity") or "Low"
        ax.add_patch(plt.Rectangle((0.03, y - 0.012), 0.006, 0.028, color=SEV_COLOR.get(sev, MUT)))
        lines = _wrap(ev.get("title"), 44)[:2]
        ax.text(0.045, y, lines[0], color=TXT, fontsize=12, weight="bold"); y -= 0.027
        if len(lines) > 1:
            ax.text(0.045, y, lines[1], color=TXT, fontsize=12, weight="bold"); y -= 0.027
        ax.text(0.045, y, f"{sev.upper()} · conf {ev.get('confidence')}% · {ev.get('status', 'NEW')} · src {ev.get('source_count')}",
                color=MUT, fontsize=10); y -= 0.05

    # Column 2: market pulse
    x2 = 0.40; y = 0.76
    ax.text(x2, y, "MARKET PULSE", color=BLU, fontsize=15, weight="bold"); y -= 0.04
    for m in pulse.get("gainers", [])[:4]:
        ax.text(x2, y, m["t"], color=TXT, fontsize=12, weight="bold")
        ax.text(x2 + 0.10, y, f"+{m['pct']:.2f}%", color=GRN, fontsize=12); y -= 0.03
    y -= 0.015
    for m in pulse.get("losers", [])[:4]:
        ax.text(x2, y, m["t"], color=TXT, fontsize=12, weight="bold")
        ax.text(x2 + 0.10, y, f"{m['pct']:.2f}%", color=RED, fontsize=12); y -= 0.03

    # Column 3: macro + regime
    x3 = 0.68; y = 0.76
    ax.text(x3, y, "MACRO & RATES", color=BLU, fontsize=15, weight="bold"); y -= 0.04
    groups = {}
    for i in macro.get("instruments", []): groups.setdefault(i.get("type"), []).append(i)
    for gname, key, n in (("INDICES", "index", 4), ("COMMODITIES", "future", 3), ("RATES", "bond", 3), ("FOREX", "forex", 3)):
        ax.text(x3, y, gname, color=MUT, fontsize=10.5, weight="bold"); y -= 0.026
        for inst in groups.get(key, [])[:n]:
            p = inst.get("pct")
            col = GRN if (p or 0) > 0 else (RED if (p or 0) < 0 else MUT)
            ax.text(x3, y, inst["name"], color=TXT, fontsize=11)
            ax.text(x3 + 0.16, y, f"{p:+.2f}%" if p is not None else "-", color=col, fontsize=11)
            y -= 0.026
        y -= 0.012
    for line in ([f"VIX: {regime['vix']}"] if "vix" in regime else []) + \
                ([f"2s10s: {regime['curve_2s10s']}" + (" INVERTED" if regime.get("curve_inverted") else "")] if "curve_2s10s" in regime else []) + \
                ([f"DXY: {regime['dxy']}"] if "dxy" in regime else []):
        ax.text(x3, y, line, color=AMB, fontsize=11); y -= 0.026

    # Footer: sentiment
    rolls = {"bullish": 0, "neutral": 0, "bearish": 0}
    for e in events:
        s = (e.get("sentiment") or "").lower()
        if s in rolls: rolls[s] += 1
    tot = max(sum(rolls.values()), 1)
    ax.text(0.03, 0.06, "NEWS SENTIMENT (24H)", color=MUT, fontsize=10.5, weight="bold")
    x = 0.03
    for key, col in (("bullish", GRN), ("neutral", MUT), ("bearish", RED)):
        w = 0.5 * rolls[key] / tot
        ax.add_patch(plt.Rectangle((x, 0.03), max(w, 0.004), 0.015, color=col))
        x += w + 0.004
    ax.text(0.97, 0.04, f"bull {rolls['bullish']} · neut {rolls['neutral']} · bear {rolls['bearish']}  ·  TENTATIVE - machine-compiled",
            color=MUT, fontsize=10, ha="right")

    os.makedirs(REPORTS, exist_ok=True)
    fig.savefig(OUT, facecolor=BG)
    plt.close(fig)
    return OUT

def send_slide(path):
    wh = os.environ.get("DISCORD_WEBHOOK")
    if not wh:
        print("FATAL: DISCORD_WEBHOOK secret is not set."); return
    with open(path, "rb") as f:
        r = requests.post(wh, files={"file": ("intel_slide.png", f, "image/png")},
                          data={"payload_json": json.dumps({"content": "📊 **AggregateIT Intelligence Slide** (tentative)"})})
    if r.status_code >= 400:
        raise RuntimeError(f"Discord HTTP {r.status_code}: {r.text[:120]}")
    print("✅ Slide delivered!")

if __name__ == "__main__":
    p = build_slide()
    send_slide(p)
