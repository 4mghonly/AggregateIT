"""slide.py v7 — THE AGGREGATE GAZETTE. 4K two-page editorial deck.
Paper/ink theme, serif masthead, desk kickers, stat strip, heatmap,
geopolitics-balanced desks, 1-hour movers, headlines, two-column macro table.
All figures from snapshots; LLM narrative validated with fallbacks."""
import os, json, re, time, textwrap, requests
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
PREV_FILE = os.path.join(REPORTS, "prev_slide.json")

PAPER, INK, MUT2, CARDL = "#F6F1E7", "#1C1B18", "#6E675C", "#EFE8DA"
GEO, MKT, SOC, UP, DN, HI = "#7D2A2A", "#1F3864", "#8A6D1F", "#2E5E3A", "#A33B2E", "#C89B2A"
SEV_COLOR = {"Critical": DN, "High": "#B4622D", "Medium": HI, "Low": MUT2}
GEO_TAGS = {"GG", "ME", "TR", "CY", "US"}

def _clean(s): return re.sub(r'[^\x20-\x7E]', '', s or '').strip()
def _wrap(s, n): return textwrap.wrap(_clean(s), n) or [""]
def _fmt_price(p, t):
    if p is None: return "-"
    if t in ("forex",): return "%.4f" % p
    if t in ("bond",): return "%.2f%%" % p
    if p >= 10000: return "%.0f" % p
    if p >= 100: return "%.1f" % p
    return "%.2f" % p

def _load_prev():
    try:
        with open(PREV_FILE) as f: return json.load(f)
    except Exception: return None

