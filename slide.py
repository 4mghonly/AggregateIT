"""slide.py — two-page PowerPoint-style intelligence deck (PNG) to Discord.
Heavy analysis over news + markets + social chatter. Charts are computed
strictly from snapshots (no hallucination path); LLM narrative is schema-
validated with deterministic fallbacks."""
import os, json, re, textwrap, requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime, timezone
from storage import SQLiteStore
import market
from briefing import fetch_stocktwits, load_events, theme_counts, DOMAIN_NAMES

BASE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(BASE, "reports")
P1 = os.path.join(REPORTS, "intel_slide_p1.png")
P2 = os.path.join(REPORTS, "intel_slide_p2.png")

BG, PANEL, TXT, MUT = "#1e1f22", "#2b2d31", "#dbdee1", "#949ba4"
GRN, RED, AMB, BLU = "#2ecc71", "#e74c3c", "#f1c40f", "#5865f2"
SEV_COLOR = {"Critical": RED, "High": AMB, "Medium": "#e67e22", "Low": MUT}

def _wrap(s, n): return textwrap.wrap(s or "", n) or [""]

# ================= COLLECT (snapshots only) =================
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
    return {"store": store, "pulse": pulse, "macro": macro, "regime": regime,
            "events": events, "themes": themes, "st_sent": st_sent, "st_radar": st_radar,
            "reddit": reddit}

# ================= ANALYSIS (validated LLM + fallbacks) =================
ANALYSIS_PROMPT = """You are a senior cross-asset intelligence analyst. Write a TENTATIVE but
quantitative read over the data below. Strict rules: only use numbers present in the data;
never invent tickers, prices, or events; keep each field under 600 chars.
Return ONLY this JSON:
{
  "summary": "2-3 sentences tying the dominant news to observed market moves",
  "news_read": "1-2 sentences on the most material news cluster",
  "market_read": "1-2 sentences on equities, rates, FX, commodities behavior",
  "social_read": "1-2 sentences on retail/social chatter vs price action",
  "key_risk": "one sentence: the most important risk or opportunity next"
}

DATA:
__DATA__"""

def _data_text(d):
    L = []
    for e in d["events"][:8]:
        L.append("EVENT [%s/%s] %s (src %s)" % (e.get("severity"), e.get("status"), e.get("title"), e.get("source")))
    for m in (d["pulse"].get("gainers", []) + d["pulse"].get("losers", []))[:8]:
        L.append("MOVER %s %+.2f%%" % (m["t"], m["pct"]))
    for i in d["macro"].get("instruments", []):
        if i.get("pct") is not None: L.append("MACRO %s %+.2f%%" % (i["name"], i["pct"]))
    for k, v in d["regime"].items(): L.append("REGIME %s=%s" % (k, v))
    for k, v in sorted(d["themes"].items(), key=lambda x: -x[1])[:5]:
        L.append("THEME %s x%d" % (DOMAIN_NAMES.get(k, k), v))
    if d["st_radar"]: L.append("STOCKTWITS " + " | ".join(d["st_radar"][:6]))
    if d["reddit"]:
        L.append("REDDIT " + ", ".join("%s x%d" % (k, v) for k, v in sorted(d["reddit"].items(), key=lambda x: -x[1])[:5]))
    return "\n".join(L)

