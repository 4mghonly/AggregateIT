import os, re, json, time, sqlite3, asyncio, calendar, hashlib, sys
import feedparser, aiohttp, requests, trafilatura
from datetime import datetime, timezone, timedelta
from storage import SQLiteStore, DATA

BASE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(BASE, "reports")
os.makedirs(DATA, exist_ok=True); os.makedirs(REPORTS, exist_ok=True)

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
LOOKBACK_H = int(os.environ.get("LOOKBACK_HOURS", "6"))
MAX_PER_SOURCE = 5
MAX_ANALYZE = 25
ALWAYS_ANALYZE = ["federal reserve", "european central bank", "cisa"]
PRIO_LIMIT = {"Very High": 10, "High": 5, "Medium": 3}
UA = {"User-Agent": "NewsIntelEngine/0.2 (personal research)"}

CASHTAG_ONLY = {
    "ALL","ARE","CAT","KEY","LOW","FIX","TAP","MAS","LIN","GEN","HAL","DOW","MET",
    "ION","ARM","USB","GPS","KEYS","FAST","FLEX","LITE","DASH","FANG","COIN",
    "SNOW","JOBS","CARS","BEER","DECK",
    "HAS","APP","TECH","NOW","COST","BALL","WELL","POOL","ICE","AMP","DOC","FOX","PARA"
}

# --- system health counters (F-09: failures are visible, never silent) ---
HEALTH = {"rss_ok":0,"rss_fail":0,"reddit_ok":0,"reddit_fail":0,"github_ok":0,"github_fail":0,
          "qwen_ok":0,"qwen_fail":0,"qwen_invalid":0,"discord_ok":0,"discord_fail":0,"discord_skipped":0}

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

store = SQLiteStore()

def normalize_title(title):
    t = re.sub(r'[^\w\s]', '', (title or "").lower())
    return re.sub(r'\s+', ' ', t).strip()

def title_hash(title):
    return hashlib.md5(normalize_title(title).encode()).hexdigest()

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
    HEALTH["rss_ok" if out else "rss_fail"] += 1
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
    HEALTH["reddit_ok" if out else "reddit_fail"] += 1
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
    HEALTH["github_ok" if out else "github_fail"] += 1
    return out

def full_text(url, fallback):
    try:
        raw = trafilatura.fetch_url(url)
        txt = trafilatura.extract(raw, include_comments=False)
        if txt and len(txt) > 400: return txt[:4000]
    except Exception: pass
    return fallback[:4000]

# ================= QWEN INTELLIGENCE CONTRACT =================
PROMPT_T = """You are a disciplined intelligence analyst. Strict tradecraft rules:
- FACTS must be directly supported by the source text. Never present inference as fact.
- ASSESSMENT is your interpretation, always separated from facts.
- CONFIDENCE 0-100 must reflect evidence quality; single-source claims stay at or below 60.
- If information is missing, record it in "gaps". Never invent it.
- Only include tickers that literally appear in the text.

Output ONLY one valid JSON object with exactly these keys:
{{
  "event": "one-sentence description of the event",
  "event_type": "earnings|regulation|geopolitical|market_move|security|macro|other",
  "facts": ["statement directly supported by the text"],
  "assessment": "analytical interpretation, clearly opinion not fact",
  "importance": "Low|Medium|High|Critical",
  "confidence": 0,
  "sentiment": "bullish|bearish|neutral|na",
  "entities": ["companies, people, organizations, countries"],
  "tickers": ["VALID symbols only"],
  "evidence": ["short verbatim quotes supporting key claims"],
  "corroboration": "none|single-source|multi-source",
  "source_reliability": "High|Medium|Low",
  "gaps": ["what is missing or unconfirmed"]
}}

TRIGGER CONTEXT: This item was flagged because it relates to: {cats}
SOURCE: {source_name} ({category})
TITLE: {title}
TEXT:
{text}"""

ENUM_IMP = {"Low","Medium","High","Critical"}
ENUM_SENT = {"bullish","bearish","neutral","na"}
ENUM_REL = {"High","Medium","Low"}
TICK_RE = re.compile(r"^[A-Z.\-]{1,6}$")

