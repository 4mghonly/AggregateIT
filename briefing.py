"""briefing.py — AggregateIT executive briefings (MINI / MORNING / CLOSING / LIVE).
v3: canonical event store + shared market pulse + macro layer
(board, regime signals, Qwen macro read)."""
import os, json, re, time, requests
from datetime import datetime, timezone
from storage import SQLiteStore
import market
from market import load_macro_pulse, compute_regime, build_macro_embed

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
CONFIG = os.path.join(BASE, "config")

DOMAIN_NAMES = {"ME": "🌍 Middle East", "GG": "🌐 Geopolitics", "US": "🏛️ US Policy", "EC": "📊 Macro",
                "TF": "🕵️ Threat Fin", "BK": "🚨 Breaking", "TR": "🚢 Trade Routes", "CY": "🛡️ Cyber",
                "AI": "🤖 Tech/AI", "CB": "🏦 Central Banks", "MK": "💹 Markets", "XA": "🪙 Crypto",
                "RN": "🎯 Retail", "EN": "⚡ Energy", "EL": "🗳️ Elections"}
IMP_EMOJI = {"Critical": "🚨", "High": "🔥", "Medium": "📌", "Low": "ℹ️"}

def load_json(path):
    if not os.path.exists(path): return None
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except Exception: return None

def fetch_stocktwits(tickers):
    sentiments = {"bullish": 0, "bearish": 0, "neutral": 0}
    radar = []
    for t in set(tickers):
        try:
            r = requests.get(f"https://api.stocktwits.com/api/2/streams/symbol/{t}.json", timeout=5,
                             headers={"User-Agent": "AggregateIT/1.0"})
            if r.status_code == 200:
                msgs = r.json().get("messages", [])[:15]
                bull = sum(1 for m in msgs if m.get("entities", {}).get("sentiment", {}).get("basic") == "Bullish")
                bear = sum(1 for m in msgs if m.get("entities", {}).get("sentiment", {}).get("basic") == "Bearish")
                sentiments["bullish"] += bull; sentiments["bearish"] += bear
                sentiments["neutral"] += (len(msgs) - bull - bear)
                if bull + bear >= 2:
                    ratio = bull / (bull + bear)
                    radar.append(f"{'🟢' if ratio > 0.6 else ('🔴' if ratio < 0.4 else '⚪')} {t} ({bull}B/{bear}S)")
        except Exception:
            pass
        time.sleep(0.25)
    return sentiments, radar

def load_events(store, hours):
    items = []
    for ev in store.recent_all_events(hours=hours):
        try: urls = json.loads(ev.get("urls_json") or "[]")
        except Exception: urls = []
        try: srcs = json.loads(ev.get("sources_json") or "[]")
        except Exception: srcs = []
        src = srcs[0].get("name", "Unknown") if srcs else "Unknown"
        if len(srcs) > 1: src += f" +{len(srcs) - 1} more"
        items.append({"url": urls[0] if urls else "", "ts": ev.get("last_updated") or 0,
                      "title": ev.get("title") or "Untitled event", "source": src,
                      "score": ev.get("score") or 0,
                      "triggers": json.loads(ev.get("triggers_json") or "[]"),
                      "importance": ev.get("severity") or "Low",
                      "sentiment": ev.get("sentiment") or "na",
                      "summary": ev.get("assessment") or ""})
    return items

def theme_counts(items):
    counts = {}
    for i in items:
        seen = set()
        for t in i.get("triggers", []):
            m = re.match(r"([A-Z]{2})-\d+", t)
            if m and m.group(1) not in seen:
                counts[m.group(1)] = counts.get(m.group(1), 0) + 1
                seen.add(m.group(1))
    return counts

def hbar(n, mx, width=10):
    if mx <= 0 or n <= 0: return "░" * width
    filled = max(1, round(n / mx * width))
    return "█" * filled + "░" * (width - filled)

def theme_chart(items):
    tc = theme_counts(items)
    if not tc: return "No theme activity in window."
    top = sorted(tc.items(), key=lambda x: -x[1])[:5]
    return "\n".join(f"{DOMAIN_NAMES.get(k, k)} {hbar(v, top[0][1])} {v}" for k, v in top)

def sentiment_gauge(items):
    rolls = {"bullish": 0, "neutral": 0, "bearish": 0}
    for i in items:
        s = (i.get("sentiment") or "").lower()
        if s in rolls: rolls[s] += 1
    total = sum(rolls.values())
    if not total: return "➖ No news sentiment in window."
    bar = " ".join(f"{e}{'█' * round(rolls[k] / total * 10)}"
                   for k, e in (("bullish", "🟢"), ("neutral", "⚪"), ("bearish", "🔴")))
    return f"{bar} (🟢{rolls['bullish']} ⚪{rolls['neutral']} 🔴{rolls['bearish']})"

def watch_hits(items, movers):
    watch = (load_json(os.path.join(CONFIG, "watchlist.json")) or {}).get("tickers", [])
    hits = {t.upper() for t in watch if t.upper() in movers}
    for t in watch:
        tu = t.upper()
        for i in items:
            if any(tu in tr for tr in i.get("triggers", [])):
                hits.add(tu)
    return sorted(hits)