def _fallback_analysis(d):
    ev, pulse, regime = d["events"], d["pulse"], d["regime"]
    g, l = pulse.get("gainers", []), pulse.get("losers", [])
    lead = ("led by %s +%.1f%%" % (g[0]["t"], g[0]["pct"])) if g else "quiet"
    lag = (", while %s %.1f%% lags" % (l[0]["t"], l[0]["pct"])) if l else ""
    mkt = "Equities %s%s; VIX %s; 2s10s %s." % (lead, lag, regime.get("vix", "n/a"), regime.get("curve_2s10s", "n/a"))
    if d["themes"]:
        dom = DOMAIN_NAMES.get(sorted(d["themes"].items(), key=lambda x: -x[1])[0][0], "Mixed")
        news = "Dominant cluster: %s." % dom
    else:
        news = "No dominant news cluster in window."
    if ev:
        news += " Top event: %s" % (ev[0].get("title") or "")[:80]
    soc = " | ".join(d["st_radar"][:4]) if d["st_radar"] else "No strong retail consensus on movers."
    if d["reddit"]:
        soc += " Reddit: " + ", ".join("%s x%d" % (k, v) for k, v in sorted(d["reddit"].items(), key=lambda x: -x[1])[:3])
    summ = (news + " " + mkt)[:600]
    risk = ("Monitor for escalation in the dominant cluster; cross-check against next session open."
            if ev else "Quiet tape - primary risk is gap-on-open from off-hours news.")
    return {"summary": summ, "news_read": news[:600], "market_read": mkt[:600],
            "social_read": soc[:600], "key_risk": risk[:600]}

def analyze(d):
    try:
        base = os.environ.get("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1").rstrip("/")
        r = requests.post(base + "/chat/completions",
            headers={"Authorization": "Bearer " + os.environ["QWEN_API_KEY"]},
            json={"model": os.environ.get("QWEN_MODEL", "qwen-plus"), "temperature": 0.3,
                  "messages": [{"role": "system", "content": "Disciplined analyst. Output ONLY valid JSON."},
                               {"role": "user", "content": ANALYSIS_PROMPT.replace("__DATA__", _data_text(d))}]},
            timeout=90)
        r.raise_for_status()
        m = re.search(r"\{[\s\S]*\}", r.json()["choices"][0]["message"]["content"])
        if m:
            obj = json.loads(m.group(0))
            if all(isinstance(obj.get(k), str) and 10 <= len(obj.get(k)) <= 600
                   for k in ("summary", "news_read", "market_read", "social_read", "key_risk")):
                return obj, True
    except Exception:
        pass
    return _fallback_analysis(d), False

# ================= RENDER =================
def _style_ax(ax):
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=MUT, labelsize=9)
    for s in ax.spines.values(): s.set_color("#3f4147")
    ax.title.set_color(TXT); ax.title.set_fontsize(11)