def _save_prev(a, d):
    try:
        with open(PREV_FILE, "w") as f:
            json.dump({"ts": time.time(), "summary": a.get("lead", ""),
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
    for e in events:
        e["geo"] = any((t or "").split("-")[0] in GEO_TAGS for t in e.get("triggers", []))
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
    headlines = sorted(events, key=lambda x: -(x.get("ts") or 0))[:8]
    sectors = {}
    for m in pulse.get("mega_caps", []):
        if m.get("pct") is not None:
            sectors.setdefault(m.get("s", "Other"), []).append(m["pct"])
    sector_tape = sorted(((k, sum(v) / len(v)) for k, v in sectors.items()), key=lambda x: -x[1])
    return {"store": store, "pulse": pulse, "macro": macro, "regime": regime, "events": events,
            "geo_events": [e for e in events if e.get("geo")], "themes": themes,
            "st_radar": st_radar, "reddit": reddit, "sources_active": sources_active,
            "headlines": headlines, "sector_tape": sector_tape}

ANALYSIS_PROMPT = """You are the editor of a financial-and-geopolitical intelligence gazette.
Write TENTATIVE, quantitative, complete-sentence analysis. Rules:
- Use ONLY data present below; never invent tickers, numbers, events, or countries.
- Balance geopolitical and economic analysis equally.
- NO EMOJIS. Complete sentences only. Each field under 600 chars.
Return ONLY this JSON:
{
  "headline": "serif-style front-page headline, max 90 chars",
  "lead": "3-sentence lead paragraph tying geopolitics AND markets together",
  "geopol_read": "2-3 sentences: geopolitical developments, their market transmission channels",
  "market_read": "2-3 sentences: equities, rates, FX, commodities behavior and divergences",
  "social_read": "1-2 sentences: retail/social chatter vs price action",
  "cross_asset": "2 sentences: specific news-to-price connections",
  "outlook": "1-2 sentences: catalysts and levels to watch next 24 hours",
  "key_risk": "1 sentence: single most important risk or opportunity",
  "delta": "1-2 sentences: what changed vs the previous edition"
}

PREVIOUS EDITION:
__PREV__

CURRENT DATA:
__DATA__"""

REQUIRED_KEYS = ("headline", "lead", "geopol_read", "market_read", "social_read",
                 "cross_asset", "outlook", "key_risk", "delta")

def _data_text(d):
    L = []
    for e in d["events"][:10]:
        L.append("EVENT [%s/%s] %s (src: %s)" % (e.get("severity"), e.get("status"), e.get("title"), e.get("source")))
    for m in (d["pulse"].get("gainers", []) + d["pulse"].get("losers", []))[:8]:
        L.append("MOVER %s %+.2f%%" % (m["t"], m["pct"]))
    for m in d["pulse"].get("hour_movers", [])[:5]:
        L.append("1H-MOVER %s %+.2f%% (1h)" % (m["t"], m["hour_chg"]))
    for i in d["macro"].get("instruments", []):
        if i.get("pct") is not None: L.append("MACRO %s %+.2f%%" % (i["name"], i["pct"]))
    for k, v in d["regime"].items(): L.append("REGIME %s = %s" % (k, v))
    for k, v in d["sector_tape"][:6]: L.append("SECTOR %s %+.2f%%" % (k, v))
    for k, v in sorted(d["themes"].items(), key=lambda x: -x[1])[:6]:
        L.append("THEME %s x%d" % (_clean(DOMAIN_NAMES.get(k, k)), v))
    if d["st_radar"]: L.append("STOCKTWITS " + " | ".join([_clean(r) for r in d["st_radar"][:6]]))
    if d["reddit"]:
        L.append("REDDIT " + ", ".join("%s x%d" % (k, v) for k, v in sorted(d["reddit"].items(), key=lambda x: -x[1])[:5]))
    if d["sources_active"]: L.append("SOURCES: " + ", ".join(d["sources_active"][:15]))
    return "\n".join(L)

def _prev_text(prev):
    if not prev: return "First edition of this cycle - no prior comparison."
    L = ["Previous edition %s UTC:" % datetime.fromtimestamp(prev.get("ts", 0), timezone.utc).strftime("%H:%M")]
    if prev.get("summary"): L.append("Prev lead: %s" % prev["summary"][:200])
    if prev.get("event_titles"): L.append("Prev events: %s" % ", ".join(prev["event_titles"][:5]))
    return "\n".join(L)

def _fallback_analysis(d, prev):
    ev, pulse, regime = d["events"], d["pulse"], d["regime"]
    g, l = pulse.get("gainers", []), pulse.get("losers", [])
    lead = ("led by %s +%.1f%%" % (g[0]["t"], g[0]["pct"])) if g else "quiet"
    lag = ("; %s %.1f%% lags" % (l[0]["t"], l[0]["pct"])) if l else ""
    mkt = "Equities %s%s. VIX %s; 2s10s %s." % (lead, lag, regime.get("vix", "n/a"), regime.get("curve_2s10s", "n/a"))
    geo = ("Geopolitical desk: %s." % (d["geo_events"][0].get("title") or "")[:90]) if d["geo_events"] else "Geopolitical desk: no major developments in window."
    news = ("Dominant cluster: %s." % _clean(DOMAIN_NAMES.get(sorted(d["themes"].items(), key=lambda x: -x[1])[0][0], "Mixed"))) if d["themes"] else "No dominant cluster."
    if ev: news += " Top event: %s." % (ev[0].get("title") or "")[:80]
    soc = " | ".join([_clean(r) for r in d["st_radar"][:4]]) if d["st_radar"] else "No strong retail consensus."
    if d["reddit"]: soc += " Reddit: " + ", ".join("%s x%d" % (k, v) for k, v in sorted(d["reddit"].items(), key=lambda x: -x[1])[:3])
    headline = (ev[0].get("title") or "Quiet session across markets")[:90] if ev else "Quiet session across markets"
    return {"headline": headline, "lead": (geo + " " + mkt)[:600], "geopol_read": geo[:600],
            "market_read": mkt[:600], "social_read": soc[:600], "cross_asset": mkt[:600],
            "outlook": "Watch for continuation in dominant themes; monitor pre-market futures for gap risk.",
            "key_risk": ("Monitor for escalation in the dominant cluster." if ev else "Quiet tape - gap-on-open risk."),
            "delta": ("First edition - no prior comparison." if not prev else "Prior edition %s UTC." % datetime.fromtimestamp(prev.get("ts", 0), timezone.utc).strftime("%H:%M"))}

def analyze(d):
    prev = _load_prev()
    try:
        base = os.environ.get("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1").rstrip("/")
        prompt = ANALYSIS_PROMPT.replace("__DATA__", _data_text(d)).replace("__PREV__", _prev_text(prev))
        r = requests.post(base + "/chat/completions",
            headers={"Authorization": "Bearer " + os.environ["QWEN_API_KEY"]},
            json={"model": os.environ.get("QWEN_MODEL", "qwen-plus"), "temperature": 0.3,
                  "messages": [{"role": "system", "content": "Gazette editor. Output ONLY valid JSON. NO EMOJIS."},
                               {"role": "user", "content": prompt}]}, timeout=90)
        r.raise_for_status()
        m = re.search(r"\{[\s\S]*\}", r.json()["choices"][0]["message"]["content"])
        if m:
            obj = json.loads(m.group(0))
            if all(isinstance(obj.get(k), str) and len(obj.get(k)) >= 10 for k in REQUIRED_KEYS):
                return obj, True, prev
    except Exception: pass
    return _fallback_analysis(d, prev), False, prev

# ================= PRIMITIVES =================
def _kicker(A, x, y, w, text, color):
    A.text(x, y, _clean(text), color=color, fontsize=10.5, weight="bold")
    A.add_patch(plt.Rectangle((x, y - 0.013), w, 0.0022, color=color))

def _lax(ax):
    ax.set_facecolor(PAPER)
    ax.tick_params(colors=MUT2, labelsize=8)
    for s in ax.spines.values(): s.set_color("#C9C0AE")
    ax.title.set_color(INK); ax.title.set_fontsize(10); ax.title.set_weight("bold")

def _masthead(A, title, right1, right2):
    A.text(0.5, 0.965, _clean(title), color=INK, fontsize=26, weight="bold",
           fontfamily="serif", ha="center")
    A.text(0.03, 0.965, right1, color=MUT2, fontsize=8.5)
    A.text(0.97, 0.965, right2, color=MUT2, fontsize=8.5, ha="right")
    A.add_patch(plt.Rectangle((0.03, 0.945), 0.94, 0.004, color=INK))
    A.add_patch(plt.Rectangle((0.03, 0.940), 0.94, 0.0015, color=INK))

# ================= PAGE 1 =================
def render_p1(d, a, llm_ok):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=200); fig.patch.set_facecolor(PAPER)
    A = fig.add_axes([0, 0, 1, 1]); A.set_axis_off(); A.set_xlim(0, 1); A.set_ylim(0, 1)
    now = datetime.now(timezone.utc).strftime("%A, %Y-%m-%d %H:%M UTC")
    session = "LIVE US SESSION EDITION" if d["pulse"].get("session_open") else "PREVIOUS SESSION EDITION"
    vol = (datetime.now(timezone.utc) - datetime(2026, 1, 1, tzinfo=timezone.utc)).days
    _masthead(A, "THE AGGREGATE GAZETTE", "Vol. %d · Market & Geopolitical Intelligence" % vol, "%s · %s" % (now, session))

    # stat strip
    pulse, macro, regime = d["pulse"], d["macro"], d["regime"]
    rolls = {"bullish": 0, "neutral": 0, "bearish": 0}
    for e in d["events"]:
        s = (e.get("sentiment") or "").lower()
        if s in rolls: rolls[s] += 1
    tot = max(sum(rolls.values()), 1)
    mega = [m for m in pulse.get("mega_caps", []) if m.get("pct") is not None]
    adv = sum(1 for m in mega if m["pct"] > 0)
    hi_crit = sum(1 for e in d["events"] if (e.get("severity") or "") in ("High", "Critical"))
    im = {i["name"]: i for i in macro.get("instruments", [])}
    stats = [("EVENTS 24H", str(len(d["events"])), "tracked"), ("HIGH/CRIT", str(hi_crit), "severity"),
             ("BULLISH", "%d%%" % round(100 * rolls["bullish"] / tot), "news share"),
             ("BREADTH", "%d/%d" % (adv, len(mega)), "advancers"),
             ("VIX", "%.1f" % (im.get("VIX", {}).get("price") or 0), regime.get("vix", "")),
             ("2s10s", regime.get("curve_2s10s", "-"), "curve"),
             ("DXY", "%+.2f%%" % (im.get("US Dollar Index", {}).get("pct") or 0), regime.get("dxy", "")),
             ("WTI", "%+.2f%%" % (im.get("WTI Crude", {}).get("pct") or 0), "crude")]
    x = 0.03; w = 0.94 / 8
    for i, (lab, val, sub) in enumerate(stats):
        cx = x + i * w
        if i: A.add_patch(plt.Rectangle((cx, 0.885), 0.0012, 0.045, color=INK))
        A.text(cx + w / 2, 0.925, _clean(lab), color=MUT2, fontsize=7.5, ha="center", weight="bold")
        A.text(cx + w / 2, 0.905, _clean(val), color=INK, fontsize=12, ha="center", weight="bold")
        A.text(cx + w / 2, 0.888, _clean(sub), color=MUT2, fontsize=7, ha="center")
    A.add_patch(plt.Rectangle((0.03, 0.878), 0.94, 0.0015, color=INK))

    # LEAD (center)
    A.text(0.335, 0.845, _clean(a["headline"]), color=INK, fontsize=17, weight="bold", fontfamily="serif")
    A.add_patch(plt.Rectangle((0.335, 0.835), 0.35, 0.0015, color=HI))
    body = _wrap(a["lead"], 62)
    y = 0.815
    if body:
        A.text(0.335, y, body[0][0], color=INK, fontsize=22, weight="bold", fontfamily="serif")
        A.text(0.352, y, body[0][1:], color=INK, fontsize=9.5)
        y -= 0.021
        for line in body[1:7]:
            A.text(0.335, y, line, color=INK, fontsize=9.5); y -= 0.019
    # heatmap strip
    hy = y - 0.012
    cells = mega[:12]; cw = 0.35 / max(len(cells), 1)
    for i, m in enumerate(cells):
        col = UP if m["pct"] > 0 else DN
        A.add_patch(plt.Rectangle((0.335 + i * cw, hy - 0.035), cw * 0.92, 0.032, color=col,
                                  alpha=min(0.25 + abs(m["pct"]) / 4.0, 0.9)))
        A.text(0.335 + i * cw + cw / 2, hy - 0.012, m["t"], color="#fff", fontsize=6.5, ha="center", weight="bold")
        A.text(0.335 + i * cw + cw / 2, hy - 0.026, "%+.1f" % m["pct"], color="#fff", fontsize=6, ha="center")

    # LEFT rail: WORLD & GEOPOLITICS
    _kicker(A, 0.03, 0.845, 0.27, "WORLD & GEOPOLITICS", GEO)
    y = 0.822
    for line in _wrap(a["geopol_read"], 46)[:6]:
        A.text(0.03, y, line, color=INK, fontsize=9); y -= 0.018
    y -= 0.008
    A.text(0.03, y, "GEOPOLITICAL WATCHLIST", color=GEO, fontsize=8.5, weight="bold"); y -= 0.018
    for e in d["geo_events"][:4]:
        sev = e.get("severity") or "Low"
        A.add_patch(plt.Rectangle((0.03, y + 0.001), 0.005, 0.014, color=SEV_COLOR.get(sev, MUT2)))
        A.text(0.04, y, _wrap(e.get("title"), 42)[0], color=INK, fontsize=8.4, weight="bold")
        A.text(0.04, y - 0.014, _clean("%s | %s%% | %s" % (sev, e.get("confidence"), e.get("source", ""))), color=MUT2, fontsize=7)
        y -= 0.034
    y -= 0.01
    A.text(0.03, y, "RISK THERMOMETER", color=GEO, fontsize=8.5, weight="bold"); y -= 0.016
    score = min(100, 25 * sum(1 for e in d["events"] if e.get("severity") == "Critical") +
                10 * hi_crit + (im.get("VIX", {}).get("price") or 15))
    A.add_patch(plt.Rectangle((0.03, y - 0.006), 0.27, 0.010, color=CARDL))
    A.add_patch(plt.Rectangle((0.03, y - 0.006), 0.27 * score / 100.0, 0.010, color=GEO))
    A.text(0.305, y - 0.006, "%d" % score, color=GEO, fontsize=8, weight="bold")

    # RIGHT rail: MARKETS & ECONOMY
    _kicker(A, 0.70, 0.845, 0.27, "MARKETS & ECONOMY", MKT)
    y = 0.822
    for line in _wrap(a["market_read"], 46)[:6]:
        A.text(0.70, y, line, color=INK, fontsize=9); y -= 0.018
    y -= 0.008
    A.text(0.70, y, "SECTOR TAPE (avg %chg)", color=MKT, fontsize=8.5, weight="bold"); y -= 0.017
    for k, v in d["sector_tape"][:5]:
        A.text(0.70, y, _clean(k)[:18], color=MUT2, fontsize=7.8)
        bw = min(abs(v) / 2.0, 1.0) * 0.16
        A.add_patch(plt.Rectangle((0.80, y + 0.002), bw, 0.009, color=UP if v > 0 else DN))
        A.text(0.97, y, "%+.2f%%" % v, color=UP if v > 0 else DN, fontsize=7.8, ha="right", weight="bold")
        y -= 0.016
    y -= 0.008
    A.text(0.70, y, "TOP MOVERS", color=MKT, fontsize=8.5, weight="bold"); y -= 0.016
    for m in (pulse.get("gainers", [])[:2] + pulse.get("losers", [])[:2]):
        A.text(0.70, y, m["t"], color=INK, fontsize=8.2, weight="bold")
        A.text(0.97, y, "%+.2f%%" % m["pct"], color=UP if m["pct"] > 0 else DN, fontsize=8.2, ha="right", weight="bold")
        y -= 0.015

    # BOTTOM band
    by = 0.30
    A.add_patch(plt.Rectangle((0.03, 0.06), 0.94, 0.0015, color=INK))
    _kicker(A, 0.03, by, 0.29, "WHAT CHANGED", HI)
    y = by - 0.024
    for line in _wrap(a["delta"], 48)[:4]:
        A.text(0.03, y, line, color=INK, fontsize=8.8); y -= 0.018
    _kicker(A, 0.36, by, 0.29, "SOCIAL PULSE", SOC)
    y = by - 0.024
    for line in _wrap(a["social_read"], 48)[:3]:
        A.text(0.36, y, line, color=INK, fontsize=8.8); y -= 0.018
    for line in ([_clean(r)[:40] for r in d["st_radar"][:3]] or ["No retail consensus."]):
        A.text(0.36, y, line, color=MUT2, fontsize=7.8); y -= 0.015
    _kicker(A, 0.70, by, 0.27, "OUTLOOK & KEY RISK", DN)
    y = by - 0.024
    for line in _wrap(a["outlook"], 46)[:3]:
        A.text(0.70, y, line, color=INK, fontsize=8.8); y -= 0.018
    A.add_patch(plt.Rectangle((0.70, y - 0.02), 0.27, 0.03, color="#EAD9D2"))
    A.text(0.708, y - 0.002, _wrap(a["key_risk"], 46)[0], color=DN, fontsize=8.2, weight="bold")
    A.text(0.708, y - 0.015, _wrap(a["key_risk"], 46)[1] if len(_wrap(a["key_risk"], 46)) > 1 else "", color=DN, fontsize=8.2)

    mode = "Qwen (validated)" if llm_ok else "deterministic fallback"
    A.text(0.03, 0.02, "Narrative: %s | Charts from snapshots | Tentative - machine-compiled, not investment advice" % mode, color=MUT2, fontsize=7.5)
    A.text(0.97, 0.02, "Page 1 of 2", color=MUT2, fontsize=7.5, ha="right")
    fig.savefig(P1, facecolor=PAPER); plt.close(fig)

# ================= PAGE 2 =================
def render_p2(d, a, llm_ok):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=200); fig.patch.set_facecolor(PAPER)
    A = fig.add_axes([0, 0, 1, 1]); A.set_axis_off(); A.set_xlim(0, 1); A.set_ylim(0, 1)
    now = datetime.now(timezone.utc).strftime("%A, %Y-%m-%d %H:%M UTC")
    _masthead(A, "MARKETS & DATA", "The Aggregate Gazette · Section B", now)
    pulse, macro, regime = d["pulse"], d["macro"], d["regime"]

    # LEFT: mega-cap + sector charts
    ax = fig.add_axes([0.05, 0.60, 0.27, 0.30]); _lax(ax); ax.set_title("MEGA-CAP LEADERS (%CHG)")
    mega = [m for m in pulse.get("mega_caps", []) if m.get("pct") is not None][:12]
    if mega:
        names = [m["t"] for m in mega][::-1]; vals = [m["pct"] for m in mega][::-1]
        ax.barh(names, vals, color=[UP if v > 0 else DN for v in vals], height=0.72)
        ax.axvline(0, color=MUT2, lw=0.6)
        mm = max([abs(v) for v in vals] + [0.1]); ax.set_xlim(-mm * 1.3, mm * 1.3)
    ax = fig.add_axes([0.05, 0.33, 0.27, 0.22]); _lax(ax); ax.set_title("SECTOR TAPE (avg %chg)")
    if d["sector_tape"]:
        ks = [k[:14] for k, _ in d["sector_tape"][:8]][::-1]; vs = [v for _, v in d["sector_tape"][:8]][::-1]
        ax.barh(ks, vs, color=[UP if v > 0 else DN for v in vs], height=0.7)
        ax.axvline(0, color=MUT2, lw=0.6)

    # CENTER: two-column macro table
    _kicker(A, 0.36, 0.90, 0.32, "MACRO & RATES - FULL BOARD", MKT)
    groups = {}
    for i in macro.get("instruments", []): groups.setdefault(i.get("type", "other"), []).append(i)
    y = 0.875
    for gname, key, n in [("CASH INDICES", "index", 6), ("INDEX FUTURES", "index_future", 3), ("COMMODITIES", "commodity", 5)]:
        A.text(0.36, y, gname, color=MUT2, fontsize=7.5, weight="bold"); y -= 0.016
        for i in groups.get(key, [])[:n]:
            p = i.get("pct")
            A.text(0.36, y, _clean(i["name"])[:16], color=INK, fontsize=8)
            A.text(0.475, y, _fmt_price(i.get("price"), i.get("type")), color=MUT2, fontsize=7.8, ha="right")
            A.text(0.53, y, "%+.2f%%" % p if p is not None else "-", color=UP if (p or 0) > 0 else (DN if (p or 0) < 0 else MUT2), fontsize=8, ha="right", weight="bold")
            y -= 0.016
        y -= 0.006
    y = 0.875
    for gname, key, n in [("FOREX", "forex", 4), ("RATES", "bond", 3)]:
        A.text(0.56, y, gname, color=MUT2, fontsize=7.5, weight="bold"); y -= 0.016
        for i in groups.get(key, [])[:n]:
            p = i.get("pct")
            A.text(0.56, y, _clean(i["name"])[:14], color=INK, fontsize=8)
            A.text(0.685, y, "%+.2f%%" % p if p is not None else "-", color=UP if (p or 0) > 0 else (DN if (p or 0) < 0 else MUT2), fontsize=8, ha="right", weight="bold")
            y -= 0.016
        y -= 0.006
    A.text(0.56, y, "REGIME", color=MUT2, fontsize=7.5, weight="bold"); y -= 0.016
    for line in filter(None, [
        "VIX: %s" % regime.get("vix"), "2s10s: %s%s" % (regime.get("curve_2s10s", ""), " INVERTED" if regime.get("curve_inverted") else ""),
        "DXY: %s" % regime.get("dxy"), "Oil: %s" % regime.get("oil_spike")]):
        A.text(0.56, y, _clean(line), color=GEO, fontsize=8); y -= 0.016

    # yield curve
    ax = fig.add_axes([0.36, 0.33, 0.30, 0.22]); _lax(ax); ax.set_title("US YIELD CURVE")
    im = {i["sym"]: i for i in macro.get("instruments", [])}
    pts = [(n, im.get(s, {}).get("price")) for n, s in [("2Y", "TVC:US02Y"), ("10Y", "TVC:US10Y"), ("30Y", "TVC:US30Y")]]
    pts = [(n, p) for n, p in pts if p is not None]
    if pts:
        ax.plot([n for n, _ in pts], [p for _, p in pts], marker="o", color=GEO, lw=2.5, markersize=8)
        for n, p in pts: ax.annotate("%.2f%%" % p, (n, p), textcoords="offset points", xytext=(0, 10), color=INK, fontsize=9, ha="center")
        if len(pts) >= 2:
            sp = (pts[-1][1] - pts[0][1]) * 100
            ax.set_title("US YIELD CURVE | 2s10s %+.0fbp%s" % (sp, " INVERTED" if sp < 0 else ""))

    # RIGHT: commodities chart + 1h movers + headlines-free zone
    ax = fig.add_axes([0.71, 0.72, 0.26, 0.18]); _lax(ax); ax.set_title("COMMODITIES COMPLEX")
    coms = [i for i in groups.get("commodity", []) if i.get("pct") is not None]
    if coms:
        ax.bar([_clean(i["name"])[:8] for i in coms], [i["pct"] for i in coms], color=[UP if i["pct"] > 0 else DN for i in coms])
        ax.axhline(0, color=MUT2, lw=0.6)
    _kicker(A, 0.71, 0.66, 0.26, "1-HOUR MOVERS (LARGE CAPS)", HI)
    y = 0.635
    hm = pulse.get("hour_movers", [])
    if not hm:
        A.text(0.71, y, "No large-cap stock moved >1% in the past hour.", color=MUT2, fontsize=8.2); y -= 0.02
    for m in hm[:5]:
        A.text(0.71, y, m["t"], color=INK, fontsize=9, weight="bold")
        A.text(0.80, y, "%+.2f%% (1h)" % m["hour_chg"], color=UP if m["hour_chg"] > 0 else DN, fontsize=8.4, weight="bold")
        A.text(0.97, y, "sess %+.2f%% · $%.0fB" % (m["pct"], m["mcap"] / 1e9), color=MUT2, fontsize=7.6, ha="right")
        y -= 0.021
    _kicker(A, 0.71, 0.50, 0.26, "MOVERS SCATTER", MKT)
    ax = fig.add_axes([0.72, 0.33, 0.25, 0.15]); _lax(ax)
    sig = [{"t": k, **v} for k, v in pulse.get("sig", {}).items() if v.get("pct") is not None and v.get("relvol")][:50]
    if sig:
        ax.scatter([v["pct"] for v in sig], [v["relvol"] for v in sig], c=[UP if v["pct"] > 0 else DN for v in sig], s=14, alpha=0.7)
        for v in sorted(sig, key=lambda x: -x["relvol"])[:4]:
            ax.annotate(_clean(v["t"]), (v["pct"], v["relvol"]), color=INK, fontsize=7, xytext=(3, 3), textcoords="offset points")

    # HEADLINES band
    A.add_patch(plt.Rectangle((0.03, 0.285), 0.94, 0.0015, color=INK))
    _kicker(A, 0.03, 0.265, 0.94, "NEWS HEADLINES - PAST 24 HOURS", GEO)
    hl = d["headlines"][:8]
    for i, e in enumerate(hl):
        colx = 0.03 + (i % 2) * 0.485
        yy = 0.240 - (i // 2) * 0.021
        ts = datetime.fromtimestamp(e.get("ts") or 0, timezone.utc).strftime("%H:%M")
        A.text(colx, yy, "[%s] %s" % (ts, _wrap(e.get("title"), 62)[0]), color=INK, fontsize=8.2)

    # bottom band: cross-asset + themes/sentiment + key numbers
    _kicker(A, 0.03, 0.145, 0.40, "CROSS-ASSET ANALYSIS", MKT)
    y = 0.122
    for line in _wrap(a["cross_asset"], 70)[:3]:
        A.text(0.03, y, line, color=INK, fontsize=8.6); y -= 0.017
    _kicker(A, 0.50, 0.145, 0.22, "THEMES & SENTIMENT", SOC)
    y = 0.122
    top_themes = sorted(d["themes"].items(), key=lambda x: -x[1])[:4]
    mx = top_themes[0][1] if top_themes else 1
    for k, v in top_themes:
        A.text(0.50, y, _clean(DOMAIN_NAMES.get(k, k))[:14], color=MUT2, fontsize=7.6)
        A.add_patch(plt.Rectangle((0.60, y + 0.002), 0.08 * v / mx, 0.008, color=MKT))
        A.text(0.69, y, str(v), color=INK, fontsize=7.6); y -= 0.016
    x = 0.50
    for key, col in [("bullish", UP), ("neutral", MUT2), ("bearish", DN)]:
        w = 0.15 * rolls[key] / tot
        A.add_patch(plt.Rectangle((x, y - 0.004), max(w, 0.004), 0.009, color=col)); x += w + 0.004
    A.text(x + 0.01, y - 0.004, "B%d N%d S%d" % (rolls["bullish"], rolls["neutral"], rolls["bearish"]), color=MUT2, fontsize=7.6)
    _kicker(A, 0.76, 0.145, 0.21, "KEY NUMBERS", GEO)
    y = 0.122
    g0 = pulse.get("gainers", [{}])[0]; l0 = pulse.get("losers", [{}])[0]
    for lab, val, col in [("GAINER", "%s %+.2f%%" % (g0.get("t", "-"), g0.get("pct", 0)) if g0.get("t") else "-", UP),
                          ("LOSER", "%s %+.2f%%" % (l0.get("t", "-"), l0.get("pct", 0)) if l0.get("t") else "-", DN),
                          ("GOLD", "%+.2f%%" % (im.get("Gold", {}).get("pct") or 0), UP if (im.get("Gold", {}).get("pct") or 0) > 0 else DN),
                          ("10Y", _fmt_price(im.get("US 10Y Yield", {}).get("price"), "bond"), GEO)]:
        A.text(0.76, y, lab, color=MUT2, fontsize=7.5, weight="bold")
        A.text(0.97, y, _clean(val), color=col, fontsize=8.2, ha="right", weight="bold"); y -= 0.017

    A.text(0.03, 0.02, "All charts computed from source snapshots | Tentative - machine-compiled, not investment advice", color=MUT2, fontsize=7.5)
    A.text(0.97, 0.02, "Page 2 of 2", color=MUT2, fontsize=7.5, ha="right")
    fig.savefig(P2, facecolor=PAPER); plt.close(fig)

def send(pages):
    wh = os.environ.get("DISCORD_WEBHOOK")
    if not wh: print("FATAL: DISCORD_WEBHOOK secret is not set."); return
    files = []
    for i, p in enumerate(pages):
        files.append(("files[%d]" % i, (os.path.basename(p), open(p, "rb"), "image/png")))
    r = requests.post(wh, files=files,
                      data={"payload_json": json.dumps({"content": "🗞️ **THE AGGREGATE GAZETTE** (tentative, machine-compiled)"})})
    if r.status_code >= 400:
        raise RuntimeError("Discord HTTP %d: %s" % (r.status_code, r.text[:120]))
    print("Gazette delivered (2 pages, 4K)!")

if __name__ == "__main__":
    os.makedirs(REPORTS, exist_ok=True)
    data = collect()
    analysis, llm_ok, prev = analyze(data)
    render_p1(data, analysis, llm_ok)
    render_p2(data, analysis, llm_ok)
    _save_prev(analysis, data)
    send([P1, P2])
