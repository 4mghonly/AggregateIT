"""slide.py — v5 professional two-page intelligence deck.
Rich, tidy, text+visual combined. LLM narrative prevalent (7 validated blocks).
Delta vs previous briefing via persisted deck_state.json. Fresh snapshots are
fetched by the workflow before render. Charts computed strictly from data."""
import os, json, re, time, textwrap, hashlib, requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime, timezone
from storage import SQLiteStore
import market
from briefing import fetch_stocktwits, theme_counts, DOMAIN_NAMES

BASE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(BASE, "reports")
DATA = market.DATA
P1 = os.path.join(REPORTS, "intel_slide_p1.png")
P2 = os.path.join(REPORTS, "intel_slide_p2.png")
STATE = os.path.join(DATA, "deck_state.json")

BG, PANEL, TXT, MUT = "#1e1f22", "#2b2d31", "#dbdee1", "#949ba4"
GRN, RED, AMB, BLU = "#2ecc71", "#e74c3c", "#f1c40f", "#5865f2"
SEV_COLOR = {"Critical": RED, "High": AMB, "Medium": "#e67e22", "Low": MUT}
SEV_RANK = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}

_EMOJI_RE = re.compile("["
    u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF" u"\U0001F680-\U0001F6FF"
    u"\U0001F1E0-\U0001F1FF" u"\U00002702-\U000027B0" u"\U000024C2-\U0001F251"
    "]+", flags=re.UNICODE)

def _clean(s): return _EMOJI_RE.sub("", s or "").strip()
def _wrap(s, n): return textwrap.wrap(_clean(s), n) or [""]
def _pct(v): return "-" if v is None else ("%+.2f%%" % v)

# ================= COLLECT =================
def collect():
    store = SQLiteStore()
    pulse = market.load_market_pulse() or {}
    macro = market.load_macro_pulse() or {}
    regime = market.compute_regime(macro) if macro else {}
    raw = store.recent_all_events(hours=24, limit=200)
    events = []
    for ev in raw:
        try: srcs = json.loads(ev.get("sources_json") or "[]")
        except Exception: srcs = []
        events.append({"id": ev.get("event_id"), "title": ev.get("title") or "",
                       "sev": ev.get("severity") or "Low", "st": ev.get("status") or "NEW",
                       "cf": ev.get("confidence"), "sent": ev.get("sentiment") or "na",
                       "ts": ev.get("last_updated") or 0, "score": ev.get("score") or 0,
                       "srcs": srcs, "src": srcs[0].get("name", "?") if srcs else "?",
                       "trig": json.loads(ev.get("triggers_json") or "[]")})
    events.sort(key=lambda e: (SEV_RANK.get(e["sev"], 4), -e["score"]))
    themes = theme_counts([{"triggers": e["trig"]} for e in events])
    movers_t = [m["t"] for m in (pulse.get("gainers", []) + pulse.get("losers", []))[:8]]
    st_sent, st_radar = fetch_stocktwits(movers_t)
    fam = {}
    for e in events:
        for s in e["srcs"]: fam[s.get("name", "?")] = fam.get(s.get("name", "?"), 0) + 1
    prev = None
    try:
        with open(STATE, encoding="utf-8") as f: prev = json.load(f)
    except Exception: pass
    changes, seq = compute_changes(prev, events, pulse, macro)
    return {"store": store, "pulse": pulse, "macro": macro, "regime": regime,
            "events": events, "themes": themes, "st_radar": st_radar, "fam": fam,
            "changes": changes, "seq": seq, "prev": prev}