def render_p1(d, a, llm_ok):
    fig = plt.figure(figsize=(16, 9), dpi=120); fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    now = datetime.now(timezone.utc).strftime("%a %Y-%m-%d %H:%M UTC")
    session = "LIVE US SESSION" if d["pulse"].get("session_open") else "PREVIOUS SESSION"
    ax.text(0.03, 0.95, "AGGREGATEIT - INTELLIGENCE DECK  ·  PAGE 1/2", color=TXT, fontsize=22, weight="bold")
    ax.text(0.97, 0.95, "%s · %s" % (now, session), color=MUT, fontsize=11, ha="right")
    ax.add_patch(plt.Rectangle((0.03, 0.928), 0.94, 0.008, color=BLU))

    ax.text(0.03, 0.90, "EXECUTIVE SUMMARY (TENTATIVE)", color=BLU, fontsize=13, weight="bold")
    y = 0.872
    for line in _wrap(a["summary"], 105)[:3]:
        ax.text(0.03, y, line, color=TXT, fontsize=12); y -= 0.026
    y -= 0.012
    for title, body, col in (("NEWS READ", a["news_read"], AMB), ("MARKET READ", a["market_read"], GRN),
                             ("SOCIAL READ", a["social_read"], "#e67e22")):
        ax.text(0.03, y, title, color=col, fontsize=11, weight="bold"); y -= 0.024
        for line in _wrap(body, 105)[:2]:
            ax.text(0.03, y, line, color=TXT, fontsize=11); y -= 0.024
        y -= 0.008
    ax.add_patch(plt.Rectangle((0.03, y - 0.03), 0.55, 0.045, color="#3a2b2b"))
    ax.text(0.038, y - 0.008, "KEY RISK:", color=RED, fontsize=11, weight="bold")
    ax.text(0.115, y - 0.008, _wrap(a["key_risk"], 80)[0], color=TXT, fontsize=11)

    x2 = 0.62; y = 0.90
    ax.text(x2, y, "TOP EVENTS (24H)", color=BLU, fontsize=13, weight="bold"); y -= 0.03
    for ev in d["events"][:5]:
        sev = ev.get("severity") or "Low"
        ax.add_patch(plt.Rectangle((x2, y - 0.011), 0.005, 0.024, color=SEV_COLOR.get(sev, MUT)))
        ax.text(x2 + 0.012, y, _wrap(ev.get("title"), 46)[0], color=TXT, fontsize=10.5, weight="bold")
        ax.text(x2 + 0.012, y - 0.022, "%s · %s%% · %s" % (sev, ev.get("confidence"), ev.get("status", "NEW")),
                color=MUT, fontsize=8.5)
        y -= 0.052
    y -= 0.01
    ax.text(x2, y, "THEME ACTIVITY", color=BLU, fontsize=13, weight="bold"); y -= 0.028
    top = sorted(d["themes"].items(), key=lambda x: -x[1])[:5]
    mx = top[0][1] if top else 1
    for k, v in top:
        ax.text(x2, y, DOMAIN_NAMES.get(k, k), color=MUT, fontsize=9.5)
        ax.add_patch(plt.Rectangle((x2 + 0.13, y + 0.002), 0.20 * v / mx, 0.012, color=BLU))
        ax.text(x2 + 0.34, y, str(v), color=TXT, fontsize=9.5)
        y -= 0.026
    y -= 0.015
    rolls = {"bullish": 0, "neutral": 0, "bearish": 0}
    for e in d["events"]:
        s = (e.get("sentiment") or "").lower()
        if s in rolls: rolls[s] += 1
    tot = max(sum(rolls.values()), 1)
    ax.text(x2, y, "SENTIMENT + SOCIAL", color=BLU, fontsize=13, weight="bold"); y -= 0.026
    x = x2
    for key, col in (("bullish", GRN), ("neutral", MUT), ("bearish", RED)):
        w = 0.30 * rolls[key] / tot
        ax.add_patch(plt.Rectangle((x, y), max(w, 0.004), 0.014, color=col)); x += w + 0.004
    ax.text(x + 0.01, y, "%d/%d/%d" % (rolls["bullish"], rolls["neutral"], rolls["bearish"]), color=MUT, fontsize=9.5)
    y -= 0.028
    for line in (d["st_radar"][:4] or ["No retail consensus on movers."]):
        ax.text(x2, y, line, color=TXT, fontsize=9.5); y -= 0.024
    mode = "Qwen (validated)" if llm_ok else "deterministic fallback"
    ax.text(0.03, 0.02, "Narrative: %s · charts computed from snapshots · machine-compiled, unverified" % mode,
            color=MUT, fontsize=9)
    fig.savefig(P1, facecolor=BG); plt.close(fig)

