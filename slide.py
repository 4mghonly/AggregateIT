"""slide.py v6 — Infographic-style two-page intelligence deck.
Design language: KPI ring row, rounded accent panels, right numbers rail,
structured macro grid. All charts computed strictly from snapshots.
LLM narrative (8 fields) schema-validated with deterministic fallbacks.
Previous state persisted for delta-vs-previous-briefing."""
import os, json, re, time, textwrap, requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, FancyBboxPatch
from datetime import datetime, timezone
from storage import SQLiteStore
import market
from briefing import fetch_stocktwits, load_events, theme_counts, DOMAIN_NAMES

BASE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(BASE, "reports")
P1 = os.path.join(REPORTS, "intel_slide_p1.png")
P2 = os.path.join(REPORTS, "intel_slide_p2.png")
PREV_FILE = os.path.join(REPORTS, "prev_slide.json")

BG, PANEL, CARD, TXT, MUT = "#141517", "#1e1f22", "#26272b", "#dbdee1", "#949ba4"
LINE = "#3a3d42"
GRN, RED, AMB, BLU, ORG, TEAL, PUR = "#2ecc71", "#e74c3c", "#f1c40f", "#5865f2", "#e67e22", "#1abc9c", "#9b59b6"
SEV_COLOR = {"Critical": RED, "High": AMB, "Medium": ORG, "Low": MUT}

def _clean(s): return re.sub(r'[^\x20-\x7E]', '', s or '').strip()
def _wrap(s, n): return textwrap.wrap(_clean(s), n) or [""]
def _fmt_price(p, t):
    if p is None: return "-"
    if t == "forex": return "%.4f" % p
    if t == "bond": return "%.2f%%" % p
    if p >= 10000: return "%.0f" % p
    if p >= 100: return "%.1f" % p
    return "%.2f" % p

# ================= STATE / COLLECT / ANALYSIS (unchanged logic) =================
def _load_prev():
    try:
        with open(PREV_FILE) as f: return json.load(f)
    except Exception: return None

def _save_prev(a, d):
    try:
        with open(PREV_FILE, "w") as f:
            json.dump({"ts": time.time(), "summary": a.get("summary", ""),
                       "event_titles": [e.get("title", "") for e in d["events"][:8]],
                       "regime": d.get("regime", {}),
                       "top_gainer": d["pulse"].get("gainers", [{}])[0].get("t") if d["pulse"].get("gainers") else None,
                       "top_loser": d["pulse"].get("losers", [{}])[0].get("t") if d["pulse"].get("losers") else None}, f)
    except Exception: pass

def collect():
    store = SQLiteStore()
    pulse = market.load_market_pulse() or {}
    macro = market.load_macro_pulse() or {}
    regime = market.compute_regime(macro) if macro else {}
    events = load_events(store, 24)
    themes = theme_counts(events)
    movers_t = [m["t"] for m in (pulse.get("gainers", []) + pulse.get("losers", []))[:8]]
    st_sent, st_radar = fetch_stocktwits(movers_t)
    reddit = {}
    for ev in store.recent_all_events(hours=24):
        try: srcs = json.loads(ev.get("sources_json") or "[]")
        except Exception: srcs = []
        for s in srcs:
            n = s.get("name", "")
            if n.startswith("r/"): reddit[n] = reddit.get(n, 0) + 1
    sources_active = sorted({(e.get("source") or "").split(" +")[0] for e in events if e.get("source")})
    return {"store": store, "pulse": pulse, "macro": macro, "regime": regime, "events": events,
            "themes": themes, "st_sent": st_sent, "st_radar": st_radar, "reddit": reddit,
            "sources_active": sources_active}