def compute_changes(prev, events, pulse, macro):
    if not prev:
        return ["First briefing in series - no prior deck to compare."], 1
    ch = []
    pe = prev.get("events", {})
    for e in events:
        h = hashlib.md5(e["title"].lower().encode()).hexdigest()[:10]
        old = pe.get(h)
        if not old:
            ch.append("NEW event: %s" % e["title"][:60])
        else:
            if old.get("st") != e["st"]:
                ch.append("%s: %s -> %s" % (e["title"][:40], old.get("st"), e["st"]))
            if old.get("cf") is not None and e["cf"] is not None and abs(e["cf"] - old["cf"]) >= 5:
                ch.append("%s: confidence %s -> %s" % (e["title"][:40], old["cf"], e["cf"]))
    for name, now in (macro.get("instruments") or []) and {i["name"]: i["pct"] for i in macro["instruments"] if i.get("pct") is not None}.items() or {}:
        was = prev.get("macro", {}).get(name)
        if was is not None and now is not None and abs(now - was) >= 0.5:
            ch.append("MACRO %s %+.2f%% now vs %+.2f%% prior (%+.2fpp)" % (name, now, was, now - was))
    for t, m in (pulse.get("mega_caps") or []) and {m["t"]: m for m in pulse["mega_caps"] if m.get("pct") is not None}.items() or {}:
        was = prev.get("eq", {}).get(t)
        if was is not None and abs(m["pct"] - was) >= 1.0:
            ch.append("EQUITY %s %+.2f%% now vs %+.2f%% prior" % (t, m["pct"], was))
    ch = ch[:10]
    if not ch: ch = ["No material changes since the previous briefing."]
    return ch, prev.get("seq", 0) + 1

def save_state(d):
    st = {"seq": d["seq"], "ts": time.time(), "events": {}, "macro": {}, "eq": {}}
    for e in d["events"]:
        h = hashlib.md5(e["title"].lower().encode()).hexdigest()[:10]
        st["events"][h] = {"st": e["st"], "cf": e["cf"]}
    for i in d["macro"].get("instruments", []):
        if i.get("pct") is not None: st["macro"][i["name"]] = i["pct"]
    for m in d["pulse"].get("mega_caps", []):
        if m.get("pct") is not None: st["eq"][m["t"]] = m["pct"]
    try:
        with open(STATE, "w", encoding="utf-8") as f: json.dump(st, f)
    except Exception: pass

# ================= ANALYSIS =================
ANALYSIS_PROMPT = """You are a senior cross-asset intelligence analyst producing a professional
briefing deck. Write TENTATIVE, quantitative narrative. Rules: only use numbers present in the
data; never invent tickers/prices/events; NO EMOJIS; each field <= 700 chars.
Return ONLY this JSON:
{
  "summary": "3-4 sentence executive summary tying dominant news to observed market moves",
  "news_read": "2-3 sentences on the most material news clusters and sources driving them",
  "market_read": "2-3 sentences on equities, rates, FX, commodities and breadth",
  "social_read": "1-2 sentences on retail/social chatter vs price action",
  "macro_micro": "2-3 sentences explicitly linking the macro regime to the micro/corporate events and movers",
  "changes": "2-3 sentences explaining what changed since the previous briefing and why it matters",
  "key_risk": "one sentence: the most important risk or opportunity next"
}

DATA:
__DATA__"""

def _data_text(d):
    L = ["SEQ briefing #%s" % d["seq"]]
    for e in d["events"][:10]:
        L.append("EVENT [%s/%s/src %s] %s" % (e["sev"], e["st"], e["src"], e["title"]))
    for m in (d["pulse"].get("gainers", []) + d["pulse"].get("losers", []))[:10]:
        L.append("MOVER %s %s" % (m["t"], _pct(m["pct"])))
    for i in d["macro"].get("instruments", []):
        if i.get("pct") is not None: L.append("MACRO %s %s" % (i["name"], _pct(i["pct"])))
    for k, v in d["regime"].items(): L.append("REGIME %s=%s" % (k, v))
    for k, v in sorted(d["themes"].items(), key=lambda x: -x[1])[:6]:
        L.append("THEME %s x%d" % (DOMAIN_NAMES.get(k, k), v))
    for k, v in sorted(d["fam"].items(), key=lambda x: -x[1])[:8]:
        L.append("SOURCE %s x%d" % (k, v))
    if d["st_radar"]: L.append("STOCKTWITS " + " | ".join(d["st_radar"][:6]))
    L.append("CHANGES SINCE LAST BRIEFING:")
    L += ["- " + c for c in d["changes"]]
    return "\n".join(L)

