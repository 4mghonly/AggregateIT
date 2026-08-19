import os, json, re, time, requests
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

DOMAIN_NAMES = {"ME": "🌍 Middle East", "GG": "🌐 Geopolitics", "US": "🏛️ US Policy", "EC": "📊 Macro",
                "TF": "🕵️ Threat Finance", "BK": "🚨 Breaking", "TR": "🚢 Trade Routes", "CY": "🛡️ Cyber",
                "AI": "🤖 Tech/AI", "CB": "🏦 Central Banks", "MK": "💹 Markets", "XA": "🪙 Crypto",
                "RN": "🎯 Retail", "EN": "⚡ Energy", "EL": "🗳️ Elections"}

def load_json(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path): return None
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except Exception:
        return None

def load_history(hours):
    data = load_json("news_history.json")
    if not data: return []
    cutoff = time.time() - hours * 3600
    return [i for i in data.get("items", []) if i.get("ts", 0) >= cutoff]

def theme_breakdown(items):
    counts = {}
    for i in items:
        for t in i.get("triggers", []):
            m = re.match(r"([A-Z]{2})-\d+", t)
            if m: counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    top = sorted(counts.items(), key=lambda x: -x[1])[:4]
    return " · ".join([f"{DOMAIN_NAMES.get(k, k)} ×{v}" for k, v in top]) or "—"

def news_cycle_summary(items, hours):
    if not items:
        return f"📡 Quiet cycle: no major matches in the last {hours}h."
    top = max(items, key=lambda x: x.get("score", 0))
    return "\n".join([
        f"📡 **{len(items)}** relevant stories in the last {hours}h",
        f"🧭 {theme_breakdown(items)}",
        f"⭐ Top: {top.get('title', '')[:90]}"])

def headlines_block(items, n=5):
    if not items: return "No major news matched the taxonomy in this window."
    top = sorted(items, key=lambda x: -x.get("score", 0))[:n]
    out = []
    for i in top:
        emoji = {"Critical": "🚨", "High": "🔥", "Medium": "📌", "Low": "ℹ️"}.get(i.get("importance"), "📰")
        out.append(f"{emoji} [{i.get('title','')[:75]}]({i.get('url','')}) · *{i.get('source','')}*")
    return "\n".join(out)

def build_mini():
    items = load_history(16)
    return {
        "title": "🌅 AGGREGATEIT · OVERNIGHT WIRE (08:00 UAE)",
        "description": news_cycle_summary(items, 16),
        "color": 0xE67E22,
        "fields": [{"name": "📰 Major Headlines (last 16h)", "value": headlines_block(items, 8), "inline": False}],
        "footer": {"text": "AggregateIT Intelligence Terminal"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

def build_briefing(mode="MORNING"):
    uni_data = load_json("tv_universe.json")
    movers_data = load_json("movers.json")
    if not uni_data or not movers_data:
        return None, "Missing TradingView data. Run the TV Refresh workflow first."
    uni = uni_data.get("rows", [])
    movers = movers_data.get("movers", {})

    top_20 = sorted([r for r in uni if r.get("mcap", 0) > 0], key=lambda x: x["mcap"], reverse=True)[:20]
    mega_caps = []
    for r in top_20:
        pct = r.get("pct", 0)
        mega_caps.append(f"{'🟢' if pct >= 0 else '🔴'} {r['t']} {pct:+.2f}%")

    mover_list = [{"t": k, **v} for k, v in movers.items()]
    gainers = sorted([m for m in mover_list if m.get("pct", 0) > 0], key=lambda x: x["pct"], reverse=True)[:5]
    losers = sorted([m for m in mover_list if m.get("pct", 0) < 0], key=lambda x: x["pct"])[:5]
    gainers_txt = "\n".join([f"🚀 **{m['t']}** +{m['pct']:.1f}% ({m.get('relvol', 0):.1f}x vol)" for m in gainers]) or "—"
    losers_txt = "\n".join([f"📉 **{m['t']}** {m['pct']:.1f}% ({m.get('relvol', 0):.1f}x vol)" for m in losers]) or "—"

    hours = 16 if mode == "MORNING" else 9
    items = load_history(hours)
    color = 0xF1C40F if mode == "MORNING" else 0x3498DB
    title = f"☀️ AGGREGATEIT · THE MORNING DESK" if mode == "MORNING" else f"🔔 AGGREGATEIT · THE CLOSING BELL"

    return {
        "title": title,
        "description": f"Market & Intelligence Briefing • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "color": color,
        "fields": [
            {"name": "🔄 News Cycle Summary", "value": news_cycle_summary(items, hours), "inline": False},
            {"name": "🚀 Top Movers", "value": gainers_txt, "inline": True},
            {"name": "📉 Top Fallers", "value": losers_txt, "inline": True},
            {"name": "🏛️ Mega-Caps (Top 20)", "value": " | ".join(mega_caps[:10]) + "\n" + " | ".join(mega_caps[10:]), "inline": False},
            {"name": "📰 Top News Narratives", "value": headlines_block(items, 5), "inline": False},
        ],
        "footer": {"text": "AggregateIT Intelligence Terminal"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, None

def main():
    mode = os.environ.get("BRIEFING_MODE", "MORNING").upper()
    webhook = os.environ.get("DISCORD_WEBHOOK")
    if not webhook:
        print("FATAL: DISCORD_WEBHOOK secret is not set."); return
    if mode == "MINI":
        embed, err = build_mini(), None
    else:
        embed, err = build_briefing(mode)
    if err:
        print(f"Error: {err}"); return
    try:
        r = requests.post(webhook, json={"embeds": [embed]})
        r.raise_for_status()
        print(f"✅ {mode} briefing delivered to Discord!")
    except Exception as e:
        print(f"Failed to send briefing: {e}")

if __name__ == "__main__":
    main()
