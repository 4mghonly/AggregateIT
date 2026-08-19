import os, re, json, time, sqlite3, asyncio, calendar, hashlib, sys
import feedparser, aiohttp, requests, trafilatura
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data"); REPORTS = os.path.join(BASE, "reports")
os.makedirs(DATA, exist_ok=True); os.makedirs(REPORTS, exist_ok=True)

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

LOOKBACK_H = int(os.environ.get("LOOKBACK_HOURS", "6"))
MAX_PER_SOURCE = 5
ALWAYS_ANALYZE = ["federal reserve", "european central bank", "cisa"]
PRIO_LIMIT = {"Very High": 10, "High": 5, "Medium": 3}
UA = {"User-Agent": "NewsIntelEngine/0.1 (personal research)"}

# ===== SIGNAL STACK tuning =====
MIN_DIGEST_SCORE = 5   # L4 floor: only items scoring >= this reach the digest / Qwen
DIGEST_CAP = 10        # L4 cap: max items analyzed + shown per run (token control)

CASHTAG_ONLY = {
    "ALL","ARE","CAT","KEY","LOW","FIX","TAP","MAS","LIN","GEN","HAL","DOW","MET",
    "ION","ARM","USB","GPS","KEYS","FAST","FLEX","LITE","DASH","FANG","COIN",
    "SNOW","JOBS","CARS","BEER","DECK",
    "HAS","APP","TECH","NOW","COST","BALL","WELL","POOL","ICE","AMP","DOC","FOX","PARA"
}

def load(n):
    with open(os.path.join(BASE, "config", n), encoding="utf-8") as f: return json.load(f)

RAW = load("sources.json"); REDDIT = load("reddit.json"); WATCH = load("watchlist.json")
_kw = load("keywords.json")
KEYWORDS_DATA = _kw["clusters"] if isinstance(_kw, dict) else _kw
PRIO_SCORE = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
for e in KEYWORDS_DATA:
    e["phrases"] = [p.lower() for p in e.get("phrases", [])]

TICK_RAW = load("tickers.json") + [{"t": x, "c": x, "s": "Watchlist"} for x in WATCH.get("tickers", [])]
T_BY_SYM = {d["t"].upper(): d for d in TICK_RAW}
SYMS = [t for t in T_BY_SYM if len(t) >= 3 and t not in CASHTAG_ONLY]
NAMES = [(d["c"].lower(), d) for d in TICK_RAW if len(d["c"]) >= 6]

# ===== Load TradingView universe + movers (graceful degradation) =====
TV_UNIVERSE = []; MOVERS = {}
try:
    _tvp = os.path.join(DATA, "tv_universe.json")
    if os.path.exists(_tvp):
        TV_UNIVERSE = json.load(open(_tvp, encoding="utf-8"))["rows"]
    _mvp = os.path.join(DATA, "movers.json")
    if os.path.exists(_mvp):
        MOVERS = json.load(open(_mvp, encoding="utf-8"))["movers"]
except Exception as e:
    print("TV data load err:", type(e).__name__)

# L1a: full-universe ticker set for $CASHTAG matching
ALL_TICKS = set(T_BY_SYM.keys()); TV_BY_TICK = {}
for _r in TV_UNIVERSE:
    _t = _r["t"].upper(); ALL_TICKS.add(_t); TV_BY_TICK[_t] = _r

# L1c: expand company-name matching with today's movers ("the market is voting")
_mover_names = {}
for _tick in MOVERS:
    _r = TV_BY_TICK.get(_tick.upper())
    if _r:
        _nm = (_r.get("c") or "").lower().strip()
        if len(_nm) >= 6:
            _mover_names[_nm] = {"t": _r["t"], "c": _r.get("c",""), "s": _r.get("s","")}
_existing_names = {n for n, _ in NAMES}
ALL_NAMES = list(NAMES) + [(nm, d) for nm, d in _mover_names.items() if nm not in _existing_names]

def _tick_info(sym):
    return T_BY_SYM.get(sym.upper()) or TV_BY_TICK.get(sym.upper())

seen_u = set(); RSS = []; GH = []
for s in RAW:
    u = s.get("Url", "").replace("http://", "https://").rstrip("/")
    if not u or u in seen_u: continue
    seen_u.add(u)
    (GH if "github.com/" in u else RSS).append({**s, "_url": u})

con = sqlite3.connect(os.path.join(DATA, "seen.db"))
con.execute("CREATE TABLE IF NOT EXISTS seen(url TEXT PRIMARY KEY, ts REAL)")
con.execute("CREATE TABLE IF NOT EXISTS seen_titles(title_hash TEXT PRIMARY KEY, url TEXT, ts REAL)")