def _fallback(d):
    ev, pulse, regime = d["events"], d["pulse"], d["regime"]
    g, l = pulse.get("gainers", []), pulse.get("losers", [])
    adv = sum(1 for m in pulse.get("mega_caps", []) if (m.get("pct") or 0) > 0)
    dec = sum(1 for m in pulse.get("mega_caps", []) if (m.get("pct") or 0) < 0)
    lead = ("led by %s %s" % (g[0]["t"], _pct(g[0]["pct"]))) if g else "quiet"
    lag = (", %s %s lags" % (l[0]["t"], _pct(l[0]["pct"]))) if l else ""
    mkt = ("Equities %s%s; breadth %d adv / %d dec; VIX %s; 2s10s %s; DXY %s."
           % (lead, lag, adv, dec, regime.get("vix", "n/a"), regime.get("curve_2s10s", "n/a"), regime.get("dxy", "n/a")))
    dom = DOMAIN_NAMES.get(sorted(d["themes"].items(), key=lambda x: -x[1])[0][0], "Mixed") if d["themes"] else "Mixed"
    news = "Dominant cluster: %s (%d events in 24h)." % (dom, len(ev))
    if ev: news += " Most material: %s (%s, %s)." % (ev[0]["title"][:70], ev[0]["src"], ev[0]["sev"])
    soc = (" | ".join(d["st_radar"][:4]) if d["st_radar"] else "No strong retail consensus on movers.")
    mm = ("Macro backdrop (%s VIX, %s curve) frames the micro picture: %s."
          % (regime.get("vix", "n/a"), regime.get("curve_2s10s", "n/a"),
             ("energy-linked names and movers dominate" if d["themes"] else "corporate news is driving isolated movers")))
    chg = " ".join(d["changes"][:3])
    risk = ("Monitor escalation in the dominant cluster against the next session open."
            if ev else "Quiet tape - primary risk is an off-hours headline gap.")
    summ = ("%s %s %s" % (news, mkt, soc))[:700]
    return {"summary": summ, "news_read": news[:700], "market_read": mkt[:700],
            "social_read": soc[:700], "macro_micro": mm[:700], "changes": chg[:700], "key_risk": risk[:700]}

def analyze(d):
    try:
        base = os.environ.get("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1").rstrip("/")
        r = requests.post(base + "/chat/completions",
            headers={"Authorization": "Bearer " + os.environ["QWEN_API_KEY"]},
            json={"model": os.environ.get("QWEN_MODEL", "qwen-plus"), "temperature": 0.3,
                  "messages": [{"role": "system", "content": "Disciplined analyst. ONLY valid JSON. NO EMOJIS."},
                               {"role": "user", "content": ANALYSIS_PROMPT.replace("__DATA__", _data_text(d))}]},
            timeout=90)
        r.raise_for_status()
        m = re.search(r"\{[\s\S]*\}", r.json()["choices"][0]["message"]["content"])
        if m:
            obj = json.loads(m.group(0))
            keys = ("summary", "news_read", "market_read", "social_read", "macro_micro", "changes", "key_risk")
            if all(isinstance(obj.get(k), str) and 10 <= len(obj.get(k)) <= 700 for k in keys):
                return obj, True
    except Exception:
        pass
    return _fallback(d), False

# ================= RENDER P1 =================
def _sec(ax, x, y, t, col=BLU, size=11.5):
    ax.text(x, y, _clean(t), color=col, fontsize=size, weight="bold")
    return y - 0.024

