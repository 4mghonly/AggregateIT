"""slide.py v8 — THE AGGREGATE GAZETTE. 4K two-page editorial deck.
v8: larger type, kicker spacing fixed, sentence-safe wrapping, dollar-claim
scrubber (no invented prices), index futures hidden until resolvable,
yield history chart (trailing sessions), compact headlines, whitespace filled."""
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
YIELD_FILE = os.path.join(market.DATA, "yield_hist.json")

PAPER, INK, MUT2, CARDL = "#F6F1E7", "#1C1B18", "#6E675C", "#EFE8DA"
GEO, MKT, SOC, UP, DN, HI = "#7D2A2A", "#1F3864", "#8A6D1F", "#2E5E3A", "#A33B2E", "#C89B2A"
SEV_COLOR = {"Critical": DN, "High": "#B4622D", "Medium": HI, "Low": MUT2}
GEO_TAGS = {"GG", "ME", "TR", "CY", "US"}

def _clean(s): return re.sub(r'[^\x20-\x7E]', '', s or '').strip()

def _wrap(s, n): return textwrap.wrap(_clean(s), n) or [""]

def _fit(text, width, max_lines):
    """Wrap to max_lines keeping complete sentences; ellipsize if truncated."""
    lines = textwrap.wrap(_clean(text), width)
    if len(lines) <= max_lines: return lines
    s = " ".join(lines[:max_lines])
    cut = max(s.rfind(". "), s.rfind("! "), s.rfind("? "))
    if cut > len(s) * 0.5: s = s[:cut + 1]
    else: s = s.rstrip() + " ..."
    return textwrap.wrap(s, width)[:max_lines]

_DOLLAR_RE = re.compile(r"\$\s?[\d,]+")
def _scrub(text):
    """Drop sentences containing dollar/price claims (anti-hallucination)."""
    sents = re.split(r"(?<=[.!?])\s+", _clean(text))
    keep = [s for s in sents if not _DOLLAR_RE.search(s)]
    return " ".join(keep)

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
    # yield curve points + trailing history
    im_all = {x["sym"]: x for x in macro.get("instruments", [])}
    curve_pts = {}
    for s, n in (("TVC:US02Y", "2Y"), ("TVC:US05Y", "5Y"), ("TVC:US10Y", "10Y"), ("TVC:US30Y", "30Y")):
        i = im_all.get(s)
        if i and i.get("price") is not None: curve_pts[n] = i["price"]
    hist = []
    try:
        with open(YIELD_FILE) as f: hist = json.load(f)
    except Exception: pass
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if curve_pts:
        hist = [h for h in hist if h.get("day") != day]
        sp = None
        if "2Y" in curve_pts and "10Y" in curve_pts: sp = (curve_pts["10Y"] - curve_pts["2Y"]) * 100
        hist.append({"day": day, "ts": time.time(), "pts": curve_pts, "spread2s10s": sp})
        hist = hist[-60:]
        try:
            with open(YIELD_FILE, "w") as f: json.dump(hist, f)
        except Exception: pass
    return {"store": store, "pulse": pulse, "macro": macro, "regime": regime, "events": events,
            "geo_events": [e for e in events if e.get("geo")], "themes": themes,
            "st_radar": st_radar, "reddit": reddit, "sources_active": sources_active,
            "headlines": headlines, "sector_tape": sector_tape,
            "curve_pts": curve_pts, "yield_hist": hist}