def is_seen(u): return con.execute("SELECT 1 FROM seen WHERE url=?", (u,)).fetchone()
def mark_seen(us):
    con.executemany("INSERT OR IGNORE INTO seen(url,ts) VALUES (?,?)", [(u, time.time()) for u in us]); con.commit()

def normalize_title(title):
    t = re.sub(r'[^\w\s]', '', (title or "").lower())
    return re.sub(r'\s+', ' ', t).strip()

def title_hash(title):
    return hashlib.md5(normalize_title(title).encode()).hexdigest()

def is_title_seen(item):
    th = title_hash(item.get("title", ""))
    if th == hashlib.md5(b"").hexdigest(): return False
    return con.execute("SELECT 1 FROM seen_titles WHERE title_hash=?", (th,)).fetchone()

def mark_title_seen(items):
    rows = [(title_hash(i.get("title","")), i.get("url",""), time.time()) for i in items if i.get("title")]
    if rows:
        con.executemany("INSERT OR IGNORE INTO seen_titles(title_hash,url,ts) VALUES (?,?,?)", rows); con.commit()

CASHTAG = re.compile(r"\$([A-Za-z]{1,6})\b")

def find_matches(text):
    low = text.lower()
    return [e for e in KEYWORDS_DATA if any(p in low for p in e["phrases"])]

def score_item(i):
    text = i["title"] + " " + i["text"]; low = text.lower()
    score = 0; hits = []; matched = set()
    if any(a in i["source_name"].lower() for a in ALWAYS_ANALYZE):
        score += 5; hits.append("Priority Source")
    # L1a: $CASHTAG against full universe
    for sym in set(c.upper() for c in CASHTAG.findall(text)):
        if sym in ALL_TICKS:
            score += 3; hits.append(sym); matched.add(sym)
    # L1b: bare ticker word — S&P + watchlist only
    for t in SYMS:
        if re.search(rf"\b{re.escape(t)}\b", text, re.I):
            score += 2; hits.append(t); matched.add(t)
    # L1c: company name — S&P + watchlist + today's movers
    for name, d in ALL_NAMES:
        if name in low:
            score += 3; hits.append(d["t"]); matched.add(d["t"].upper())
    # L2: market-movers boost — once per unique matched mover
    for t in matched:
        if t.upper() in MOVERS:
            score += 4; hits.append(f"🔥 {t} MOVER")
    # Keyword clusters
    kws = find_matches(text)
    for e in kws: score += PRIO_SCORE.get(e.get("prio", "Medium"), 2)
    i["keyword_ids"] = [e["id"] for e in kws]
    i["keyword_tags"] = sorted({t for e in kws for t in e.get("tags", [])})
    labels = []
    for h in dict.fromkeys(hits):
        if h == "Priority Source" or "MOVER" in h:
            labels.append(h)
        else:
            d = _tick_info(h)
            labels.append(f"{h} ({d['c']} · {d.get('s','')})" if d else h)
    labels += [f"{e['id']} · {e['sub']}" for e in kws]
    return score, labels

async def fetch_text(session, url, sem, headers=None):
    async with sem:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20), headers=headers) as r:
                if r.status == 200: return await r.text()
        except Exception: pass
    return None

async def fetch_rss(session, src, sem):
    txt = await fetch_text(session, src["_url"], sem); out = []
    if txt:
        for e in feedparser.parse(txt).entries[:MAX_PER_SOURCE]:
            out.append({"source_type": "rss", "source_name": src.get("Source_name", ""),
                "category": src.get("Category", ""), "url": e.get("link", ""),
                "title": e.get("title", ""), "text": re.sub("<[^>]+>", "", e.get("summary", "")),
                "ts": calendar.timegm(e.published_parsed) if e.get("published_parsed") else time.time()})
    return out

async def fetch_reddit(session, r, sem):
    txt = await fetch_text(session, f"https://www.reddit.com/r/{r['sub']}/new/.rss", sem)
    out = []
    if txt:
        parsed = feedparser.parse(txt)
        for entry in parsed.entries[:PRIO_LIMIT.get(r["priority"], 3)]:
            title = entry.get("title", "").split(" :: ")[0]
            out.append({"source_type": "reddit", "source_name": "r/" + r["sub"], "category": "Reddit",
                "url": entry.get("link", ""), "title": title,
                "text": re.sub("<[^>]+>", "", entry.get("summary", "")),
                "ts": calendar.timegm(entry.published_parsed) if entry.get("published_parsed") else time.time()})
    return out

def parse_iso_ts(ts_str):
    if not ts_str: return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None