def render_p1(d, a, llm_ok):
    fig = plt.figure(figsize=(16, 9), dpi=120); fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    now = datetime.now(timezone.utc).strftime("%a %Y-%m-%d %H:%M UTC")
    session = "LIVE US SESSION" if d["pulse"].get("session_open") else "PREVIOUS SESSION"
    ax.text(0.03, 0.965, "AGGREGATEIT - INTELLIGENCE DECK · PAGE 1/2", color=TXT, fontsize=20, weight="bold")
    ax.text(0.97, 0.965, "BRIEF #%d · %s · %s" % (d["seq"], now, session), color=MUT, fontsize=10.5, ha="right")
    ax.add_patch(plt.Rectangle((0.03, 0.947), 0.94, 0.006, color=BLU))

    y = _sec(ax, 0.03, 0.925, "EXECUTIVE SUMMARY (TENTATIVE)")
    for line in _wrap(a["summary"], 108)[:4]:
        ax.text(0.03, y, line, color=TXT, fontsize=11.5); y -= 0.0235
    ax.add_patch(plt.Rectangle((0.66, 0.845), 0.31, 0.075, color="#3a2b2b"))
    ax.text(0.668, 0.905, "KEY RISK", color=RED, fontsize=10.5, weight="bold")
    for i, line in enumerate(_wrap(a["key_risk"], 52)[:2]):
        ax.text(0.668, 0.884 - i * 0.022, line, color=TXT, fontsize=9.5)

    y0 = 0.80
    # Column 1
    x = 0.03
    y = _sec(ax, x, y0, "NEWS READ", AMB)
    for line in _wrap(a["news_read"], 56)[:3]:
        ax.text(x, y, line, color=TXT, fontsize=9.5); y -= 0.021
    y -= 0.012
    y = _sec(ax, x, y, "SINCE LAST BRIEFING", AMB)
    for line in _wrap(a["changes"], 56)[:3]:
        ax.text(x, y, line, color=TXT, fontsize=9.5); y -= 0.021
    y -= 0.004
    for c in d["changes"][:3]:
        ax.text(x, y, "· " + _clean(c)[:62], color=MUT, fontsize=8.5); y -= 0.019
    # Column 2
    x = 0.365
    y = _sec(ax, x, y0, "MARKET READ", GRN)
    for line in _wrap(a["market_read"], 56)[:3]:
        ax.text(x, y, line, color=TXT, fontsize=9.5); y -= 0.021
    y -= 0.012
    y = _sec(ax, x, y, "MACRO - MICRO LINK", GRN)
    for line in _wrap(a["macro_micro"], 56)[:4]:
        ax.text(x, y, line, color=TXT, fontsize=9.5); y -= 0.021
    # Column 3
    x = 0.70
    y = _sec(ax, x, y0, "SOCIAL READ", "#e67e22")
    for line in _wrap(a["social_read"], 56)[:3]:
        ax.text(x, y, line, color=TXT, fontsize=9.5); y -= 0.021
    y -= 0.004
    for line in (d["st_radar"][:3] or ["No retail consensus on movers."]):
        ax.text(x, y, _clean(line)[:58], color=MUT, fontsize=8.5); y -= 0.019

    y1 = 0.47
    # Events
    x = 0.03
    y = _sec(ax, x, y1, "TOP EVENTS (24H)")
    for e in d["events"][:6]:
        ax.add_patch(plt.Rectangle((x, y - 0.008), 0.004, 0.02, color=SEV_COLOR.get(e["sev"], MUT)))
        ax.text(x + 0.01, y, _wrap(e["title"], 44)[0], color=TXT, fontsize=9.5, weight="bold")
        cf = "-" if e["cf"] is None else ("%d%%" % e["cf"])
        ax.text(x + 0.01, y - 0.018, "%s · conf %s · %s · src %s" % (e["sev"], cf, e["st"], e["src"][:18]),
                color=MUT, fontsize=8); y -= 0.042
    # Headlines
    x = 0.365
    y = _sec(ax, x, y1, "TODAY'S HEADLINES (BY SOURCE)")
    for e in sorted(d["events"], key=lambda e: -e["ts"])[:9]:
        ax.text(x, y, "[%s] %s" % (e["src"][:14], _wrap(e["title"], 40)[0]), color=TXT, fontsize=8.5)
        y -= 0.0265
    # Themes + source mix + sentiment
    x = 0.70
    y = _sec(ax, x, y1, "THEME ACTIVITY")
    top = sorted(d["themes"].items(), key=lambda x2: -x2[1])[:4]
    mx = top[0][1] if top else 1
    for k, v in top:
        ax.text(x, y, _clean(DOMAIN_NAMES.get(k, k))[:20], color=MUT, fontsize=8.5)
        ax.add_patch(plt.Rectangle((x + 0.12, y + 0.002), 0.14 * v / mx, 0.011, color=BLU))
        ax.text(x + 0.27, y, str(v), color=TXT, fontsize=8.5); y -= 0.024
    y -= 0.01
    y = _sec(ax, x, y, "SOURCE MIX (24H)")
    for k, v in sorted(d["fam"].items(), key=lambda x2: -x2[1])[:4]:
        ax.text(x, y, _clean(k)[:24], color=MUT, fontsize=8.5)
        ax.text(x + 0.22, y, "x%d" % v, color=TXT, fontsize=8.5); y -= 0.022
    y -= 0.008
    rolls = {"bullish": 0, "neutral": 0, "bearish": 0}
    for e in d["events"]:
        s = (e["sent"] or "").lower()
        if s in rolls: rolls[s] += 1
    tot = max(sum(rolls.values()), 1)
    ax.text(x, y, "SENTIMENT", color=BLU, fontsize=10, weight="bold"); y -= 0.02
    xx = x
    for key, col in (("bullish", GRN), ("neutral", MUT), ("bearish", RED)):
        w = 0.24 * rolls[key] / tot
        ax.add_patch(plt.Rectangle((xx, y), max(w, 0.004), 0.012, color=col)); xx += w + 0.004
    ax.text(xx + 0.01, y, "%d/%d/%d" % (rolls["bullish"], rolls["neutral"], rolls["bearish"]), color=MUT, fontsize=8.5)

    mode = "Qwen (validated)" if llm_ok else "deterministic fallback"
    ax.text(0.03, 0.02, "Narrative: %s · all charts computed from source snapshots · machine-compiled, unverified" % mode,
            color=MUT, fontsize=8.5)
    fig.savefig(P1, facecolor=BG); plt.close(fig)