def render_p2(d):
    fig, axs = plt.subplots(2, 2, figsize=(16, 9), dpi=120)
    fig.patch.set_facecolor(BG)
    fig.suptitle("AGGREGATEIT - THE NUMBERS  ·  %s" % datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                 color=TXT, fontsize=16, weight="bold", y=0.97)
    pulse, macro, regime = d["pulse"], d["macro"], d["regime"]

    ax = axs[0, 0]; _style_ax(ax); ax.set_title("MEGA-CAP LEADERS (pct chg)")
    mega = [m for m in pulse.get("mega_caps", []) if m.get("pct") is not None][:10]
    if mega:
        names = [m["t"] for m in mega][::-1]; vals = [m["pct"] for m in mega][::-1]
        ax.barh(names, vals, color=[GRN if v > 0 else RED for v in vals])
        ax.axvline(0, color=MUT, lw=0.7)
    else: ax.text(0.5, 0.5, "no data", color=MUT, ha="center")

    ax = axs[0, 1]; _style_ax(ax); ax.set_title("MACRO BOARD (pct chg)")
    insts = [i for i in macro.get("instruments", []) if i.get("pct") is not None][:14]
    if insts:
        names = [i["name"] for i in insts][::-1]; vals = [i["pct"] for i in insts][::-1]
        ax.barh(names, vals, color=[GRN if v > 0 else RED for v in vals])
        ax.axvline(0, color=MUT, lw=0.7)
    else: ax.text(0.5, 0.5, "no data", color=MUT, ha="center")

    ax = axs[1, 0]; _style_ax(ax); ax.set_title("US YIELD CURVE (levels)")
    im = {i["sym"]: i for i in macro.get("instruments", [])}
    pts = [(n, im.get(s, {}).get("price")) for n, s in (("2Y", "TVC:US02Y"), ("10Y", "TVC:US10Y"), ("30Y", "TVC:US30Y"))]
    pts = [(n, p) for n, p in pts if p is not None]
    if pts:
        ax.plot([n for n, _ in pts], [p for _, p in pts], marker="o", color=AMB, lw=2)
        if len(pts) >= 2:
            spread = (pts[-1][1] - pts[0][1]) * 100
            ax.set_title("US YIELD CURVE · 2s10s %+.0fbp%s" % (spread, " INVERTED" if spread < 0 else ""))
    else: ax.text(0.5, 0.5, "no data", color=MUT, ha="center")

    ax = axs[1, 1]; _style_ax(ax); ax.set_title("SIGNIFICANT MOVERS (pct x rel-volume)")
    sig = [{"t": k, **v} for k, v in pulse.get("sig", {}).items()
           if v.get("pct") is not None and v.get("relvol")][:40]
    if sig:
        ax.scatter([v["pct"] for v in sig], [v["relvol"] for v in sig],
                   c=[GRN if v["pct"] > 0 else RED for v in sig], s=22, alpha=0.8)
        for v in sorted(sig, key=lambda x: -x["relvol"])[:3]:
            ax.annotate(v["t"], (v["pct"], v["relvol"]), color=TXT, fontsize=8,
                        xytext=(4, 4), textcoords="offset points")
    else: ax.text(0.5, 0.5, "no data", color=MUT, ha="center")

    foot = " · ".join(filter(None, [
        "VIX %s" % regime["vix"] if regime.get("vix") else "",
        "DXY %s" % regime["dxy"] if regime.get("dxy") else "",
        "oil %s" % regime["oil_spike"] if regime.get("oil_spike") else "",
        "pulse as-of %s" % datetime.fromtimestamp(pulse["updated"], timezone.utc).strftime("%H:%M") if pulse.get("updated") else "",
        "macro %d inst" % len(macro.get("instruments", [])),
        "ALL FIGURES COMPUTED FROM SOURCE SNAPSHOTS"]))
    fig.text(0.5, 0.015, foot, color=MUT, fontsize=9.5, ha="center")
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(P2, facecolor=BG); plt.close(fig)

def send(pages):
    wh = os.environ.get("DISCORD_WEBHOOK")
    if not wh:
        print("FATAL: DISCORD_WEBHOOK secret is not set."); return
    files = []
    for i, p in enumerate(pages):
        files.append(("files[%d]" % i, (os.path.basename(p), open(p, "rb"), "image/png")))
    r = requests.post(wh, files=files,
                      data={"payload_json": json.dumps({"content": "📊 **AggregateIT Intelligence Deck** (tentative, machine-compiled)"})})
    if r.status_code >= 400:
        raise RuntimeError("Discord HTTP %d: %s" % (r.status_code, r.text[:120]))
    print("✅ Deck delivered (2 pages)!")

if __name__ == "__main__":
    os.makedirs(REPORTS, exist_ok=True)
    data = collect()
    analysis, llm_ok = analyze(data)
    render_p1(data, analysis, llm_ok)
    render_p2(data)
    send([P1, P2])