ANALYSIS_PROMPT = """You are a senior cross-asset intelligence analyst compiling a periodic deck.
Write a TENTATIVE but highly quantitative analysis tying together news, market moves, and social sentiment.
Strict rules:
- Only reference data points present in the DATA section.
- Never invent tickers, prices, percentages, or events.
- DO NOT USE EMOJIS.
- Clearly distinguish facts from interpretation.
- Where applicable, explain HOW news events connect to observed price action.
- Keep each field under 600 characters.

Return ONLY this JSON:
{
  "summary": "3 sentences: what happened, what moved, and what it means",
  "news_read": "2-3 sentences: dominant news themes, most material events, source quality",
  "market_read": "2-3 sentences: equities, rates, FX, commodities cross-asset behavior and divergences",
  "social_read": "1-2 sentences: retail sentiment vs price action, crowd positioning",
  "cross_asset": "2 sentences: how specific news events connect to observed price moves",
  "outlook": "1-2 sentences: key levels, catalysts, or events to watch next 24 hours",
  "key_risk": "1 sentence: the single most important risk or opportunity right now",
  "delta": "1-2 sentences: what changed vs the previous briefing"
}

PREVIOUS BRIEFING STATE:
__PREV__

CURRENT DATA:
__DATA__"""

REQUIRED_KEYS = ("summary", "news_read", "market_read", "social_read",
                 "cross_asset", "outlook", "key_risk", "delta")

def _data_text(d):
    L = []
    for e in d["events"][:8]:
        L.append("EVENT [%s/%s] %s (src: %s)" % (e.get("severity"), e.get("status"), e.get("title"), e.get("source")))
    for m in (d["pulse"].get("gainers", []) + d["pulse"].get("losers", []))[:8]:
        L.append("MOVER %s %+.2f%%" % (m["t"], m["pct"]))
    for i in d["macro"].get("instruments", []):
        if i.get("pct") is not None:
            L.append("MACRO %s price=%s chg=%+.2f%%" % (i["name"], _fmt_price(i.get("price"), i.get("type")), i["pct"]))
    for k, v in d["regime"].items(): L.append("REGIME %s = %s" % (k, v))
    for k, v in sorted(d["themes"].items(), key=lambda x: -x[1])[:5]:
        L.append("THEME %s x%d" % (_clean(DOMAIN_NAMES.get(k, k)), v))
    if d["st_radar"]: L.append("STOCKTWITS " + " | ".join([_clean(r) for r in d["st_radar"][:6]]))
    if d["reddit"]:
        L.append("REDDIT " + ", ".join("%s x%d" % (k, v) for k, v in sorted(d["reddit"].items(), key=lambda x: -x[1])[:5]))
    if d["sources_active"]: L.append("ACTIVE SOURCES: " + ", ".join(d["sources_active"][:15]))
    return "\n".join(L)

def _prev_text(prev):
    if not prev: return "First briefing of this cycle - no prior comparison available."
    L = ["Previous briefing at %s UTC:" % datetime.fromtimestamp(prev.get("ts", 0), timezone.utc).strftime("%H:%M")]
    if prev.get("summary"): L.append("Prev summary: %s" % prev["summary"][:200])
    if prev.get("event_titles"): L.append("Prev events: %s" % ", ".join(prev["event_titles"][:5]))
    if prev.get("top_gainer"): L.append("Prev top gainer: %s" % prev["top_gainer"])
    if prev.get("top_loser"): L.append("Prev top loser: %s" % prev["top_loser"])
    if prev.get("regime"): L.append("Prev regime: " + ", ".join("%s=%s" % (k, v) for k, v in prev["regime"].items()))
    return "\n".join(L)

def _fallback_analysis(d, prev):
    ev, pulse, regime = d["events"], d["pulse"], d["regime"]
    g, l = pulse.get("gainers", []), pulse.get("losers", [])
    lead = ("led by %s +%.1f%%" % (g[0]["t"], g[0]["pct"])) if g else "quiet"
    lag = ("; %s %.1f%% lags" % (l[0]["t"], l[0]["pct"])) if l else ""
    mkt = "Equities %s%s. VIX %s; 2s10s %s." % (lead, lag, regime.get("vix", "n/a"), regime.get("curve_2s10s", "n/a"))
    news = ("Dominant cluster: %s." % _clean(DOMAIN_NAMES.get(sorted(d["themes"].items(), key=lambda x: -x[1])[0][0], "Mixed"))) if d["themes"] else "No dominant news cluster in window."
    if ev: news += " Top event: %s." % (ev[0].get("title") or "")[:80]
    soc = " | ".join([_clean(r) for r in d["st_radar"][:4]]) if d["st_radar"] else "No strong retail consensus."
    if d["reddit"]:
        soc += " Reddit: " + ", ".join("%s x%d" % (k, v) for k, v in sorted(d["reddit"].items(), key=lambda x: -x[1])[:3])
    return {"summary": (news + " " + mkt)[:600], "news_read": news[:600], "market_read": mkt[:600],
            "social_read": soc[:600], "cross_asset": mkt[:600],
            "outlook": "Watch for continuation in dominant themes; monitor pre-market futures for gap risk.",
            "key_risk": ("Monitor for escalation in the dominant cluster." if ev else "Quiet tape - gap-on-open from off-hours news is primary risk."),
            "delta": ("First briefing - no prior comparison." if not prev else "Prior briefing at %s UTC." % datetime.fromtimestamp(prev.get("ts", 0), timezone.utc).strftime("%H:%M"))}

