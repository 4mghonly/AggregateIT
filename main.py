import os, re, json, time, sqlite3, asyncio, calendar, hashlib, sys
import feedparser, aiohttp, requests, trafilatura
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data"); REPORTS = os.path.join(BASE, "reports")
os.makedirs(DATA, exist_ok=True); os.makedirs(REPORTS, exist_ok=True)

# --- Runtime mode ---
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

LOOKBACK_H = int(os.environ.get("LOOKBACK_HOURS", "6"))
MAX_PER_SOURCE = 5
MAX_ANALYZE = 15  # hard cap on LLM calls per run = cost guard
ALWAYS_ANALYZE = ["federal reserve", "european central bank", "cisa"]
PRIO_LIMIT = {"Very High": 10, "High": 5, "Medium": 3}
UA = {"User-Agent": "NewsIntelEngine/0.1 (personal research)"}

# F-02 FIX: common-word tickers matched ONLY with $ prefix. Expanded blocklist.
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

seen_u = set(); RSS = []; GH = []
for s in RAW:
    u = s.get("Url", "").replace("http://", "https://").rstrip("/")
    if not u or u in seen_u: continue
    seen_u.add(u)
    (GH if "github.com/" in u else RSS).append({**s, "_url": u})

# --- Persistent state ---
con = sqlite3.connect(os.path.join(DATA, "seen.db"))
con.execute("CREATE TABLE IF NOT EXISTS seen(url TEXT PRIMARY KEY, ts REAL)")
# F-05 FIX: title-based dedup table
con.execute("CREATE TABLE IF NOT EXISTS seen_titles(title_hash TEXT PRIMARY KEY, url TEXT, ts REAL)")

def is_seen(u): return con.execute("SELECT 1 FROM seen WHERE url=?", (u,)).fetchone()
def mark_seen(us):
    con.executemany("INSERT OR IGNORE INTO seen(url,ts) VALUES (?,?)", [(u, time.time()) for u in us]); con.commit()

# F-05 FIX: normalized-title helpers
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
    score = 0; hits = []
    if any(a in i["source_name"].lower() for a in ALWAYS_ANALYZE):
        score += 5; hits.append("Priority Source")
    for sym in set(c.upper() for c in CASHTAG.findall(text)):
        if sym in T_BY_SYM: score += 3; hits.append(sym)
    for t in SYMS:
        if re.search(rf"\b{re.escape(t)}\b", text, re.I): score += 2; hits.append(t)
    for name, d in NAMES:
        if name in low: score += 3; hits.append(d["t"])
    kws = find_matches(text)
    for e in kws: score += PRIO_SCORE.get(e.get("prio", "Medium"), 2)
    i["keyword_ids"] = [e["id"] for e in kws]
    i["keyword_tags"] = sorted({t for e in kws for t in e.get("tags", [])})
    labels = []
    for h in dict.fromkeys(hits):
        d = T_BY_SYM.get(h)
        labels.append(f"{h} ({d['c']} · {d['s']})" if d else h)
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

# F-04 FIX: parse ISO timestamps to epoch
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

def alert(i, a):
    if a.get("importance") not in ("High", "Critical") or not os.environ.get("DISCORD_WEBHOOK"): return
    requests.post(os.environ["DISCORD_WEBHOOK"], json={"embeds": [{
        "title": i["title"][:200], "url": i["url"], "description": (a.get("summary") or "")[:900],
        "fields": [
            {"name": "Source", "value": i["source_name"], "inline": True},
            {"name": "Importance", "value": a.get("importance", ""), "inline": True},
            {"name": "Sentiment", "value": a.get("sentiment", ""), "inline": True},
            {"name": "Tickers", "value": ", ".join(a.get("tickers") or []) or "-", "inline": True},
            {"name": "Triggered By", "value": ", ".join(i.get("matched_categories", []))[:500], "inline": False}]}]})

async def main():
    # D-01 FIX: fail fast if secrets missing (skip check in DRY_RUN)
    if not DRY_RUN and not os.environ.get("QWEN_API_KEY"):
        raise SystemExit("FATAL: QWEN_API_KEY secret is not set. Add it in Settings > Secrets and variables > Actions.")

    sem, sem_rd = asyncio.Semaphore(20), asyncio.Semaphore(4)
    since = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_H)
    async with aiohttp.ClientSession(headers=UA) as s:
        batches = await asyncio.gather(
            *[fetch_rss(s, x, sem) for x in RSS],
            *[fetch_reddit(s, x, sem_rd) for x in REDDIT],
            *[fetch_github(s, x["_url"].split("github.com/")[1], sem, since.isoformat()) for x in GH])
    items = [i for b in batches if b for i in b]
    # F-05 FIX: also filter by title dedup
    new = [i for i in items if i["ts"] >= since.timestamp() and i["url"] and not is_seen(i["url"]) and not is_title_seen(i)]

    scored = []; filtered_out = []
    for i in new:
        sc, labels = score_item(i)
        if sc > 0:
            i["matched_categories"] = labels; i["score"] = sc; i["cats"] = ", ".join(labels); scored.append(i)
        else:
            filtered_out.append(i)

    # F-06 FIX: mark filtered-out items seen now; matched items only after success
    if filtered_out:
        mark_seen([i["url"] for i in filtered_out]); mark_title_seen(filtered_out)

    scored.sort(key=lambda x: -x["score"])
    report = {"run": datetime.now(timezone.utc).isoformat(), "dry_run": DRY_RUN,
              "fetched": len(items), "new": len(new), "matched": len(scored),
              "analyzed": [], "would_analyze": []}

    processed_urls = []; processed_items = []
    for idx, i in enumerate(scored):
        if idx >= MAX_ANALYZE:
            processed_urls.append(i["url"]); processed_items.append(i); continue
        if i["source_type"] == "rss": i["text"] = full_text(i["url"], i["text"])
        if DRY_RUN:
            report["would_analyze"].append({"url": i["url"], "title": i["title"], "source": i["source_name"],
                                            "score": i["score"], "triggers": i["matched_categories"]})
            processed_urls.append(i["url"]); processed_items.append(i); continue
        a = analyze(i)
        if a:
            report["analyzed"].append({"url": i["url"], "title": i["title"], "source": i["source_name"],
                                       "score": i["score"], "triggers": i["matched_categories"], "analysis": a})
            alert(i, a)
            processed_urls.append(i["url"]); processed_items.append(i)
        # F-06 FIX: failed analysis NOT marked seen -> retries next run
        await asyncio.sleep(1)  # F-10 FIX

    if processed_urls:
        mark_seen(processed_urls); mark_title_seen(processed_items)

    with open(os.path.join(REPORTS, "run.json"), "w", encoding="utf-8") as f: json.dump(report, f, indent=2)
    extra = f" | WOULD_ANALYZE {len(report['would_analyze'])}" if DRY_RUN else ""
    mode = " [DRY RUN]" if DRY_RUN else ""
    print(f"FETCHED {report['fetched']} | NEW {report['new']} | MATCHED {report['matched']} | ANALYZED {len(report['analyzed'])}{extra}{mode}")

if __name__ == "__main__":
    asyncio.run(main())
