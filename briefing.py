import os, json, re, time, requests
from datetime import datetime, timezone

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

def load_history(hours):
    data = load_json(os.path.join(DATA, "news_history.json"))
    if not data: return []
    cutoff = time.time() - hours * 3600
    return [i for i in data.get("items", []) if i.get("ts", 0) >= cutoff]

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
    if not total: return "➖ No sentiment data in window."
    bar = "".join(f"{e}{'█' * round(rolls[k] / total * 10)}"
                  for k, e in (("bullish", "🟢"), ("neutral", "⚪"), ("bearish", "🔴")))
    return f"{bar}  (🟢{rolls['bullish']} ⚪{rolls['neutral']} 🔴{rolls['bearish']})"

def watch_hits(items, movers):
    watch = (load_json(os.path.join(CONFIG, "watchlist.json")) or {}).get("tickers", [])
    hits = {t.upper() for t in watch if t.upper() in movers}
    for t in watch:
        tu = t.upper()
        for i in items:
            if any(tu in tr for tr in i.get("triggers", [])):
                hits.add(tu)
    return sorted(hits)

def insights(items, gainers, losers, hits):
    out = []
    tc = theme_counts(items)
    if tc:
        k, v = sorted(tc.items(), key=lambda x: -x[1])[0]
        out.append(f"{DOMAIN_NAMES.get(k, k)} is the dominant theme ({v} stories).")
    if items:
        top = max(items, key=lambda x: x.get("score", 0))
        out.append(f"Top signal: [{top.get('title', '')[:60]}]({top.get('url', '')}) · *{top.get('source', '')}*.")
    if gainers:
        lag = f"; **{losers[0]['t']}** {losers[0]['pct']:.1f}% lags" if losers else ""
        out.append(f"Market leadership: **{gainers[0]['t']}** +{gainers[0]['pct']:.1f}% leads{lag}.")
    if hits:
        out.append(f"Watchlist radar: {', '.join(hits)} in play.")
    crit = [i for i in items if i.get("importance") == "Critical"]
    if crit:
        out.append(f"⚠️ Risk flag: {len(crit)} critical-severity story(ies) in window.")
    if not out: out.append("Quiet cycle — no major signals in window.")
    return "\n".join(f"**{n}.** {t}" for n, t in enumerate(out[:4], 1))

def findings(items, hours):
    if not items:
        return f"Quiet cycle over the last {hours}h. No front-page signals; watch the theme chart for early movement."
    tc = theme_counts(items)
    top_theme = DOMAIN_NAMES.get(sorted(tc.items(), key=lambda x: -x[1])[0][0], "Mixed") if tc else "Mixed"
    top = max(items, key=lambda x: x.get("score", 0))
    lines = [f"The last {hours}h were dominated by **{top_theme}** coverage.",
             f"Highest-impact signal: **{top.get('title', '')[:80]}** ({top.get('source', '')})."]
    crit = [i for i in items if i.get("importance") == "Critical"]
    if crit: lines.append(f"⚠️ {len(crit)} critical story(ies) require attention.")
    return "\n".join(lines)

def headlines(items, n=5):
    if not items: return "No major headlines in window."
    top = sorted(items, key=lambda x: -x.get("score", 0))[:n]
    return "\n".join(f"{IMP_EMOJI.get(i.get('importance'), '📰')} [{i.get('title', '')[:70]}]({i.get('url', '')})" for i in top)

def build_exec(mode):
    uni = load_json(os.path.join(DATA, "tv_universe.json"))
    movers = (load_json(os.path.join(DATA, "movers.json")) or {}).get("movers", {})
    hours = 16 if mode == "MORNING" else 9
    items = load_history(hours)
    ml = [{"t": k, **v} for k, v in movers.items()]
    gainers = sorted([m for m in ml if m.get("pct", 0) > 0], key=lambda x: x["pct"], reverse=True)[:4]
    losers = sorted([m for m in ml if m.get("pct", 0) < 0], key=lambda x: x["pct"])[:4]
    hits = watch_hits(items, movers)
    label = "MORNING DESK" if mode == "MORNING" else "CLOSING BELL"
    color = 0xF1C40F if mode == "MORNING" else 0x3498DB
    now = datetime.now(timezone.utc).strftime("%a %Y-%m-%d %H:%M UTC")

    e1 = {"title": f"📋 EXECUTIVE BRIEFING · {label}",
          "description": f"{now} • Window: last {hours}h • **{len(items)}** relevant stories",
          "color": color,
          "fields": [
              {"name": "🎯 Mission", "value": "Surface market-moving geopolitical & corporate signals before consensus.", "inline": True},
              {"name": "🧩 Scope", "value": "95 news sources · 32 subreddits · 20k US tickers · 40+ intel clusters", "inline": True}]}

    mega = "—"
    if uni:
        top20 = sorted([r for r in uni.get("rows", []) if r.get("mcap", 0) > 0], key=lambda x: x["mcap"], reverse=True)[:20]
        fmt = lambda r: f"{'🟢' if r.get('pct', 0) >= 0 else '🔴'} {r['t']} {r.get('pct', 0):+.1f}%"
        mega = " | ".join(fmt(r) for r in top20[:10]) + "\n" + " | ".join(fmt(r) for r in top20[10:])

    e2 = {"title": "💹 Market Pulse", "color": color, "fields": [
        {"name": "🚀 Top Movers", "value": "\n".join(f"**{m['t']}** +{m['pct']:.1f}% ({m.get('relvol', 0):.1f}x)" for m in gainers) or "—", "inline": True},
        {"name": "📉 Top Fallers", "value": "\n".join(f"**{m['t']}** {m['pct']:.1f}% ({m.get('relvol', 0):.1f}x)" for m in losers) or "—", "inline": True},
        {"name": "🏛️ Mega-Cap Scoreboard (Top 20)", "value": mega, "inline": False}]}

    e3 = {"title": "🔢 Data Insights", "color": color,
          "fields": [{"name": "Key signals this window", "value": insights(items, gainers, losers, hits), "inline": False}]}

    e4 = {"title": "📊 Theme Activity & Sentiment", "color": color, "fields": [
        {"name": "Intel cluster activity", "value": theme_chart(items), "inline": True},
        {"name": "Sentiment gauge", "value": sentiment_gauge(items), "inline": True}]}

    e5 = {"title": "🧾 Summary of Findings", "color": color,
          "description": findings(items, hours),
          "fields": [{"name": "📰 Top Headlines", "value": headlines(items, 5), "inline": False}],
          "footer": {"text": "AggregateIT Intelligence Terminal"},
          "timestamp": datetime.now(timezone.utc).isoformat()}
    return [e1, e2, e3, e4, e5]

def build_mini():
    items = load_history(16)
    return [{"title": "🌅 AGGREGATEIT · OVERNIGHT WIRE (08:00 UAE)",
             "description": findings(items, 16), "color": 0xE67E22,
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