def analyze(d):
    prev = _load_prev()
    try:
        base = os.environ.get("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1").rstrip("/")
        prompt = ANALYSIS_PROMPT.replace("__DATA__", _data_text(d)).replace("__PREV__", _prev_text(prev))
        r = requests.post(base + "/chat/completions",
            headers={"Authorization": "Bearer " + os.environ["QWEN_API_KEY"]},
            json={"model": os.environ.get("QWEN_MODEL", "qwen-plus"), "temperature": 0.3,
                  "messages": [{"role": "system", "content": "Disciplined cross-asset analyst. Output ONLY valid JSON. NO EMOJIS."},
                               {"role": "user", "content": prompt}]}, timeout=90)
        r.raise_for_status()
        m = re.search(r"\{[\s\S]*\}", r.json()["choices"][0]["message"]["content"])
        if m:
            obj = json.loads(m.group(0))
            if all(isinstance(obj.get(k), str) and len(obj.get(k)) >= 10 for k in REQUIRED_KEYS):
                return obj, True, prev
    except Exception: pass
    return _fallback_analysis(d, prev), False, prev

# ================= INFOGRAPHIC PRIMITIVES =================
def panel(ax, x, y, w, h, title=None, accent=BLU):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.004,rounding_size=0.012",
                                fc=PANEL, ec=LINE, lw=1.0, transform=ax.transAxes, zorder=1))
    if title:
        ax.add_patch(plt.Rectangle((x + 0.008, y + h - 0.030), 0.004, 0.020, color=accent, transform=ax.transAxes, zorder=2))
        ax.text(x + 0.016, y + h - 0.020, _clean(title), color=accent, fontsize=10.5, weight="bold",
                va="center", transform=ax.transAxes, zorder=2)

def ring_axes(fig, cx, cy, s, frac, color, center_txt):
    h = s * 16.0 / 9.0
    ax = fig.add_axes([cx - s / 2, cy - h / 2, s, h])
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_aspect("equal"); ax.set_axis_off()
    ax.add_patch(plt.Circle((0, 0), 0.85, fc=CARD, ec=LINE, lw=1))
    ax.add_patch(Wedge((0, 0), 0.85, 90, 90 - 360 * max(0.03, min(1.0, frac)), width=0.22, color=color))
    ax.text(0, 0, center_txt, color=TXT, fontsize=12, weight="bold", ha="center", va="center")

def donut3(fig, cx, cy, s, parts, colors):
    h = s * 16.0 / 9.0
    ax = fig.add_axes([cx - s / 2, cy - h / 2, s, h])
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_aspect("equal"); ax.set_axis_off()
    total = max(sum(parts), 1); start = 90
    for p, col in zip(parts, colors):
        if p <= 0: continue
        ang = 360.0 * p / total
        ax.add_patch(Wedge((0, 0), 0.85, start - ang, start, width=0.28, color=col))
        start -= ang
    ax.add_patch(plt.Circle((0, 0), 0.52, fc=PANEL, ec="none"))

def _style_ax(ax):
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=MUT, labelsize=8)
    for s in ax.spines.values(): s.set_color(LINE)
    ax.title.set_color(TXT); ax.title.set_fontsize(10); ax.title.set_weight("bold")