def validate_analysis(obj):
    """F-08: valid JSON is NOT automatically valid intelligence. Returns (ok, obj, errors)."""
    errs = []
    if not isinstance(obj, dict): return False, None, ["response is not a JSON object"]
    for k in ("event","assessment","event_type","corroboration","source_reliability"):
        if not isinstance(obj.get(k), str) or not obj.get(k).strip(): errs.append(f"missing/invalid '{k}'")
    for k in ("facts","entities","tickers","evidence","gaps"):
        v = obj.get(k)
        if not isinstance(v, list): errs.append(f"'{k}' must be a list")
        elif not all(isinstance(x, str) for x in v): errs.append(f"'{k}' items must be strings")
    if obj.get("importance") not in ENUM_IMP: errs.append("importance not in Low|Medium|High|Critical")
    if obj.get("sentiment") not in ENUM_SENT: errs.append("sentiment not in enum")
    if obj.get("source_reliability") not in ENUM_REL: errs.append("source_reliability not in enum")
    c = obj.get("confidence")
    if not isinstance(c, (int, float)) or not (0 <= c <= 100): errs.append("confidence must be 0-100")
    if errs: return False, obj, errs
    obj["tickers"] = [t.upper().strip() for t in obj["tickers"] if TICK_RE.match(t.upper().strip())][:10]
    if obj.get("corroboration") == "none" and obj["confidence"] > 60:
        obj["confidence"] = 60  # single-source ceiling: never present inference as confirmed fact
    return True, obj, []

