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

def fetch_stocktwits(tickers):
    """Fetches live retail sentiment from StockTwits for top movers/watchlist."""
    sentiments = {"bullish": 0, "bearish": 0, "neutral": 0}
    radar = []
    for t in set(tickers):
        try:
            url = f"https://api.stocktwits.com/api/2/streams/symbol/{t}.json"
            r = requests.get(url, timeout=5, headers={"User-Agent": "AggregateIT/1.0"})
            if r.status_code == 200:
                msgs = r.json().get("messages", [])[:15]
                bull = sum(1 for m in msgs if m.get("entities", {}).get("sentiment", {}).get("basic") == "Bullish")
                bear = sum(1 for m in msgs if m.get("entities", {}).get("sentiment", {}).get("basic") == "Bearish")
                sentiments["bullish"] += bull
                sentiments["bearish"] += bear
                sentiments["neutral"] += (len(msgs) - bull - bear)
                if bull + bear >= 2:
                    ratio = bull / (bull + bear)
                    emoji = "🟢" if ratio > 0.6 else ("🔴" if ratio < 0.4 else "⚪")
                    radar.append(f"{emoji} **{t}** ({bull}B/{bear}S)")
        except Exception:
            pass
        time.sleep(0.25)
    return sentiments, radar

def load_json(path):
    if not os.path.exists(path): return None
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except Exception: return None

def load_history(hours):
    import sqlite3
    path = os.path.join(DATA, "seen.db")
    if not os.path.exists(path): return []
    cutoff = time.time() - hours * 3600
    try:
        c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        rows = c.execute("SELECT url, ts, title, source, score, triggers, importance, sentiment, summary "
                         "FROM history WHERE ts >= ?", (cutoff,)).fetchall()
        c.close()
    except Exception:
        return []
    return [{"url": r[0], "ts": r[1], "title": r[2], "source": r[3], "score": r[4],
             "triggers": json.loads(r[5] or "[]"), "importance": r[6], "sentiment": r[7],
             "summary": r[8]} for r in rows]

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
    return "\n".join(f