def _header(A, title, subtitle, right1, right2):
    A.text(0.03, 0.965, _clean(title), color=TXT, fontsize=22, weight="bold")
    A.text(0.03, 0.940, _clean(subtitle), color=MUT, fontsize=9.5)
    A.add_patch(FancyBboxPatch((0.760, 0.952), 0.21, 0.030, boxstyle="round,pad=0.004,rounding_size=0.015",
                               fc=BLU, ec="none", alpha=0.25, transform=A.transAxes))
    A.text(0.865, 0.967, _clean(right1), color=TXT, fontsize=9.5, weight="bold", ha="center")
    A.text(0.97, 0.940, _clean(right2), color=MUT, fontsize=8.5, ha="right")
    A.add_patch(plt.Rectangle((0.03, 0.925), 0.94, 0.0025, color=BLU))

# ================= PAGE 1 =================
def render_p1(d, a, llm_ok):
    fig = plt.figure(figsize=(16, 9), dpi=150); fig.patch.set_facecolor(BG)
    A = fig.add_axes([0, 0, 1, 1]); A.set_axis_off(); A.set_xlim(0, 1); A.set_ylim(0, 1)

    now = datetime.now(timezone.utc).strftime("%a %Y-%m-%d %H:%M UTC")
    session = "LIVE US SESSION" if d["pulse"].get("session_open") else "PREVIOUS SESSION"
    n_ev, n_src, n_inst = len(d["events"]), len(d.get("sources_active", [])), len(d["macro"].get("instruments", []))
    _header(A, "AGGREGATEIT - INTELLIGENCE DECK",
            "Cross-asset intelligence: news | markets | social  -  machine-compiled, tentative",
            session, now)

    # ---- KPI ring row ----
    pulse, macro, regime = d["pulse"], d["macro"], d["regime"]
    rolls = {"bullish": 0, "neutral": 0, "bearish": 0}
    for e in d["events"]:
        s = (e.get("sentiment") or "").lower()
        if s in rolls: rolls[s] += 1
    tot = max(sum(rolls.values()), 1)
    hi_crit = sum(1 for e in d["events"] if (e.get("severity") or "") in ("High", "Critical"))
    mega = [m for m in pulse.get("mega_caps", []) if m.get("pct") is not None]
    adv = sum(1 for m in mega if m["pct"] > 0)
    vix_i = {i["sym"]: i for i in macro.get("instruments", [])}.get("CBOE:VIX") or {}
    vix_v = vix_i.get("price")
    rings = [
        (min(n_ev / 12.0, 1), BLU, str(n_ev), "EVENTS 24H", "tracked clusters"),
        (hi_crit / max(n_ev, 1), AMB, str(hi_crit), "HIGH / CRITICAL", "severity elevated"),
        (rolls["bullish"] / float(tot), GRN, "%d%%" % round(100 * rolls["bullish"] / tot), "NEWS SENTIMENT", "bullish share"),
        (min((vix_v or 0) / 40.0, 1), RED if (vix_v or 0) >= 25 else (AMB if (vix_v or 0) >= 20 else GRN),
         "%.1f" % vix_v if vix_v is not None else "-", "VIX", regime.get("vix", "n/a")),
        (adv / max(len(mega), 1), GRN if adv >= len(mega) / 2.0 else RED, "%d/%d" % (adv, len(mega)), "MEGA-CAP BREADTH", "advancers"),
    ]
    for cx, (frac, col, cen, lab, sub) in zip((0.10, 0.30, 0.50, 0.70, 0.90), rings):
        ring_axes(fig, cx, 0.845, 0.048, frac, col, cen)
        A.text(cx, 0.782, _clean(lab), color=TXT, fontsize=9.5, weight="bold", ha="center")
        A.text(cx, 0.764, _clean(sub), color=MUT, fontsize=8, ha="center")

    # ---- Executive summary panel ----
    panel(A, 0.03, 0.55, 0.94, 0.19, "EXECUTIVE SUMMARY (TENTATIVE)", BLU)
    y = 0.700
    for line in _wrap(a["summary"], 112)[:4]:
        A.text(0.045, y, line, color=TXT, fontsize=10.5); y -= 0.021
    A.add_patch(plt.Rectangle((0.62, 0.565), 0.335, 0.055, color="#3a2b2b", zorder=2))
    A.text(0.63, 0.606, "KEY RISK", color=RED, fontsize=9.5, weight="bold", zorder=3)
    for i, line in enumerate(_wrap(a["key_risk"], 58)[:2]):
        A.text(0.63, 0.590 - i * 0.016, line, color=TXT, fontsize=8.8, zorder=3)

    # ---- Middle columns ----
    panel(A, 0.03, 0.40, 0.31, 0.13, "NEWS READ", AMB)
    y = 0.505
    for line in _wrap(a["news_read"], 48)[:4]:
        A.text(0.042, y, line, color=TXT, fontsize=9); y -= 0.019
    panel(A, 0.03, 0.28, 0.31, 0.11, "SOCIAL READ", ORG)
    y = 0.365
    for line in _wrap(a["social_read"], 48)[:3]:
        A.text(0.042, y, line, color=TXT, fontsize=9); y -= 0.019

    panel(A, 0.35, 0.28, 0.31, 0.25, "TOP EVENTS (24H)", BLU)
    y = 0.498
    for ev in d["events"][:6]:
        sev = ev.get("severity") or "Low"
        A.add_patch(plt.Rectangle((0.362, y + 0.001), 0.005, 0.016, color=SEV_COLOR.get(sev, MUT), zorder=2))
        A.text(0.372, y, _wrap(ev.get("title"), 42)[0], color=TXT, fontsize=8.6, weight="bold")
        A.text(0.372, y - 0.016, _clean("%s | conf %s%% | %s | src %s" % (sev, ev.get("confidence"), ev.get("status", "NEW"), ev.get("source", ""))),
               color=MUT, fontsize=7.3)
        y -= 0.037

    panel(A, 0.67, 0.40, 0.30, 0.13, "MARKET READ", GRN)
    y = 0.505
    for line in _wrap(a["market_read"], 46)[:4]:
        A.text(0.682, y, line, color=TXT, fontsize=9); y -= 0.019
    panel(A, 0.67, 0.28, 0.30, 0.11, "OUTLOOK (NEXT 24H)", PUR)
    y = 0.365
    for line in _wrap(a["outlook"], 46)[:3]:
        A.text(0.682, y, line, color=TXT, fontsize=9); y -= 0.019

    # ---- Bottom row ----
    panel(A, 0.03, 0.05, 0.50, 0.21, "MACRO DASHBOARD", BLU)
    groups = {}
    for i in macro.get("instruments", []): groups.setdefault(i.get("type", "other"), []).append(i)
    gx = 0.045
    for gname, key, n in [("INDICES", "index", 4), ("FUTURES", "future", 4), ("FOREX", "forex", 3), ("RATES", "bond", 3)]:
        A.text(gx, 0.225, gname, color=MUT, fontsize=7.5, weight="bold")
        yy = 0.205
        for inst in groups.get(key, [])[:n]:
            p = inst.get("pct")
            col = GRN if (p or 0) > 0 else (RED if (p or 0) < 0 else MUT)
            A.text(gx, yy, _clean(inst.get("name", ""))[:13], color=TXT, fontsize=7.8)
            A.text(gx + 0.115, yy, "%+.2f%%" % p if p is not None else "-", color=col, fontsize=7.8, weight="bold", ha="right")
            yy -= 0.017
        gx += 0.125

    panel(A, 0.545, 0.05, 0.21, 0.21, "REGIME & THEMES", AMB)
    y = 0.225
    for line in filter(None, [
        "VIX: %s" % regime["vix"] if regime.get("vix") else None,
        "2s10s: %s%s" % (regime["curve_2s10s"], " INVERTED" if regime.get("curve_inverted") else "") if regime.get("curve_2s10s") else None,
        "DXY: %s" % regime["dxy"] if regime.get("dxy") else None,
        "Oil: %s" % regime["oil_spike"] if regime.get("oil_spike") else None]):
        A.text(0.557, y, _clean(line), color=AMB, fontsize=8.2); y -= 0.017
    y -= 0.008
    top_themes = sorted(d["themes"].items(), key=lambda x: -x[1])[:4]
    mx = top_themes[0][1] if top_themes else 1
    for k, v in top_themes:
        A.text(0.557, y, _clean(DOMAIN_NAMES.get(k, k))[:14], color=MUT, fontsize=7.8)
        A.add_patch(plt.Rectangle((0.645, y + 0.002), 0.08 * v / mx, 0.010, color=BLU, zorder=2))
        A.text(0.735, y, str(v), color=TXT, fontsize=7.8); y -= 0.017

    panel(A, 0.77, 0.05, 0.20, 0.21, "SOURCES & DELTA", MUT)
    y = 0.225
    for line in _wrap(", ".join(d.get("sources_active", [])[:12]) or "No sources in window.", 34)[:4]:
        A.text(0.782, y, line, color=MUT, fontsize=7.6); y -= 0.016
    y -= 0.006
    A.text(0.782, y, "VS PREVIOUS", color=AMB, fontsize=8, weight="bold"); y -= 0.016
    for line in _wrap(a["delta"], 34)[:3]:
        A.text(0.782, y, line, color=TXT, fontsize=7.6); y -= 0.016

    mode = "Qwen (validated)" if llm_ok else "deterministic fallback"
    A.add_patch(plt.Rectangle((0, 0), 1, 0.032, color=BLU, alpha=0.08))
    A.text(0.03, 0.012, "Narrative: %s | Charts from snapshots | Machine-compiled, unverified | PAGE 1/2" % mode, color=MUT, fontsize=8)
    fig.savefig(P1, facecolor=BG); plt.close(fig)