def _qwen_call(messages):
    base = os.environ.get("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1").rstrip("/")
    r = requests.post(base + "/chat/completions",
        headers={"Authorization": "Bearer " + os.environ["QWEN_API_KEY"]},
        json={"model": os.environ.get("QWEN_MODEL", "qwen-plus"), "temperature": 0.2, "messages": messages},
        timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def analyze(i):
    """F-07: bounded repair-retry + strict validation. Returns (analysis|None, error|None)."""
    prompt = PROMPT_T.format(**i)
    for attempt in (1, 2):
        try:
            content = _qwen_call([{"role": "user", "content": prompt}])
            m = re.search(r"\{[\s\S]*\}", content)
            if not m: raise ValueError("no JSON object in response")
            obj = json.loads(m.group(0))
            ok, cleaned, errs = validate_analysis(obj)
            if ok:
                HEALTH["qwen_ok"] += 1
                return cleaned, None
            if attempt == 1:
                HEALTH["qwen_invalid"] += 1
                prompt += "\n\nYour previous response was INVALID (" + "; ".join(errs) + "). Return ONLY the corrected JSON object."
                continue
            HEALTH["qwen_invalid"] += 1
            return None, "schema invalid: " + "; ".join(errs)
        except requests.exceptions.Timeout:
            if attempt == 1: continue
            HEALTH["qwen_fail"] += 1
            return None, "timeout"
        except Exception as e:
            if attempt == 1: time.sleep(2); continue
            HEALTH["qwen_fail"] += 1
            return None, f"{type(e).__name__}: {str(e)[:120]}"
    return None, "unknown"

# ================= DISCORD DIGEST =================
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
    desc = _truncate(f"**{a.get('event','')}**\n{a.get('assessment','')}", 900)
    fields = [
        {"name": "Sentiment", "value": SENT_EMOJI.get(sent, sent), "inline": True},
        {"name": "Importance", "value": f"{IMP_EMOJI.get(imp, '')} {imp}", "inline": True},
        {"name": "Confidence", "value": f"{a.get('confidence', '?')}%", "inline": True},
        {"name": "Tickers", "value": _truncate(", ".join(a.get("tickers") or []) or "-", 200), "inline": True},
    ]
    if a.get("event_type"):
        fields.append({"name": "Event Type", "value": _truncate(str(a["event_type"]), 150), "inline": True})
    fields.append({"name": "Triggered By", "value": _truncate(", ".join(i.get("matched_categories", [])) or "-", 400), "inline": False})
    return {"title": _truncate(f"{tag} {i['title']}", 250), "url": i["url"], "description": desc,
            "color": IMP_COLOR.get(imp, 0x95A5A6), "fields": fields,
            "footer": {"text": f"{i['source_name']} · score {i.get('score', 0)} · rel. {a.get('source_reliability', '?')}"}}

def send_digest(digest_items, report):
    wh = os.environ.get("DISCORD_WEBHOOK")
    if not wh or not digest_items:
        HEALTH["discord_skipped"] += 1
        return
    news = [x for x in digest_items if x["item"]["source_type"] != "reddit"]
    social = [x for x in digest_items if x["item"]["source_type"] == "reddit"]
    rolls = {"bullish": 0, "bearish": 0, "neutral": 0, "na": 0}
    for x in digest_items:
        s = (x["analysis"].get("sentiment") or "na").lower()
        rolls[s if s in rolls else "na"] += 1
    header = {
        "title": "🧠 AggregateIT Intelligence Digest",
        "description": f"**{report['new']}** new items scanned → **{report['matched']}** matched → **{len(digest_items)}** analyzed by Qwen",
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
        HEALTH["discord_ok"] += len(digest_items)
    except Exception as e:
        HEALTH["discord_fail"] += 1
        print("Discord digest err:", type(e).__name__, str(e)[:120])

def build_health(report, store_stats):
    degraded = []
    if HEALTH["rss_fail"]: degraded.append(f"{HEALTH['rss_fail']} RSS feeds failed")
    if HEALTH["reddit_fail"]: degraded.append(f"{HEALTH['reddit_fail']} subreddits failed")
    if HEALTH["github_fail"]: degraded.append(f"{HEALTH['github_fail']} GitHub repos failed")
    if HEALTH["qwen_fail"]: degraded.append(f"{HEALTH['qwen_fail']} Qwen API failures")
    if HEALTH["qwen_invalid"]: degraded.append(f"{HEALTH['qwen_invalid']} Qwen outputs rejected by schema")
    if HEALTH["discord_fail"]: degraded.append("Discord delivery failed")
    if not os.path.exists(os.path.join(DATA, "movers.json")): degraded.append("TradingView movers missing (run TV refresh)")
    if store_stats.get("fresh_init"): degraded.append("state DB freshly initialized (previous state may be lost)")
    hard_fail = (not DRY_RUN) and HEALTH["qwen_fail"] > HEALTH["qwen_ok"]
    overall = "RED" if hard_fail else ("YELLOW" if degraded else "GREEN")
    return {"run": report["run"], "overall": overall, "dry_run": DRY_RUN,
            "degraded": degraded, "counters": dict(HEALTH), "store": store_stats}

# ================= MAIN =================
async def main():
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

    new = []
    for i in items:
        if i["ts"] < since.timestamp() or not i["url"]: continue
        if not store.url_active(i["url"]): continue
        if not store.title_active(title_hash(i.get("title", ""))): continue
        new.append(i)

    scored = []
    for i in new:
        sc, labels = score_item(i)
        i["thash"] = title_hash(i.get("title", ""))
        if sc > 0:
            i["matched_categories"] = labels; i["score"] = sc; i["cats"] = ", ".join(labels)
            scored.append(i)
            if not DRY_RUN: store.register(i["url"], i["thash"], "discovered", sc)
        else:
            if not DRY_RUN: store.register(i["url"], i["thash"], "filtered", 0)  # terminal: no retry value

    scored.sort(key=lambda x: -x["score"])
    report = {"run": datetime.now(timezone.utc).isoformat(), "dry_run": DRY_RUN,
              "fetched": len(items), "new": len(new), "matched": len(scored),
              "analyzed": [], "would_analyze": [], "quarantined": []}

    digest_items = []
    for idx, i in enumerate(scored):
        if idx >= MAX_ANALYZE:
            if not DRY_RUN: store.succeed(i["url"], i["thash"], "capped")  # considered, cost-capped
            continue
        if i["source_type"] == "rss": i["text"] = full_text(i["url"], i["text"])
        if DRY_RUN:
            report["would_analyze"].append({"url": i["url"], "title": i["title"], "source": i["source_name"],
                                            "score": i["score"], "triggers": i["matched_categories"]})
            continue
        a, err = analyze(i)
        if a:
            report["analyzed"].append({"url": i["url"], "title": i["title"], "source": i["source_name"],
                                       "score": i["score"], "triggers": i["matched_categories"], "analysis": a})
            digest_items.append({"item": i, "analysis": a})
            store.succeed(i["url"], i["thash"], "analyzed", json.dumps(a))  # terminal AFTER success (F-06)
        else:
            report["quarantined"].append({"url": i["url"], "title": i["title"], "error": err})
            store.fail(i["url"])  # retriable next run
            print("QUARANTINED:", i["url"], "|", err)
        await asyncio.sleep(1)

    send_digest(digest_items, report)

    store.record_run(report["fetched"], report["new"], report["matched"], len(report["analyzed"]))
    store_stats = store.stats()
    health = build_health(report, store_stats)
    with open(os.path.join(REPORTS, "run.json"), "w", encoding="utf-8") as f: json.dump(report, f, indent=2)
    with open(os.path.join(REPORTS, "health.json"), "w", encoding="utf-8") as f: json.dump(health, f, indent=2)

    extra = f" | WOULD_ANALYZE {len(report['would_analyze'])}" if DRY_RUN else ""
    quar = f" | QUARANTINED {len(report['quarantined'])}" if report["quarantined"] else ""
    mode = " [DRY RUN]" if DRY_RUN else ""
    print(f"FETCHED {report['fetched']} | NEW {report['new']} | MATCHED {report['matched']} | ANALYZED {len(report['analyzed'])}{extra}{quar}{mode}")
    note = (" — " + "; ".join(health["degraded"])) if health["degraded"] else ""
    print(f"HEALTH: {health['overall']}{note}")

if __name__ == "__main__":
    asyncio.run(main())