# ================= RENDER P2 =================
def _style_ax(ax):
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=MUT, labelsize=8)
    for s in ax.spines.values(): s.set_color("#3f4147")
    ax.title.set_color(TXT); ax.title.set_fontsize(10)

def render_p2(d, a):
    fig, axs = plt.subplots(3, 2, figsize=(16, 9), dpi=120)
    fig.patch.set_facecolor(BG)
    fig.suptitle("AGGREGATEIT - THE NUMBERS · BRIEF #%d · %s"
                 % (d["seq"], datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")),
                 color=TXT, fontsize=15, weight="bold", y=0.98)
    pulse, macro, regime = d["pulse"], d["macro"], d["regime"]

    ax = axs[0, 0]; _style_ax(ax)
    mega = [m for m in pulse.get("mega_caps", []) if m.get("pct") is not None][:12]
    adv = sum(1 for m in mega if m["pct"] > 0)
    ax.set_title("EQUITY LEADERS · breadth %d/%d advancing" % (adv, len(mega) or 0))
    if mega:
        ax.barh([m["t"] for m in mega][::-1], [m["pct"] for m in mega][::-1],
                color=[GRN if v > 0 else RED for v in [m["pct"] for m in mega][::-1]])
        ax.axvline(0, color=MUT, lw=0.7)
    else: ax.text(0.5, 0.5, "no data", color=MUT, ha="center")

    ax = axs[0, 1]; _style_ax(ax); ax.set_title("CROSS-ASSET (macro + micro, pct chg)")
    rows = []
    for m in mega[:4]: rows.append(("EQ " + m["t"], m["pct"]))
    for i in macro.get("instruments", []):
        if i.get("pct") is not None:
            tag = {"index": "IX", "future": "CM", "forex": "FX", "bond": "RT"}.get(i.get("type"), "MA")
            rows.append((tag + " " + i["name"], i["pct"]))
    rows = rows[:16]
    if rows:
        ax.barh([r[0] for r in rows][::-1], [r[1] for r in rows][::-1],
                color=[GRN if v > 0 else RED for _, v in rows][::-1])
        ax.axvline(0, color=MUT, lw=0.7)
    else: ax.text(0.5, 0.5, "no data", color=MUT, ha="center")

    ax = axs[1, 0]; _style_ax(ax); ax.set_title("US YIELD CURVE (levels)")
    im = {i["sym"]: i for i in macro.get("instruments", [])}
    pts = [(n, (im.get(s) or {}).get("price")) for n, s in (("2Y", "TVC:US02Y"), ("10Y", "TVC:US10Y"), ("30Y", "TVC:US30Y"))]
    pts = [(n, p) for n, p in pts if p is not None]
    if pts:
        ax.plot([n for n, _ in pts], [p for _, p in pts], marker="o", color=AMB, lw=2)
        spread = (pts[-1][1] - pts[0][1]) * 100
        ax.set_title("US YIELD CURVE · 2s10s %+.0fbp%s" % (spread, " INVERTED" if spread < 0 else ""))
    else: ax.text(0.5, 0.5, "no data", color=MUT, ha="center")

    ax = axs[1, 1]; _style_ax(ax); ax.set_title("SIGNIFICANT MOVERS (pct x rel-vol, clipped p95)")
    sig = [{"t": k, **v} for k, v in pulse.get("sig", {}).items()
           if v.get("pct") is not None and v.get("relvol")][:60]
    if sig:
        cap = sorted(v["relvol"] for v in sig)[int(len(sig) * 0.95)]
        ax.scatter([v["pct"] for v in sig], [min(v["relvol"], cap) for v in sig],
                   c=[GRN if v["pct"] > 0 else RED for v in sig], s=20, alpha=0.8)
        for v in sorted(sig, key=lambda x: -x["relvol"])[:4]:
            ax.annotate(v["t"], (v["pct"], min(v["relvol"], cap)), color=TXT, fontsize=7.5,
                        xytext=(3, 3), textcoords="offset points")
        ax.set_xlabel("pct chg", color=MUT, fontsize=8); ax.set_ylabel("rel-vol", color=MUT, fontsize=8)
    else: ax.text(0.5, 0.5, "no data", color=MUT, ha="center")

    ax = axs[2, 0]; _style_ax(ax); ax.set_title("NEWS FLOW (events by 4h bucket, 24h)")
    now = time.time()
    buckets = [0] * 6
    for e in d["events"]:
        age = (now - e["ts"]) / 3600.0
        if 0 <= age < 24: buckets[5 - int(age // 4)] += 1
    ax.bar(["-24h", "-20h", "-16h", "-12h", "-8h", "-4h"], buckets, color=BLU)

    ax = axs[2, 1]; ax.set_axis_off(); ax.set_facecolor(PANEL)
    ax.set_title("SINCE LAST BRIEFING", color=TXT, fontsize=10, loc="left")
    y = 0.86
    for c in d["changes"][:8]:
        for i, line in enumerate(_wrap(c, 62)[:2]):
            ax.text(0.02, y, ("· " if i == 0 else "  ") + line, color=TXT if i == 0 else MUT, fontsize=8.5)
            y -= 0.09
    fig.tight_layout(rect=[0, 0.10, 1, 0.955])
    fig.text(0.5, 0.062, "CROSS-ASSET READ: " + _clean(a["macro_micro"])[:210], color=AMB, fontsize=9.5, ha="center")
    foot = " · ".join(filter(None, [
        "VIX %s" % regime["vix"] if regime.get("vix") else "",
        "DXY %s" % regime["dxy"] if regime.get("dxy") else "",
        "oil %s" % regime["oil_spike"] if regime.get("oil_spike") else "",
        "pulse %s" % (datetime.fromtimestamp(pulse["updated"], timezone.utc).strftime("%H:%M") if pulse.get("updated") else "n/a"),
        "macro %d inst" % len(macro.get("instruments", [])),
        "ALL FIGURES FROM SOURCE SNAPSHOTS"]))
    fig.text(0.5, 0.02, _clean(foot), color=MUT, fontsize=8.5, ha="center")
    fig.savefig(P2, facecolor=BG); plt.close(fig)

def send(pages):
    wh = os.environ.get("DISCORD_WEBHOOK")
    if not wh:
        print("FATAL: DISCORD_WEBHOOK secret is not set."); return
    files = []
    for i, p in enumerate(pages):
        files.append(("files[%d]" % i, (os.path.basename(p), open(p, "rb"), "image/png")))
    r = requests.post(wh, files=files,
                      data={"payload_json": json.dumps({"content": "📊 **AggregateIT Intelligence Deck #%s** (tentative, machine-compiled)" % 0})})
    if r.status_code >= 400:
        raise RuntimeError("Discord HTTP %d: %s" % (r.status_code, r.text[:120]))
    print("✅ Deck delivered (2 pages)!")

if __name__ == "__main__":
    os.makedirs(REPORTS, exist_ok=True)
    data = collect()
    analysis, llm_ok = analyze(data)
    render_p1(data, analysis, llm_ok)
    render_p2(data, analysis)
    save_state(data)
    send([P1, P2])