# ================= PAGE 2 =================
def render_p2(d, a, llm_ok):
    fig = plt.figure(figsize=(16, 9), dpi=150); fig.patch.set_facecolor(BG)
    A = fig.add_axes([0, 0, 1, 1]); A.set_axis_off(); A.set_xlim(0, 1); A.set_ylim(0, 1)
    now = datetime.now(timezone.utc).strftime("%a %Y-%m-%d %H:%M UTC")
    pulse, macro, regime = d["pulse"], d["macro"], d["regime"]
    _header(A, "AGGREGATEIT - THE NUMBERS",
            "All charts computed strictly from source snapshots - no modeled or invented values",
            "PAGE 2/2", now)

    # ---- top-left: mega-cap leaders ----
    ax = fig.add_axes([0.05, 0.52, 0.30, 0.38]); _style_ax(ax); ax.set_title("MEGA-CAP LEADERS (%CHG)")
    mega = [m for m in pulse.get("mega_caps", []) if m.get("pct") is not None][:12]
    if mega:
        names = [_clean(m["t"]) for m in mega][::-1]; vals = [m["pct"] for m in mega][::-1]
        ax.barh(names, vals, color=[GRN if v > 0 else RED for v in vals], height=0.72)
        ax.axvline(0, color=MUT, lw=0.6)
        mm = max([abs(v) for v in vals] + [0.1])
        ax.set_xlim(-mm * 1.3, mm * 1.3)
    else: ax.text(0.5, 0.5, "no data", color=MUT, ha="center")

    # ---- top-mid: macro board ----
    ax = fig.add_axes([0.385, 0.52, 0.30, 0.38]); _style_ax(ax); ax.set_title("MACRO BOARD (%CHG)")
    insts = [i for i in macro.get("instruments", []) if i.get("pct") is not None][:14]
    if insts:
        names = [_clean(i["name"])[:14] for i in insts][::-1]; vals = [i["pct"] for i in insts][::-1]
        ax.barh(names, vals, color=[GRN if v > 0 else RED for v in vals], height=0.72)
        ax.axvline(0, color=MUT, lw=0.6)
        mm = max([abs(v) for v in vals] + [0.1])
        ax.set_xlim(-mm * 1.3, mm * 1.3)
    else: ax.text(0.5, 0.5, "no data", color=MUT, ha="center")

    # ---- top-right: cross-asset + outlook panels ----
    panel(A, 0.71, 0.71, 0.26, 0.19, "CROSS-ASSET ANALYSIS", BLU)
    y = 0.865
    for line in _wrap(a["cross_asset"], 42)[:5]:
        A.text(0.722, y, line, color=TXT, fontsize=8.8); y -= 0.018
    panel(A, 0.71, 0.52, 0.26, 0.17, "OUTLOOK (NEXT 24H)", PUR)
    y = 0.655
    for line in _wrap(a["outlook"], 42)[:4]:
        A.text(0.722, y, line, color=TXT, fontsize=8.8); y -= 0.018

    # ---- mid-left: yield curve ----
    ax = fig.add_axes([0.05, 0.10, 0.26, 0.34]); _style_ax(ax); ax.set_title("US YIELD CURVE")
    im = {i["sym"]: i for i in macro.get("instruments", [])}
    pts = [(n, im.get(s, {}).get("price")) for n, s in [("2Y", "TVC:US02Y"), ("10Y", "TVC:US10Y"), ("30Y", "TVC:US30Y")]]
    pts = [(n, p) for n, p in pts if p is not None]
    if pts:
        ax.plot([n for n, _ in pts], [p for _, p in pts], marker="o", color=AMB, lw=2.5, markersize=8)
        for n, p in pts:
            ax.annotate("%.2f%%" % p, (n, p), textcoords="offset points", xytext=(0, 10), color=TXT, fontsize=9, ha="center")
        if len(pts) >= 2:
            spread = (pts[-1][1] - pts[0][1]) * 100
            ax.set_title("US YIELD CURVE | 2s10s %+.0fbp%s" % (spread, " INVERTED" if spread < 0 else ""))
    else: ax.text(0.5, 0.5, "no data", color=MUT, ha="center")

    # ---- mid-mid: movers scatter ----
    ax = fig.add_axes([0.345, 0.10, 0.26, 0.34]); _style_ax(ax); ax.set_title("MOVERS: %CHG vs REL-VOLUME")
    sig = [{"t": k, **v} for k, v in pulse.get("sig", {}).items() if v.get("pct") is not None and v.get("relvol")][:50]
    if sig:
        ax.scatter([v["pct"] for v in sig], [v["relvol"] for v in sig],
                   c=[GRN if v["pct"] > 0 else RED for v in sig], s=18, alpha=0.7)
        ax.axvline(0, color=MUT, lw=0.5, ls="--")
        for v in sorted(sig, key=lambda x: -x["relvol"])[:5]:
            ax.annotate(_clean(v["t"]), (v["pct"], v["relvol"]), color=TXT, fontsize=7.5, xytext=(4, 4), textcoords="offset points")
        ax.set_xlabel("% change", color=MUT, fontsize=8)
        ax.set_ylabel("relative volume", color=MUT, fontsize=8)
    else: ax.text(0.5, 0.5, "no data", color=MUT, ha="center")

    # ---- mid-right-1: themes + sentiment donut ----
    panel(A, 0.63, 0.10, 0.16, 0.34, "THEMES & SENTIMENT", BLU)
    y = 0.40
    top_themes = sorted(d["themes"].items(), key=lambda x: -x[1])[:5]
    mx = top_themes[0][1] if top_themes else 1
    for k, v in top_themes:
        A.text(0.642, y, _clean(DOMAIN_NAMES.get(k, k))[:13], color=MUT, fontsize=7.8)
        A.add_patch(plt.Rectangle((0.715, y + 0.002), 0.05 * v / mx, 0.010, color=BLU, zorder=2))
        A.text(0.772, y, str(v), color=TXT, fontsize=7.8); y -= 0.020
    rolls = {"bullish": 0, "neutral": 0, "bearish": 0}
    for e in d["events"]:
        s = (e.get("sentiment") or "").lower()
        if s in rolls: rolls[s] += 1
    donut3(fig, 0.685, 0.20, 0.040, [rolls["bullish"], rolls["neutral"], rolls["bearish"]], [GRN, MUT, RED])
    A.text(0.735, 0.225, "B %d" % rolls["bullish"], color=GRN, fontsize=8)
    A.text(0.735, 0.205, "N %d" % rolls["neutral"], color=MUT, fontsize=8)
    A.text(0.735, 0.185, "S %d" % rolls["bearish"], color=RED, fontsize=8)
    y = 0.155
    for line in ([_clean(r)[:26] for r in d["st_radar"][:3]] or ["No retail consensus."]):
        A.text(0.642, y, line, color=TXT, fontsize=7.5); y -= 0.016

    # ---- mid-right-2: key numbers rail ----
    panel(A, 0.805, 0.10, 0.165, 0.34, "KEY NUMBERS", AMB)
    def _by_name(nm):
        for i in macro.get("instruments", []):
            if i.get("name") == nm: return i
        return {}
    g0 = pulse.get("gainers", [{}])[0]; l0 = pulse.get("losers", [{}])[0]
    rows = [
        ("TOP GAINER", "%s %+.2f%%" % (g0.get("t", "-"), g0.get("pct", 0)) if g0.get("t") else "-", GRN),
        ("TOP LOSER", "%s %+.2f%%" % (l0.get("t", "-"), l0.get("pct", 0)) if l0.get("t") else "-", RED),
        ("WTI CRUDE", "%+.2f%%" % _by_name("WTI Crude").get("pct", 0) if _by_name("WTI Crude").get("pct") is not None else "-", GRN if (_by_name("WTI Crude").get("pct") or 0) > 0 else RED),
        ("GOLD", "%+.2f%%" % _by_name("Gold").get("pct", 0) if _by_name("Gold").get("pct") is not None else "-", GRN if (_by_name("Gold").get("pct") or 0) > 0 else RED),
        ("DXY", "%+.2f%%" % _by_name("US Dollar Index").get("pct", 0) if _by_name("US Dollar Index").get("pct") is not None else "-", GRN if (_by_name("US Dollar Index").get("pct") or 0) > 0 else RED),
        ("US 10Y", "%s" % _fmt_price(_by_name("US 10Y Yield").get("price"), "bond"), AMB),
    ]
    y = 0.40
    for lab, val, col in rows:
        A.text(0.817, y, lab, color=MUT, fontsize=7.5, weight="bold")
        A.text(0.958, y, _clean(val), color=col, fontsize=8.5, weight="bold", ha="right")
        y -= 0.024
    y -= 0.01
    A.text(0.817, y, "VS PREVIOUS", color=AMB, fontsize=7.8, weight="bold"); y -= 0.018
    for line in _wrap(a["delta"], 26)[:3]:
        A.text(0.817, y, line, color=TXT, fontsize=7.3); y -= 0.016

    foot = " | ".join(filter(None, [
        "VIX %s" % regime["vix"] if regime.get("vix") else None,
        "DXY %s" % regime["dxy"] if regime.get("dxy") else None,
        "oil %s" % regime["oil_spike"] if regime.get("oil_spike") else None,
        "pulse %s" % datetime.fromtimestamp(pulse["updated"], timezone.utc).strftime("%H:%M") if pulse.get("updated") else None,
        "macro %d inst" % len(macro.get("instruments", [])),
        "ALL FIGURES FROM SNAPSHOTS | PAGE 2/2"]))
    A.add_patch(plt.Rectangle((0, 0), 1, 0.032, color=BLU, alpha=0.08))
    A.text(0.5, 0.012, _clean(foot), color=MUT, fontsize=8.5, ha="center")
    fig.savefig(P2, facecolor=BG); plt.close(fig)

# ================= SEND =================
def send(pages):
    wh = os.environ.get("DISCORD_WEBHOOK")
    if not wh: print("FATAL: DISCORD_WEBHOOK secret is not set."); return
    files = []
    for i, p in enumerate(pages):
        files.append(("files[%d]" % i, (os.path.basename(p), open(p, "rb"), "image/png")))
    r = requests.post(wh, files=files,
                      data={"payload_json": json.dumps({"content": "**AGGREGATEIT INTELLIGENCE DECK** (tentative, machine-compiled)"})})
    if r.status_code >= 400:
        raise RuntimeError("Discord HTTP %d: %s" % (r.status_code, r.text[:120]))
    print("Deck delivered (2 pages)!")

if __name__ == "__main__":
    os.makedirs(REPORTS, exist_ok=True)
    data = collect()
    analysis, llm_ok, prev = analyze(data)
    render_p1(data, analysis, llm_ok)
    render_p2(data, analysis, llm_ok)
    _save_prev(analysis, data)
    send([P1, P2])