def scope_line():
    n_src = len(load_json(os.path.join(CONFIG, "sources.json")) or [])
    n_red = len(load_json(os.path.join(CONFIG, "reddit.json")) or [])
    kw = load_json(os.path.join(CONFIG, "keywords.json")) or {}
    uni = load_json(os.path.join(DATA, "tv_universe.json")) or {}
    return (f"{n_src} news sources · {n_red} subreddits · "
            f"{uni.get('total', '—')} US stocks · {len(kw.get('clusters', []))} intel clusters")

def insights(items, gainers, losers, hits):
    out = []
    tc = theme_counts(items)
    if tc:
        k, v = sorted(tc.items(), key=lambda x: -x[1])[0]
        out.append(f"{DOMAIN_NAMES.get(k, k)} is the dominant theme ({v} stories).")
    if items:
        top = max(items, key=lambda x: x.get("score", 0))
        out.append(f"Top signal: [{top.get('title', '')[:60]}]({top.get('url', '')}) · {top.get('source', '')}.")
    if gainers:
        lag = f"; {losers[0]['t']} {losers[0]['pct']:.1f}% lags" if losers else ""
        out.append(f"Market leadership: {gainers[0]['t']} +{gainers[0]['pct']:.1f}% leads{lag}.")
    if hits:
        out.append(f"Watchlist radar: {', '.join(hits)} in play.")
    crit = [i for i in items if i.get("importance") == "Critical"]
    if crit:
        out.append(f"⚠️ Risk flag: {len(crit)} critical-severity story(ies) in window.")
    if not out: out.append("Quiet cycle — no major signals in window.")
    return "\n".join(f"{n}. {t}" for n, t in enumerate(out[:4], 1))

def findings(items, hours):
    if not items:
        return f"Quiet cycle over the last {hours}h. No front-page signals; watch the theme chart for early movement."
    tc = theme_counts(items)
    top_theme = DOMAIN_NAMES.get(sorted(tc.items(), key=lambda x: -x[1])[0][0], "Mixed") if tc else "Mixed"
    top = max(items, key=lambda x: x.get("score", 0))
    lines = [f"The last {hours}h were dominated by {top_theme} coverage.",
             f"Highest-impact signal: {top.get('title', '')[:80]} ({top.get('source', '')})."]
    crit = [i for i in items if i.get("importance") == "Critical"]
    if crit: lines.append(f"⚠️ {len(crit)} critical story(ies) require attention.")
    return "\n".join(lines)

def headlines(items, n=5):
    if not items: return "No major headlines in window."
    top = sorted(items, key=lambda x: -x.get("score", 0))[:n]
    return "\n".join(f"{IMP_EMOJI.get(i.get('importance'), '📰')} [{i.get('title', '')[:70]}]({i.get('url', '')})" for i in top)

# ================= MACRO READ (Qwen) =================
MACRO_READ_SYSTEM = "You are a disciplined macro strategist. Output ONLY valid JSON."
MACRO_READ_PROMPT = """You are a macro strategist analyzing the current market backdrop.
Provide a concise macro read based on the data below. Strict rules:
- Be specific and quantitative.
- Identify risk appetite (risk-on / risk-off / mixed).
- Note any divergences (e.g., stocks up but yields falling).
- Flag one key risk or opportunity.

Output ONLY one valid JSON object:
{{
  "risk_appetite": "risk-on|risk-off|mixed",
  "rates_fx": "one-sentence read on rates and FX",
  "commodities": "one-sentence read on commodities",
  "key_risk": "one key risk or opportunity"
}}

MACRO DATA:
{macro_text}"""