ANALYSIS_PROMPT = """You are the editor of a financial-and-geopolitical intelligence gazette.
Write TENTATIVE, quantitative, complete-sentence analysis. Rules:
- Use ONLY data present below; never invent tickers, numbers, events, or countries.
- NEVER use dollar signs or absolute price levels; express all moves in percent only.
- Balance geopolitical and economic analysis equally.
- NO EMOJIS. Complete sentences only. Each field under 600 chars.
Return ONLY this JSON:
{
  "headline": "serif-style front-page headline, max 90 chars",
  "lead": "3-sentence lead paragraph tying geopolitics AND markets together",
  "geopol_read": "2-3 sentences: geopolitical developments and their market transmission channels",
  "market_read": "2-3 sentences: equities, rates, FX, commodities behavior and divergences",
  "social_read": "1-2 sentences: retail/social chatter vs price action",
  "cross_asset": "2 sentences: specific news-to-price connections",
  "outlook": "1-2 sentences: catalysts and percent-level moves to watch next 24 hours",
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
    out = None
    try:
        base = os.environ.get("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1").rstrip("/")
        prompt = ANALYSIS_PROMPT.replace("__DATA__", _data_text(d)).replace("__PREV__", _prev_text(prev))
        r = requests.post(base + "/chat/completions",
            headers={"Authorization": "Bearer " + os.environ["QWEN_API_KEY"]},
            json={"model": os.environ.get("QWEN_MODEL", "qwen-plus"), "temperature": 0.3,
                  "messages": [{"role": "system", "content": "Gazette editor. Output ONLY valid JSON. NO EMOJIS. NO DOLLAR FIGURES."},
                               {"role": "user", "content": prompt}]}, timeout=90)
        r.raise_for_status()
        m = re.search(r"\{[\s\S]*\}", r.json()["choices"][0]["message"]["content"])
        if m:
            obj = json.loads(m.group(0))
            if all(isinstance(obj.get(k), str) and len(obj.get(k)) >= 10 for k in REQUIRED_KEYS):
                out = obj
    except Exception: pass
    if out is None:
        out, llm = _fallback_analysis(d, prev), False
    else:
        llm = True
    for k in REQUIRED_KEYS:
        out[k] = _scrub(out[k]) or out[k]
    return out, llm, prev

# ================= PRIMITIVES =================
def _kicker(A, x, y, w, text, color):
    A.text(x, y, _clean(text), color=color, fontsize=12.5, weight="bold")
    A.add_patch(plt.Rectangle((x, y - 0.016), w, 0.0022, color=color))

def _lax(ax):
    ax.set_facecolor(PAPER)
    ax.tick_params(colors=MUT2, labelsize=9)
    for s in ax.spines.values(): s.set_color("#C9C0AE")
    ax.title.set_color(INK); ax.title.set_fontsize(11); ax.title.set_weight("bold")
    
def _title(ax, t):
    ax.set_title(_clean(t))
    ax.title.set_color(INK); ax.title.set_fontsize(12); ax.title.set_weight("bold")

def _masthead(A, title, right1, right2):
    A.text(0.5, 0.965, _clean(title), color=INK, fontsize=30, weight="bold", fontfamily="serif", ha="center")
    A.text(0.03, 0.965, right1, color=MUT2, fontsize=9.5)
    A.text(0.97, 0.965, right2, color=MUT2, fontsize=9.5, ha="right")
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
        if i: A.add_patch(plt.Rectangle((cx, 0.883), 0.0012, 0.048, color=INK))
        A.text(cx + w / 2, 0.925, _clean(lab), color=MUT2, fontsize=9, ha="center", weight="bold")
        A.text(cx + w / 2, 0.902, _clean(val), color=INK, fontsize=15, ha="center", weight="bold")
        A.text(cx + w / 2, 0.886, _clean(sub), color=MUT2, fontsize=8.5, ha="center")
    A.add_patch(plt.Rectangle((0.03, 0.878), 0.94, 0.0015, color=INK))

    # LEAD
    A.text(0.335, 0.845, _clean(a["headline"]), color=INK, fontsize=20, weight="bold", fontfamily="serif")
    A.add_patch(plt.Rectangle((0.335, 0.831), 0.35, 0.0015, color=HI))
    body = _fit(a["lead"], 76, 8)
    y = 0.808
    if body:
        A.text(0.335, y - 0.006, body[0][0], color=INK, fontsize=26, weight="bold", fontfamily="serif")
        A.text(0.352, y, body[0][1:], color=INK, fontsize=11)
        y -= 0.023
        for line in body[1:]:
            A.text(0.335, y, line, color=INK, fontsize=11); y -= 0.021
    hy = y - 0.012
    cells = mega[:12]; cw = 0.35 / max(len(cells), 1)
    for i, m in enumerate(cells):
        col = UP if m["pct"] > 0 else DN
        A.add_patch(plt.Rectangle((0.335 + i * cw, hy - 0.038), cw * 0.92, 0.035, color=col,
                                  alpha=min(0.25 + abs(m["pct"]) / 4.0, 0.9)))
        A.text(0.335 + i * cw + cw / 2, hy - 0.014, m["t"], color="#fff", fontsize=7.5, ha="center", weight="bold")
        A.text(0.335 + i * cw + cw / 2, hy - 0.029, "%+.1f" % m["pct"], color="#fff", fontsize=7, ha="center")

    # LEFT rail
    _kicker(A, 0.03, 0.845, 0.27, "WORLD & GEOPOLITICS", GEO)
    y = 0.816
    for line in _fit(a["geopol_read"], 60, 5):
        A.text(0.03, y, line, color=INK, fontsize=11); y -= 0.021
    y -= 0.010
    A.text(0.03, y, "GEOPOLITICAL WATCHLIST", color=GEO, fontsize=10, weight="bold"); y -= 0.020
    for e in d["geo_events"][:5]:
        sev = e.get("severity") or "Low"
        A.add_patch(plt.Rectangle((0.03, y + 0.001), 0.005, 0.015, color=SEV_COLOR.get(sev, MUT2)))
        A.text(0.04, y, _wrap(e.get("title"), 44)[0], color=INK, fontsize=9.5, weight="bold")
        A.text(0.04, y - 0.015, _clean("%s | %s%% | %s" % (sev, e.get("confidence"), e.get("source", ""))), color=MUT2, fontsize=8.5)
        y -= 0.036
    y -= 0.010
    A.text(0.03, y, "RISK THERMOMETER", color=GEO, fontsize=10, weight="bold"); y -= 0.020
    score = min(100, 25 * sum(1 for e in d["events"] if e.get("severity") == "Critical") +
                10 * hi_crit + (im.get("VIX", {}).get("price") or 15))
    A.add_patch(plt.Rectangle((0.03, y - 0.006), 0.27, 0.011, color=CARDL))
    A.add_patch(plt.Rectangle((0.03, y - 0.006), 0.27 * score / 100.0, 0.011, color=GEO))
    A.text(0.305, y - 0.006, "%d" % score, color=GEO, fontsize=9.5, weight="bold")
    y -= 0.030
    A.text(0.03, y, "ACTIVE NEWS SOURCES", color=GEO, fontsize=10, weight="bold"); y -= 0.019
    for line in _wrap(", ".join(d.get("sources_active", [])[:14]) or "No sources in window.", 58)[:4]:
        A.text(0.03, y, line, color=MUT2, fontsize=9); y -= 0.017

    # RIGHT rail
    _kicker(A, 0.70, 0.845, 0.27, "MARKETS & ECONOMY", MKT)
    y = 0.816
    for line in _fit(a["market_read"], 60, 5):
        A.text(0.70, y, line, color=INK, fontsize=11); y -= 0.021
    y -= 0.010
    A.text(0.70, y, "SECTOR TAPE (avg %chg)", color=MKT, fontsize=10, weight="bold"); y -= 0.019
    for k, v in d["sector_tape"][:5]:
        A.text(0.70, y, _clean(k)[:18], color=MUT2, fontsize=9)
        A.add_patch(plt.Rectangle((0.80, y + 0.002), min(abs(v) / 2.0, 1.0) * 0.16, 0.010, color=UP if v > 0 else DN))
        A.text(0.97, y, "%+.2f%%" % v, color=UP if v > 0 else DN, fontsize=9, ha="right", weight="bold")
        y -= 0.018
    y -= 0.010
    A.text(0.70, y, "TOP MOVERS", color=MKT, fontsize=10, weight="bold"); y -= 0.018
    for m in (pulse.get("gainers", [])[:2] + pulse.get("losers", [])[:2]):
        A.text(0.70, y, m["t"], color=INK, fontsize=9.5, weight="bold")
        A.text(0.97, y, "%+.2f%%" % m["pct"], color=UP if m["pct"] > 0 else DN, fontsize=9.5, ha="right", weight="bold")
        y -= 0.017
    y -= 0.010
    A.text(0.70, y, "MACRO SNAPSHOT", color=MKT, fontsize=10, weight="bold"); y -= 0.018
    for nm in ("S&P 500", "VIX", "US 10Y Yield", "WTI Crude"):
        i = im.get(nm, {})
        p = i.get("pct")
        A.text(0.70, y, nm, color=MUT2, fontsize=9)
        A.text(0.97, y, "%+.2f%%" % p if p is not None else "-", color=UP if (p or 0) > 0 else (DN if (p or 0) < 0 else MUT2), fontsize=9, ha="right", weight="bold")
        y -= 0.017

    # BOTTOM band
    by = 0.30
    A.add_patch(plt.Rectangle((0.03, 0.315), 0.94, 0.0015, color=INK))
    _kicker(A, 0.03, by, 0.29, "WHAT CHANGED", HI)
    y = by - 0.030
    for line in _fit(a["delta"], 62, 4):
        A.text(0.03, y, line, color=INK, fontsize=10); y -= 0.019
    _kicker(A, 0.36, by, 0.29, "SOCIAL PULSE", SOC)
    y = by - 0.030
    for line in _fit(a["social_read"], 62, 3):
        A.text(0.36, y, line, color=INK, fontsize=10); y -= 0.019
    for line in ([_clean(r)[:44] for r in d["st_radar"][:3]] or ["No retail consensus."]):
        A.text(0.36, y, line, color=MUT2, fontsize=9); y -= 0.017
    _kicker(A, 0.70, by, 0.27, "OUTLOOK & KEY RISK", DN)
    y = by - 0.030
    for line in _fit(a["outlook"], 58, 3):
        A.text(0.70, y, line, color=INK, fontsize=10); y -= 0.019
    A.add_patch(plt.Rectangle((0.70, y - 0.024), 0.27, 0.036, color="#EAD9D2"))
    rk = _fit(a["key_risk"], 52, 2)
    A.text(0.708, y - 0.006, rk[0] if rk else "", color=DN, fontsize=9.5, weight="bold")
    A.text(0.708, y - 0.020, rk[1] if len(rk) > 1 else "", color=DN, fontsize=9.5)

    mode = "Qwen (validated)" if llm_ok else "deterministic fallback"
    A.text(0.03, 0.02, "Narrative: %s | Charts from snapshots | Tentative - machine-compiled, not investment advice" % mode, color=MUT2, fontsize=8.5)
    A.text(0.97, 0.02, "Page 1 of 2", color=MUT2, fontsize=8.5, ha="right")
    fig.savefig(P1, facecolor=PAPER); plt.close(fig)

# ================= PAGE 2 =================
def render_p2(d, a, llm_ok):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=200); fig.patch.set_facecolor(PAPER)
    A = fig.add_axes([0, 0, 1, 1]); A.set_axis_off(); A.set_xlim(0, 1); A.set_ylim(0, 1)
    now = datetime.now(timezone.utc).strftime("%A, %Y-%m-%d %H:%M UTC")
    _masthead(A, "MARKETS & DATA", "The Aggregate Gazette · Section B", now)
    pulse, macro, regime = d["pulse"], d["macro"], d["regime"]
    rolls = {"bullish": 0, "neutral": 0, "bearish": 0}
    for e in d["events"]:
        s = (e.get("sentiment") or "").lower()
        if s in rolls: rolls[s] += 1
    tot = max(sum(rolls.values()), 1)
    im = {i["name"]: i for i in macro.get("instruments", [])}

    # LEFT column: INCREASED SPACING to prevent overlap
    ax = fig.add_axes([0.05, 0.68, 0.27, 0.22]); _lax(ax); _title(ax, "MEGA-CAP LEADERS (%CHG)")
    mega = [m for m in pulse.get("mega_caps", []) if m.get("pct") is not None][:12]
    if mega:
        names = [m["t"] for m in mega][::-1]; vals = [m["pct"] for m in mega][::-1]
        ax.barh(names, vals, color=[UP if v > 0 else DN for v in vals], height=0.72)
        ax.axvline(0, color=MUT2, lw=0.6)
        mm = max([abs(v) for v in vals] + [0.1]); ax.set_xlim(-mm * 1.3, mm * 1.3)
    
    ax = fig.add_axes([0.05, 0.51, 0.27, 0.14]); _lax(ax); _title(ax, "SECTOR TAPE (avg %chg)")
    if d["sector_tape"]:
        ks = [k[:14] for k, _ in d["sector_tape"][:8]][::-1]; vs = [v for _, v in d["sector_tape"][:8]][::-1]
        ax.barh(ks, vs, color=[UP if v > 0 else DN for v in vs], height=0.7)
        ax.axvline(0, color=MUT2, lw=0.6)
    
    ax = fig.add_axes([0.05, 0.36, 0.27, 0.12]); _lax(ax); _title(ax, "MOVERS: %CHG vs REL-VOLUME")
    sig = [{"t": k, **v} for k, v in pulse.get("sig", {}).items() if v.get("pct") is not None and v.get("relvol")][:50]
    if sig:
        ax.scatter([v["pct"] for v in sig], [v["relvol"] for v in sig], c=[UP if v["pct"] > 0 else DN for v in sig], s=12, alpha=0.7)
        for v in sorted(sig, key=lambda x: -x["relvol"])[:4]:
            ax.annotate(_clean(v["t"]), (v["pct"], v["relvol"]), color=INK, fontsize=7.5, xytext=(3, 3), textcoords="offset points")

    # MIDDLE: Macro table with MISSING DATA HANDLING
    _kicker(A, 0.36, 0.90, 0.32, "MACRO & RATES - FULL BOARD", MKT)
    groups = {}
    for i in macro.get("instruments", []): groups.setdefault(i.get("type", "other"), []).append(i)
    blocks = [("CASH INDICES", "index", 6), ("COMMODITIES", "commodity", 5)]
    if groups.get("index_future"): blocks.insert(1, ("INDEX FUTURES", "index_future", 3))
    y = 0.868
    for gname, key, n in blocks:
        A.text(0.36, y, gname, color=MUT2, fontsize=9.5, weight="bold"); y -= 0.017
        rows = groups.get(key, [])[:n]
        if not rows:
            A.text(0.36, y, "No data available", color=MUT2, fontsize=9); y -= 0.017
        else:
            for i in rows:
                p = i.get("pct")
                A.text(0.36, y, _clean(i["name"])[:16], color=INK, fontsize=9.5)
                A.text(0.475, y, _fmt_price(i.get("price"), i.get("type")), color=MUT2, fontsize=9, ha="right")
                A.text(0.53, y, "%+.2f%%" % p if p is not None else "-", color=UP if (p or 0) > 0 else (DN if (p or 0) < 0 else MUT2), fontsize=9.5, ha="right", weight="bold")
                y -= 0.017
        y -= 0.006

    y = 0.868
    for gname, key, n in [("FOREX", "forex", 4), ("RATES", "bond", 4)]:
        A.text(0.56, y, gname, color=MUT2, fontsize=9.5, weight="bold"); y -= 0.017
        rows = groups.get(key, [])[:n]
        if not rows:
            A.text(0.56, y, "No data available", color=MUT2, fontsize=9); y -= 0.017
        else:
            for i in rows:
                p = i.get("pct")
                A.text(0.56, y, _clean(i["name"])[:14], color=INK, fontsize=9.5)
                A.text(0.685, y, "%+.2f%%" % p if p is not None else "-", color=UP if (p or 0) > 0 else (DN if (p or 0) < 0 else MUT2), fontsize=9.5, ha="right", weight="bold")
                y -= 0.017
        y -= 0.006

    A.text(0.56, y, "REGIME", color=MUT2, fontsize=9.5, weight="bold"); y -= 0.017
    regime_lines = list(filter(None, [
        "VIX: %s" % regime.get("vix") if regime.get("vix") else None,
        "2s10s: %s%s" % (regime.get("curve_2s10s", ""), " INVERTED" if regime.get("curve_inverted") else "") if regime.get("curve_2s10s") else None,
        "DXY: %s" % regime.get("dxy") if regime.get("dxy") else None,
        "Oil: %s" % regime.get("oil_spike") if regime.get("oil_spike") else None]))
    if not regime_lines:
        A.text(0.56, y, "No regime data", color=MUT2, fontsize=9); y -= 0.017
    else:
        for line in regime_lines:
            A.text(0.56, y, _clean(line), color=GEO, fontsize=9.5); y -= 0.017

    # Yield curve
    ax = fig.add_axes([0.36, 0.36, 0.30, 0.22]); _lax(ax)
    hist = [h for h in d["yield_hist"] if h.get("spread2s10s") is not None]
    if len(hist) >= 3:
        ax.plot(range(len(hist)), [h["spread2s10s"] for h in hist], marker="o", color=GEO, lw=2.5, markersize=6)
        ax.axhline(0, color=MUT2, lw=0.6, ls="--")
        _title(ax, "2s10s SPREAD (bp) - TRAILING %d SESSIONS" % len(hist))
        ax.set_xlabel("%s → %s" % (hist[0]["day"], hist[-1]["day"]), color=MUT2, fontsize=8.5)
    else:
        pts = [(n, d["curve_pts"].get(n)) for n in ("2Y", "5Y", "10Y", "30Y") if d["curve_pts"].get(n) is not None]
        if pts:
            ax.plot([n for n, _ in pts], [p for _, p in pts], marker="o", color=GEO, lw=2.5, markersize=8)
            for n, p in pts: ax.annotate("%.2f%%" % p, (n, p), textcoords="offset points", xytext=(0, 10), color=INK, fontsize=9.5, ha="center")
            _title(ax, "US YIELD CURVE - CURRENT TERM STRUCTURE (history building)")
        else:
            ax.text(0.5, 0.5, "no data", color=MUT2, ha="center")

    # RIGHT column: Commodities + Risers/Fallers + 1h movers
    ax = fig.add_axes([0.72, 0.76, 0.25, 0.12]); _lax(ax); _title(ax, "COMMODITIES COMPLEX")
    coms = [i for i in groups.get("commodity", []) if i.get("pct") is not None]
    if not coms:
        ax.text(0.5, 0.5, "No data", color=MUT2, ha="center", transform=ax.transAxes)
    else:
        ax.bar([_clean(i["name"])[:8] for i in coms], [i["pct"] for i in coms], color=[UP if i["pct"] > 0 else DN for i in coms])
        ax.axhline(0, color=MUT2, lw=0.6)

    _kicker(A, 0.71, 0.72, 0.26, "RISERS & FALLERS (SINCE LAST UPDATE)", HI)
    deltas = pulse.get("deltas", {})
    if deltas:
        up = sum(1 for v in deltas.values() if v > 0.05)
        dn = sum(1 for v in deltas.values() if v < -0.05)
        fl = len(deltas) - up - dn
        axp = fig.add_axes([0.72, 0.52, 0.115, 0.185]); axp.set_facecolor(PAPER); axp.set_axis_off()
        axp.pie([up, dn, fl], colors=[UP, DN, "#B9B0A0"], startangle=90, wedgeprops={"linewidth": 0.8, "edgecolor": PAPER})
        A.text(0.85, 0.65, "Rising %d" % up, color=UP, fontsize=10.5, weight="bold")
        A.text(0.85, 0.61, "Falling %d" % dn, color=DN, fontsize=10.5, weight="bold")
        A.text(0.85, 0.57, "Unchanged %d" % fl, color=MUT2, fontsize=10.5, weight="bold")
    else:
        A.text(0.72, 0.62, "No previous snapshot yet -", color=MUT2, fontsize=9.5)
        A.text(0.72, 0.59, "baseline building.", color=MUT2, fontsize=9.5)

    _kicker(A, 0.71, 0.49, 0.26, "1-HOUR MOVERS (LARGE CAPS)", HI)
    y = 0.46
    hm = pulse.get("hour_movers", [])
    if not hm:
        A.text(0.71, y, "No large-cap stock moved >1% in the past hour.", color=MUT2, fontsize=9.5); y -= 0.023
    for m in hm[:5]:
        A.text(0.71, y, m["t"], color=INK, fontsize=10, weight="bold")
        A.text(0.80, y, "%+.2f%% (1h)" % m["hour_chg"], color=UP if m["hour_chg"] > 0 else DN, fontsize=9.5, weight="bold")
        A.text(0.97, y, "sess %+.2f%% · $%.0fB" % (m["pct"], m["mcap"] / 1e9), color=MUT2, fontsize=9, ha="right")
        y -= 0.023

    # HEADLINES: LOWERED to create buffer from charts
    A.add_patch(plt.Rectangle((0.03, 0.305), 0.94, 0.0015, color=INK))
    _kicker(A, 0.03, 0.288, 0.94, "NEWS HEADLINES - PAST 24 HOURS", GEO)
    for i, e in enumerate(d["headlines"][:8]):
        colx = 0.03 + (i % 2) * 0.485
        yy = 0.263 - (i // 2) * 0.017
        ts = datetime.fromtimestamp(e.get("ts") or 0, timezone.utc).strftime("%H:%M")
        t = _clean(e.get("title"))
        if len(t) > 120: t = t[:117] + "..."
        A.text(colx, yy, "[%s] %s" % (ts, t), color=INK, fontsize=9)

    _kicker(A, 0.03, 0.150, 0.40, "CROSS-ASSET ANALYSIS", MKT)
    y = 0.122
    for line in _fit(a["cross_asset"], 88, 3):
        A.text(0.03, y, line, color=INK, fontsize=10); y -= 0.018
    _kicker(A, 0.50, 0.150, 0.22, "THEMES & SENTIMENT", SOC)
    y = 0.122
    top_themes = sorted(d["themes"].items(), key=lambda x: -x[1])[:4]
    mx = top_themes[0][1] if top_themes else 1
    for k, v in top_themes:
        A.text(0.50, y, _clean(DOMAIN_NAMES.get(k, k))[:14], color=MUT2, fontsize=9)
        A.add_patch(plt.Rectangle((0.60, y + 0.002), 0.08 * v / mx, 0.009, color=MKT))
        A.text(0.69, y, str(v), color=INK, fontsize=9); y -= 0.017
    x = 0.50
    for key, col in [("bullish", UP), ("neutral", MUT2), ("bearish", DN)]:
        w = 0.15 * rolls[key] / tot
        A.add_patch(plt.Rectangle((x, y - 0.004), max(w, 0.004), 0.010, color=col)); x += w + 0.004
    A.text(x + 0.01, y - 0.004, "B%d N%d S%d" % (rolls["bullish"], rolls["neutral"], rolls["bearish"]), color=MUT2, fontsize=9)
    _kicker(A, 0.76, 0.150, 0.21, "KEY NUMBERS", GEO)
    y = 0.122
    g0 = pulse.get("gainers", [{}])[0]; l0 = pulse.get("losers", [{}])[0]
    for lab, val, col in [("GAINER", "%s %+.2f%%" % (g0.get("t", "-"), g0.get("pct", 0)) if g0.get("t") else "-", UP),
                          ("LOSER", "%s %+.2f%%" % (l0.get("t", "-"), l0.get("pct", 0)) if l0.get("t") else "-", DN),
                          ("GOLD", "%+.2f%%" % (im.get("Gold", {}).get("pct") or 0), UP if (im.get("Gold", {}).get("pct") or 0) > 0 else DN),
                          ("10Y", _fmt_price(im.get("US 10Y Yield", {}).get("price"), "bond"), GEO)]:
        A.text(0.76, y, lab, color=MUT2, fontsize=9, weight="bold")
        A.text(0.97, y, _clean(val), color=col, fontsize=9.5, ha="right", weight="bold"); y -= 0.018

    A.text(0.03, 0.02, "All charts computed from source snapshots | Tentative - machine-compiled, not investment advice", color=MUT2, fontsize=8.5)
    A.text(0.97, 0.02, "Page 2 of 2", color=MUT2, fontsize=8.5, ha="right")
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