async def fetch_github(session, repo, sem, since_iso):
    hdrs = dict(UA)
    if os.environ.get("GITHUB_TOKEN"): hdrs["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    out = []
    for ep, kind in (("releases?per_page=5", "release"), (f"commits?per_page=5&since={since_iso}", "commit")):
        txt = await fetch_text(session, f"https://api.github.com/repos/{repo}/{ep}", sem, hdrs)
        if txt:
            try:
                data = json.loads(txt)
                if isinstance(data, list):
                    for it in data:
                        if kind == "release":
                            ts = parse_iso_ts(it.get("published_at") or it.get("created_at")) or time.time()
                        else:
                            ts = parse_iso_ts(it.get("commit", {}).get("committer", {}).get("date")) or time.time()
                        out.append({"source_type": "github", "source_name": repo, "category": "GitHub",
                            "url": it.get("html_url", ""), "title": (it.get("name") or it.get("commit", {}).get("message") or "")[:200],
                            "text": (it.get("body") or it.get("commit", {}).get("message") or "")[:4000], "ts": ts})
            except Exception: pass
    return out

def full_text(url, fallback):
    try:
        raw = trafilatura.fetch_url(url)
        txt = trafilatura.extract(raw, include_comments=False)
        if txt and len(txt) > 400: return txt[:4000]
    except Exception: pass
    return fallback[:4000]

PROMPT_T = """You are a precise intelligence analyst. Treat the text as sole source of truth. Output ONLY valid JSON with keys:
summary, category, importance (Low/Medium/High/Critical), keywords (list), entities (list), tickers (list), sentiment (bullish/bearish/neutral/na), event_type, countries (list), key_developments, unconfirmed_or_missing

TRIGGER CONTEXT: This article was flagged because it relates to: {cats}
SOURCE: {source_name} ({category})
TITLE: {title}
TEXT:
{text}"""

def analyze(i):
    try:
        base = os.environ.get("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1").rstrip("/")
        r = requests.post(base + "/chat/completions",
            headers={"Authorization": "Bearer " + os.environ["QWEN_API_KEY"]},
            json={"model": os.environ.get("QWEN_MODEL", "qwen3.7-flash-2026-07-15"), "temperature": 0.2,
                  "messages": [{"role": "user", "content": PROMPT_T.format(**i)}]}, timeout=120)
        m = re.search(r"\{[\s\S]*\}", r.json()["choices"][0]["message"]["content"])
        return json.loads(m.group(0)) if m else None
    except Exception as e:
        print("LLM err:", e); return None

SENT_EMOJI = {"bullish": "🟢 Bullish", "bearish": "🔴 Bearish", "neutral": "⚪ Neutral", "na": "➖ N/A"}
IMP_EMOJI = {"Critical": "🚨", "High": "🔥", "Medium": "📌", "Low": "ℹ️"}
IMP_COLOR = {"Critical": 0xE74C3C, "High": 0xE67E22, "Medium": 0xF1C40F, "Low": 0x95A5A6}

def _truncate(s, n):
    s = (s or "").strip()
    return s if len(s) <= n else s[:n-1] + "…"

def build_item_embed(i, a):
    imp = a.get("importance", "Low")
    sent = (a.get("sentiment") or "na").lower()
    tag = "💬" if i["source_type"] == "reddit" else "📰"
    fields = [
        {"name": "Sentiment", "value": SENT_EMOJI.get(sent, sent), "inline": True},
        {"name": "Importance", "value": f"{IMP_EMOJI.get(imp, '')} {imp}", "inline": True},
        {"name": "Tickers", "value": _truncate(", ".join(a.get("tickers") or []) or "-", 200), "inline": True},
    ]
    if a.get("event_type"):
        fields.append({"name": "Event Type", "value": _truncate(str(a["event_type"]), 150), "inline": True})
    fields.append({"name": "Triggered By", "value": _truncate(", ".join(i.get("matched_categories", [])) or "-", 400), "inline": False})
    return {
        "title": _truncate(f"{tag} {i['title']}", 250),
        "url": i["url"],
        "description": _truncate(a.get("summary") or "No summary available.", 900),
        "color": IMP_COLOR.get(imp, 0x95A5A6),
        "fields": fields,
        "footer": {"text": f"{i['source_name']} · relevance score {i.get('score', 0)}"},
    }

def send_digest(digest_items, report):
    wh = os.environ.get("DISCORD_WEBHOOK")
    if not wh or not digest_items: return
    news = [x for x in digest_items if x["item"]["source_type"] != "reddit"]
    social = [x for x in digest_items if x["item"]["source_type"] == "reddit"]
    rolls = {"bullish": 0, "bearish": 0, "neutral": 0, "na": 0}
    for x in digest_items:
        s = (x["analysis"].get("sentiment") or "na").lower()
        rolls[s if s in rolls else "na"] += 1
    header = {
        "title": "🧠 AggregateIT Intelligence Digest",
        "description": f"**{report['new']}** new → **{report['matched']}** matched → **{len(digest_items)}** on the front page",
        "color": 0x5865F2,
        "fields": [
            {"name": "📰 News items", "value": str(len(news)), "inline": True},
            {"name": "💬 Social items", "value": str(len(social)), "inline": True},
            {"name": "📊 Sentiment rollup", "value": f"🟢 {rolls['bullish']} · 🔴 {rolls['bearish']} · ⚪ {rolls['neutral']}", "inline": True},
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        news_embeds = [build_item_embed(x["item"], x["analysis"]) for x in news]
        social_embeds = [build_item_embed(x["item"], x["analysis"]) for x in social]
        requests.post(wh, json={"content": "**📰 NEWS SOURCES**", "embeds": [header] + news_embeds[:3]})
        for k in range(3, len(news_embeds), 4):
            requests.post(wh, json={"embeds": news_embeds[k:k+4]})
        if social_embeds:
            requests.post(wh, json={"content": "**💬 SOCIAL NETWORKS**", "embeds": social_embeds[:4]})
            for k in range(4, len(social_embeds), 4):
                requests.post(wh, json={"embeds": social_embeds[k:k+4]})
    except Exception as e:
        print("Discord digest err:", e)

async def main():
    if not DRY_RUN and not os.environ.get("QWEN_API_KEY"):
        raise SystemExit("FATAL: QWEN_API_KEY secret is not set.")

    sem, sem_rd = asyncio.Semaphore(20), asyncio.Semaphore(4)
    since = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_H)
    async with aiohttp.ClientSession(headers=UA) as s:
        batches = await asyncio.gather(
            *[fetch_rss(s, x, sem) for x in RSS],
            *[fetch_reddit(s, x, sem_rd) for x in REDDIT],
            *[fetch_github(s, x["_url"].split("github.com/")[1], sem, since.isoformat()) for x in GH])
    items = [i for b in batches if b for i in b]
    new = [i for i in items if i["ts"] >= since.timestamp() and i["url"] and not is_seen(i["url"]) and not is_title_seen(i)]

    scored = []; filtered_out = []
    for i in new:
        sc, labels = score_item(i)
        if sc > 0:
            i["matched_categories"] = labels; i["score"] = sc; i["cats"] = ", ".join(labels); scored.append(i)
        else:
            filtered_out.append(i)
    if filtered_out:
        mark_seen([i["url"] for i in filtered_out]); mark_title_seen(filtered_out)

    scored.sort(key=lambda x: -x["score"])
    # L4: Front-page curation — only digest-worthy items spend Qwen tokens
    above_floor = [x for x in scored if x["score"] >= MIN_DIGEST_SCORE]
    front_page = above_floor[:DIGEST_CAP]
    fp_ids = {id(x) for x in front_page}
    wire = [x for x in scored if id(x) not in fp_ids]

    report = {"run": datetime.now(timezone.utc).isoformat(), "dry_run": DRY_RUN,
              "fetched": len(items), "new": len(new), "matched": len(scored),
              "front_page": len(front_page), "wire": [], "analyzed": [], "would_analyze": []}
    for i in wire:
        report["wire"].append({"url": i["url"], "title": i["title"], "source": i["source_name"],
                               "score": i["score"], "triggers": i["matched_categories"]})

    processed_urls = []; processed_items = []; digest_items = []
    for i in front_page:
        if i["source_type"] == "rss": i["text"] = full_text(i["url"], i["text"])
        if DRY_RUN:
            report["would_analyze"].append({"url": i["url"], "title": i["title"], "source": i["source_name"],
                                            "score": i["score"], "triggers": i["matched_categories"]})
            processed_urls.append(i["url"]); processed_items.append(i); continue
        a = analyze(i)
        if a:
            report["analyzed"].append({"url": i["url"], "title": i["title"], "source": i["source_name"],
                                       "score": i["score"], "triggers": i["matched_categories"], "analysis": a})
            digest_items.append({"item": i, "analysis": a})
            processed_urls.append(i["url"]); processed_items.append(i)
        await asyncio.sleep(1)

    if wire:
        mark_seen([i["url"] for i in wire]); mark_title_seen(wire)
    if processed_urls:
        mark_seen(processed_urls); mark_title_seen(processed_items)

    send_digest(digest_items, report)
    with open(os.path.join(REPORTS, "run.json"), "w", encoding="utf-8") as f: json.dump(report, f, indent=2)
    extra = f" | WOULD_ANALYZE {len(report['would_analyze'])}" if DRY_RUN else ""
    mode = " [DRY RUN]" if DRY_RUN else ""
    print(f"FETCHED {report['fetched']} | NEW {report['new']} | MATCHED {report['matched']} | FRONT {report['front_page']} | ANALYZED {len(report['analyzed'])}{extra}{mode}")

if __name__ == "__main__":
    asyncio.run(main())