def generate_macro_read(macro, regime):
    if not macro or not macro.get("valid"): return None
    inst_map = {i["sym"]: i for i in macro.get("instruments", [])}
    lines = []
    for sym in ["TVC:SPX", "TVC:NDX", "CBOE:VIX", "TVC:US10Y", "TVC:US02Y", "TVC:DXY", "NYMEX:CL1!", "COMEX:GC1!"]:
        inst = inst_map.get(sym)
        if inst and inst["pct"] is not None:
            lines.append(f"{inst['name']}: {inst['pct']:+.2f}%")
    if regime:
        for k, v in regime.items():
            lines.append(f"Regime: {k} = {v}")
    macro_text = "\n".join(lines)
    try:
        base = os.environ.get("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1").rstrip("/")
        r = requests.post(base + "/chat/completions",
            headers={"Authorization": "Bearer " + os.environ["QWEN_API_KEY"]},
            json={"model": os.environ.get("QWEN_MODEL", "qwen-plus"), "temperature": 0.3,
                  "messages": [{"role": "system", "content": MACRO_READ_SYSTEM},
                               {"role": "user", "content": MACRO_READ_PROMPT.format(macro_text=macro_text)}]},
            timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        m = re.search(r"\{[\s\S]*\}", content)
        if not m: return None
        obj = json.loads(m.group(0))
        if all(k in obj for k in ("risk_appetite", "rates_fx", "commodities", "key_risk")):
            return obj
    except Exception:
        pass
    return None

# ================= BRIEFING BUILDERS =================
def build_exec(mode):
    pulse = market.load_market_pulse()
    hours = 24
    items = load_events(SQLiteStore(), hours)
    gainers = (pulse or {}).get("gainers", [])[:4]
    losers = (pulse or {}).get("losers", [])[:4]
    hits = watch_hits(items, (pulse or {}).get("sig", {}))
    st_rolls, st_radar = fetch_stocktwits([m["t"] for m in gainers + losers] + hits)
    label = {"MORNING": "MORNING DESK", "CLOSING": "CLOSING BELL",
             "LIVE": "LIVE DESK · US SESSION"}.get(mode, "LIVE DESK · US SESSION")
    color = {"MORNING": 0xF1C40F, "CLOSING": 0x3498DB, "LIVE": 0x2ECC71}.get(mode, 0x2ECC71)
    now = datetime.now(timezone.utc).strftime("%a %Y-%m-%d %H:%M UTC")
    e1 = {"title": f"📋 EXECUTIVE BRIEFING · {label}",
          "description": f"{now} • Window: last {hours}h • **{len(items)}** tracked events",
          "color": color,
          "fields": [
              {"name": "🎯 Mission", "value": "Surface market-moving geopolitical & corporate signals before consensus.", "inline": True},
              {"name": "🧩 Scope", "value": scope_line(), "inline": True}]}
    if pulse:
        e2 = market.build_pulse_embed(pulse, color=color)
    else:
        e2 = {"title": "💹 Market Pulse", "color": color,
              "description": "No market snapshot available yet (run TradingView refresh)."}

    macro = load_macro_pulse()
    regime = compute_regime(macro) if macro else {}
    macro_embed = build_macro_embed(macro, regime, color=color) if macro else None
    macro_read = None
    if macro and macro.get("valid") and mode in ("MORNING", "CLOSING"):
        macro_read = generate_macro_read(macro, regime)

    e3 = {"title": "🔢 Data Insights", "color": color,
          "fields": [{"name": "Key signals this window", "value": insights(items, gainers, losers, hits), "inline": False}]}
    e4 = {"title": "📊 Theme Activity & Sentiment", "color": color, "fields": [
        {"name": "Intel cluster activity", "value": theme_chart(items), "inline": True},
        {"name": "News Sentiment (AI)", "value": sentiment_gauge(items), "inline": True},
        {"name": "🗣️ Retail Crowd Radar (StockTwits)", "value": "\n".join(st_radar[:6]) if st_radar else "No strong retail consensus on movers.", "inline": False}]}
    e5 = {"title": "🧾 Summary of Findings", "color": color,
          "description": findings(items, hours),
          "fields": [{"name": "📰 Top Headlines", "value": headlines(items, 5), "inline": False}],
          "footer": {"text": "AggregateIT Intelligence Terminal"},
          "timestamp": datetime.now(timezone.utc).isoformat()}

    embeds_list = [e1, e2]
    if macro_embed: embeds_list.append(macro_embed)
    if macro_read:
        embeds_list.append({"title": "🧠 Macro Read", "color": color,
            "fields": [
                {"name": "Risk Appetite", "value": macro_read.get("risk_appetite", "—"), "inline": True},
                {"name": "Rates & FX", "value": macro_read.get("rates_fx", "—"), "inline": False},
                {"name": "Commodities", "value": macro_read.get("commodities", "—"), "inline": False},
                {"name": "⚠️ Key Risk", "value": macro_read.get("key_risk", "—"), "inline": False}
            ]})
    embeds_list.extend([e3, e4, e5])
    return embeds_list

def build_mini():
    items = load_events(SQLiteStore(), 24)
    return [{"title": "🌅 AGGREGATEIT · OVERNIGHT WIRE (08:00 UAE)",
             "description": findings(items, 24), "color": 0xE67E22,
             "fields": [
                 {"name": "📰 Major Headlines", "value": headlines(items, 6), "inline": False},
                 {"name": "🧭 Theme Activity", "value": theme_chart(items), "inline": True},
                 {"name": "📊 Sentiment", "value": sentiment_gauge(items), "inline": True}],
             "footer": {"text": "AggregateIT Intelligence Terminal"},
             "timestamp": datetime.now(timezone.utc).isoformat()}]

def main():
    mode = os.environ.get("BRIEFING_MODE", "MORNING").upper()
    webhook = os.environ.get("DISCORD_WEBHOOK")
    if not webhook:
        print("FATAL: DISCORD_WEBHOOK secret is not set."); return
    embeds = build_mini() if mode == "MINI" else build_exec(mode)
    try:
        r = requests.post(webhook, json={"embeds": embeds})
        r.raise_for_status()
        print(f"✅ {mode} executive briefing delivered ({len(embeds)} panels)!")
    except Exception as e:
        print(f"Failed to send briefing: {e}")

if __name__ == "__main__":
    main()
