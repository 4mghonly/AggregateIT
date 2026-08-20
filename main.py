import os, re, json, time, sqlite3, asyncio, calendar, hashlib, sys
import feedparser, aiohttp, requests, trafilatura
from datetime import datetime, timezone, timedelta
from storage import SQLiteStore, DATA
from market import load_market_pulse, build_pulse_embed

BASE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(BASE, "reports")
os.makedirs(DATA, exist_ok=True); os.makedirs(REPORTS, exist_ok=True)

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
LOOKBACK_H = int(os.environ.get("LOOKBACK_HOURS", "6"))
MAX_PER_SOURCE = 5
MAX_ANALYZE = 25      # max articles admitted to the front page per run
MAX_EVENTS = 10       # max event clusters analyzed per run (token cap)
FRONT_PAGE_FLOOR = 5  # L4: minimum score to justify Qwen token spend
ALWAYS_ANALYZE = ["federal reserve", "european central bank", "cisa"]
PRIO_LIMIT = {"Very High": 10, "High": 5, "Medium": 3}
UA = {"User-Agent": "NewsIntelEngine/0.4 (personal research)"}

CASHTAG_ONLY = {
    "ALL","ARE","CAT","KEY","LOW","FIX","TAP","MAS","LIN","GEN","HAL","DOW","MET",
    "ION","ARM","USB","GPS","KEYS","FAST","FLEX","LITE","DASH","FANG","COIN",
    "SNOW","JOBS","CARS","BEER","DECK",
    "HAS","APP","TECH","NOW","COST","BALL","WELL","POOL","ICE","AMP","DOC","FOX","PARA"
}

HEALTH = {"rss_ok":0,"rss_fail":0,"reddit_ok":0,"reddit_fail":0,"github_ok":0,"github_fail":0,
          "qwen_ok":0,"qwen_fail":0,"qwen_invalid":0,"discord_ok":0,"discord_fail":0,"discord_skipped":0,
          "tv_movers_loaded":0,"tv_universe_loaded":0}

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

def load_market_context():
    movers, uni_tickers, uni_names = {}, set(), {}
    try:
        with open(os.path.join(DATA, "movers.json"), encoding="utf-8") as f:
            for t, meta in json.load(f).get("movers", {}).items(): movers[t.upper()] = meta
            HEALTH["tv_movers_loaded"] = len(movers)
    except Exception: pass
    try:
        with open(os.path.join(DATA, "tv_universe.json"), encoding="utf-8") as f:
            for row in json.load(f).get("rows", []):
                t = row.get("t", "").upper(); c = row.get("c", "")
                if t: uni_tickers.add(t)
                if c and len(c) >= 6: uni_names[c.lower()] = t
            HEALTH["tv_universe_loaded"] = len(uni_tickers)
    except Exception: pass
    return movers, uni_tickers, uni_names

MOVERS, TV_TICKERS, TV_NAMES = load_market_context()

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
        if sym in T_BY_SYM:
            score += 3; hits.append(sym)
            if sym in MOVERS: score += 4; hits.append(f"{sym} (Mover)")
    for t in SYMS:
        if re.search(rf"\b{re.escape(t)}\b", text, re.I): score += 2; hits.append(t)
    for name, d in NAMES:
        if name in low: score += 3; hits.append(d["t"])
    for sym in set(c.upper() for c in CASHTAG.findall(text)):
        if sym in TV_TICKERS and sym not in T_BY_SYM:
            score += 2; hits.append(f"{sym} (TV)")
            if sym in MOVERS: score += 4; hits.append(f"{sym} (Mover)")
    for name, t in TV_NAMES.items():
        if name in low and t not in T_BY_SYM:
            score += 2; hits.append(f"{t} (TV)")
            if t in MOVERS: score += 4; hits.append(f"{t} (Mover)")
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
    try: return datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
    except Exception: return None

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
                        ts = parse_iso_ts(it.get("published_at") or it.get("created_at") or it.get("commit", {}).get("committer", {}).get("date")) or time.time()
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

# ================= EVENT CLUSTERING (Spec #8) =================
STOPWORDS = {"the","a","an","of","in","on","for","to","and","or","is","are","was","were",
             "as","at","by","with","from","over","under","after","before","amid","its","it",
             "that","this","these","those","be","been","has","have","had","will","would","can",
             "could","says","said","say","new","vs","versus","per","their","his","her","your",
             "our","into","about","up","out","off","more","less","than","then","so","not","no",
             "but","if","how","why","what","when","where","who","which","all","any","some","one"}

def title_tokens(title):
    return {t for t in re.findall(r"[a-z0-9]{2,}", normalize_title(title)) if t not in STOPWORDS}

def jaccard(a, b):
    if not a or not b: return 0.0
    return len(a & b) / len(a | b)

def containment(new_tokens, stored_tokens):
    if not new_tokens: return 0.0
    return len(new_tokens & stored_tokens) / len(new_tokens)

def primary_entity(i):
    for label in i.get("matched_categories", []):
        t = label.split(" ")[0]
        if 2 <= len(t) <= 6 and t.replace(".", "").replace("-", "").isalpha():
            return t.upper()
    kws = i.get("keyword_ids", [])
    if kws: return kws[0]
    return "GEN"

def cluster_events(items):
    clusters = []
    for i in sorted(items, key=lambda x: -x.get("score", 0)):
        toks = title_tokens(i.get("title", ""))
        ent = primary_entity(i)
        placed = False
        for c in clusters:
            if c["entity"] == ent and jaccard(toks, c["tokens"]) >= 0.35:
                c["items"].append(i); c["tokens"] |= toks; placed = True; break
        if not placed:
            clusters.append({"entity": ent, "tokens": toks, "items": [i], "event_id": None})
    for c in clusters:
        seed = c["entity"] + "|" + " ".join(sorted(title_tokens(c["items"][0]["title"])))
        c["event_id"] = hashlib.md5(seed.encode()).hexdigest()[:12]
        c["source_names"] = sorted({it["source_name"] for it in c["items"]})
        c["independent_sources"] = len(c["source_names"])
    return clusters

def resolve_prior_event(c, store, hours=72):
    for ev in store.recent_events(c["entity"], hours=hours):
        try: stored = set(json.loads(ev.get("tokens_json") or "[]"))
        except Exception: continue
        if containment(c["tokens"], stored) >= 0.5: return ev
    return None

# ================= QWEN EVENT-LEVEL CONTRACT =================
EVENT_PROMPT_T = """You are a disciplined intelligence analyst performing EVENT-LEVEL analysis.
You receive multiple reports that appear to cover the SAME underlying event. Strict tradecraft rules:
- FACTS must be directly supported by at least one report. Never present inference as fact.
- ASSESSMENT is your interpretation, always separated from facts.
- Independent DISTINCT sources strengthen corroboration; multiple articles from the same source do not.
- CONFIDENCE 0-100 must reflect evidence quality and corroboration.
- If information is missing, record it in "gaps". Never invent it.
- Only include tickers that literally appear in the reports.

Output ONLY one valid JSON object with exactly these keys:
{{
  "event": "one-sentence description of the underlying event",
  "event_type": "earnings|regulation|geopolitical|market_move|security|macro|other",
  "facts": ["statements directly supported by the reports"],
  "assessment": "analytical interpretation, clearly opinion not fact",
  "what_changed": "what is NEW compared to prior coverage (or 'New event - no prior coverage')",
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

TRIGGER CONTEXT: flagged because it relates to: {cats}
PRIOR EVENT STATE:
{prior_state}

REPORTS ({n_sources} distinct source(s)):
{sources_block}"""

ENUM_IMP = {"Low","Medium","High","Critical"}
ENUM_SENT = {"bullish","bearish","neutral","na"}
ENUM_REL = {"High","Medium","Low"}
TICK_RE = re.compile(r"^[A-Z.\-]{1,6}$")

def validate_analysis(obj):
    errs = []
    if not isinstance(obj, dict): return False, None, ["response is not a JSON object"]
    for k in ("event","assessment","event_type","corroboration","source_reliability","what_changed"):
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
    if obj.get("corroboration") == "none" and obj["confidence"] > 60: obj["confidence"] = 60
    return True, obj, []

def _qwen_call(messages):
    base = os.environ.get("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1").rstrip("/")
    r = requests.post(base + "/chat/completions",
        headers={"Authorization": "Bearer " + os.environ["QWEN_API_KEY"]},
        json={"model": os.environ.get("QWEN_MODEL", "qwen-plus"), "temperature": 0.2, "messages": messages}, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def build_sources_block(c):
    lines = []
    for idx, it in enumerate(c["items"][:5], 1):
        ts = datetime.fromtimestamp(it["ts"], timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines.append(f"[{idx}] SOURCE: {it['source_name']} | PUBLISHED: {ts}\nTITLE: {it['title']}\nTEXT: {it['text'][:1200]}")
    return "\n\n".join(lines)

def analyze_event(c, prior):
    if prior:
        prior_state = (f"Event {prior['event_id']} tracked since "
                       f"{datetime.fromtimestamp(prior['first_seen'], timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | "
                       f"previous title: \"{prior['title']}\" | previous assessment: {(prior['assessment'] or '')[:300]} | "
                       f"previous confidence: {prior['confidence']} | sources so far: {prior['source_count']}")
    else:
        prior_state = "NEW EVENT — no prior coverage."
    prompt = EVENT_PROMPT_T.format(cats=c["items"][0].get("cats", ""),
                                   prior_state=prior_state,
                                   n_sources=c["independent_sources"],
                                   sources_block=build_sources_block(c))
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
            HEALTH["qwen_fail"] += 1; return None, "timeout"
        except Exception as e:
            if attempt == 1: time.sleep(2); continue
            HEALTH["qwen_fail"] += 1; return None, f"{type(e).__name__}: {str(e)[:120]}"
    return None, "unknown"

# ================= DISCORD DIGEST =================
SENT_EMOJI = {"bullish": "🟢 Bullish", "bearish": "🔴 Bearish", "neutral": "⚪ Neutral", "na": "➖ N/A"}
IMP_EMOJI = {"Critical": "🚨", "High": "🔥", "Medium": "📌", "Low": "ℹ️"}
IMP_COLOR = {"Critical": 0xE74C3C, "High": 0xE67E22, "Medium": 0xF1C40F, "Low": 0x95A5A6}

def _truncate(s, n):
    s = (s or "").strip()
    return s if len(s) <= n else s[:n-1] + "…"

def build_event_embed(c, a, prior):
    imp = a.get("importance", "Low")
    sent = (a.get("sentiment") or "na").lower()
    all_reddit = all(it["source_type"] == "reddit" for it in c["items"])
    tag = "💬" if all_reddit else "📰"
    desc = f"**{a.get('event','')}**\n{a.get('assessment','')}"
    if a.get("what_changed"): desc += f"\n🔄 *What changed: {a['what_changed']}*"
    fields = [
        {"name": "Sentiment", "value": SENT_EMOJI.get(sent, sent), "inline": True},
        {"name": "Importance", "value": f"{IMP_EMOJI.get(imp, '')} {imp}", "inline": True},
        {"name": "Confidence", "value": f"{a.get('confidence', '?')}%", "inline": True},
        {"name": "Tickers", "value": _truncate(", ".join(a.get("tickers") or []) or "-", 200), "inline": True},
    ]
    if a.get("event_type"):
        fields.append({"name": "Event Type", "value": _truncate(str(a["event_type"]), 150), "inline": True})
    fields.append({"name": f"Sources ({c['independent_sources']} distinct)",
                   "value": _truncate(", ".join(c["source_names"]), 300), "inline": False})
    fields.append({"name": "Triggered By",
                   "value": _truncate(", ".join(c["items"][0].get("matched_categories", [])) or "-", 400), "inline": False})
    footer = f"event {c['event_id']} · score {c['items'][0].get('score', 0)}"
    if prior: footer += f" · updated (prev conf {prior.get('confidence', '?')}%)"
    return {"title": _truncate(f"{tag} {a.get('event') or c['items'][0]['title']}", 250),
            "url": c["items"][0]["url"], "description": _truncate(desc, 900),
            "color": IMP_COLOR.get(imp, 0x95A5A6), "fields": fields,
            "footer": {"text": footer}}

def _post_discord(wh, payload):
    r = requests.post(wh, json=payload, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"Discord HTTP {r.status_code}: {r.text[:120]}")

def send_market_pulse():
    """Post the pulse once per fresh snapshot; never present zeros as live data."""
    wh = os.environ.get("DISCORD_WEBHOOK")
    pulse = load_market_pulse()
    if not wh or not pulse: return
    marker = os.path.join(DATA, ".last_pulse")
    last = 0.0
    try:
        with open(marker) as f: last = float(f.read().strip() or 0)
    except Exception: pass
    if pulse.get("updated", 0) <= last: return
    try:
        _post_discord(wh, {"embeds": [build_pulse_embed(pulse)]})
        with open(marker, "w") as f: f.write(str(pulse["updated"]))
        HEALTH["discord_ok"] += 1
    except Exception as e:
        HEALTH["discord_fail"] += 1; print("Discord pulse err:", type(e).__name__, str(e)[:200])

def send_digest(digest_items, report):
    wh = os.environ.get("DISCORD_WEBHOOK")
    if not digest_items:
        HEALTH["discord_skipped"] += 1; return
    if not wh:
        HEALTH["discord_fail"] += 1
        print("DISCORD: webhook secret missing - digest NOT delivered"); return
    news, social = [], []
    for x in digest_items:
        (social if all(it["source_type"] == "reddit" for it in x["cluster"]["items"]) else news).append(x)
    rolls = {"bullish": 0, "bearish": 0, "neutral": 0, "na": 0}
    for x in digest_items:
        s = (x["analysis"].get("sentiment") or "na").lower()
        rolls[s if s in rolls else "na"] += 1
    es = report.get("events_summary", {})
    header = {
        "title": "🧠 AggregateIT Intelligence Digest",
        "description": f"**{report['new']}** new items → **{report['matched']}** matched → **{len(digest_items)}** events on the Front Page",
        "color": 0x5865F2,
        "fields": [
            {"name": "🆕 New events", "value": str(es.get("new", 0)), "inline": True},
            {"name": "🔄 Updated", "value": str(es.get("updated", 0)), "inline": True},
            {"name": "📊 Sentiment", "value": f"🟢 {rolls['bullish']} · 🔴 {rolls['bearish']} · ⚪ {rolls['neutral']}", "inline": True},
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        news_embeds = [build_event_embed(x["cluster"], x["analysis"], x["prior"]) for x in news]
        social_embeds = [build_event_embed(x["cluster"], x["analysis"], x["prior"]) for x in social]
        _post_discord(wh, {"content": "**📰 NEWS SOURCES**", "embeds": [header] + news_embeds[:3]})
        for k in range(3, len(news_embeds), 4): _post_discord(wh, {"embeds": news_embeds[k:k+4]})
        if social_embeds:
            _post_discord(wh, {"content": "**💬 SOCIAL NETWORKS**", "embeds": social_embeds[:4]})
            for k in range(4, len(social_embeds), 4): _post_discord(wh, {"embeds": social_embeds[k:k+4]})
        HEALTH["discord_ok"] += len(digest_items)
    except Exception as e:
        HEALTH["discord_fail"] += 1; print("Discord err:", type(e).__name__, str(e)[:200])

def build_health(report, store_stats):
    degraded = []
    if HEALTH["rss_fail"]: degraded.append(f"{HEALTH['rss_fail']} RSS feeds failed")
    if HEALTH["reddit_fail"]: degraded.append(f"{HEALTH['reddit_fail']} subreddits failed")
    if HEALTH["github_fail"]: degraded.append(f"{HEALTH['github_fail']} GitHub repos failed")
    if HEALTH["qwen_fail"]: degraded.append(f"{HEALTH['qwen_fail']} Qwen API failures")
    if HEALTH["qwen_invalid"]: degraded.append(f"{HEALTH['qwen_invalid']} Qwen outputs rejected")
    if HEALTH["discord_fail"]: degraded.append("Discord delivery failed")
    if HEALTH["tv_movers_loaded"] == 0: degraded.append("TradingView movers missing (run TV refresh)")
    if store_stats.get("fresh_init"): degraded.append("state DB freshly initialized")
    hard_fail = (not DRY_RUN) and HEALTH["qwen_fail"] > HEALTH["qwen_ok"]
    overall = "RED" if hard_fail else ("YELLOW" if degraded else "GREEN")
    return {"run": report["run"], "overall": overall, "dry_run": DRY_RUN,
            "degraded": degraded, "counters": dict(HEALTH), "store": store_stats}

# ================= MAIN =================
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
            if not DRY_RUN: store.register(i["url"], i["thash"], "filtered", 0)

    ticker_counts = {}
    for i in scored:
        for label in i.get("matched_categories", []):
            t = label.split(" ")[0]
            if 2 <= len(t) <= 6 and t.replace(".", "").replace("-", "").isalpha():
                ticker_counts[t.upper()] = ticker_counts.get(t.upper(), 0) + 1
    for i in scored:
        for label in i.get("matched_categories", []):
            t = label.split(" ")[0].upper()
            if ticker_counts.get(t, 0) >= 2:
                i["score"] += 2
                if "Confluence" not in i["matched_categories"]: i["matched_categories"].append("Confluence")
                break

    scored.sort(key=lambda x: -x["score"])
    report = {"run": datetime.now(timezone.utc).isoformat(), "dry_run": DRY_RUN,
              "fetched": len(items), "new": len(new), "matched": len(scored),
              "events": [], "events_summary": {"clusters": 0, "new": 0, "updated": 0},
              "wire": [], "quarantined": []}

    front_page = []
    for i in scored:
        if i["score"] < FRONT_PAGE_FLOOR:
            report["wire"].append({"url": i["url"], "title": i["title"], "source": i["source_name"],
                                   "score": i["score"], "triggers": i["matched_categories"]})
            if not DRY_RUN: store.succeed(i["url"], i["thash"], "capped")
            continue
        if len(front_page) >= MAX_ANALYZE:
            if not DRY_RUN: store.succeed(i["url"], i["thash"], "capped")
            continue
        if i["source_type"] == "rss": i["text"] = full_text(i["url"], i["text"])
        front_page.append(i)

    clusters = cluster_events(front_page)
    report["events_summary"]["clusters"] = len(clusters)

    for c in clusters[MAX_EVENTS:]:
        if not DRY_RUN:
            for it in c["items"]: store.succeed(it["url"], it["thash"], "capped")

    digest_items = []
    for c in clusters[:MAX_EVENTS]:
        prior = resolve_prior_event(c, store)
        if DRY_RUN:
            report["events"].append({"event_id": c["event_id"], "entity": c["entity"], "preview": True,
                                     "new_event": prior is None,
                                     "independent_sources": c["independent_sources"],
                                     "triggers": c["items"][0].get("matched_categories", []),
                                     "sources": [{"name": it["source_name"], "url": it["url"], "title": it["title"]} for it in c["items"]]})
            continue
        a, err = analyze_event(c, prior)
        if a:
            now = time.time()
            if prior:
                c["event_id"] = prior["event_id"]
                try: old_tokens = set(json.loads(prior.get("tokens_json") or "[]"))
                except Exception: old_tokens = set()
                c["tokens"] = set(sorted(c["tokens"] | old_tokens)[:60])
                report["events_summary"]["updated"] += 1
            else:
                report["events_summary"]["new"] += 1
            ev = {"event_id": c["event_id"], "entity": c["entity"],
                  "tokens_json": json.dumps(sorted(c["tokens"])),
                  "title": a["event"], "event_type": a["event_type"], "status": "active",
                  "severity": a["importance"], "confidence": int(a["confidence"]),
                  "source_count": (prior["source_count"] if prior else 0) + c["independent_sources"],
                  "assessment": a["assessment"], "what_changed": a["what_changed"],
                  "sentiment": a.get("sentiment", "na"),
                  "triggers_json": json.dumps(c["items"][0].get("matched_categories", [])),
                  "sources_json": json.dumps([{"name": it["source_name"], "url": it["url"], "title": it["title"]} for it in c["items"]]),
                  "score": c["items"][0].get("score", 0),
                  "urls_json": json.dumps([it["url"] for it in c["items"]]),
                  "first_seen": prior["first_seen"] if prior else now, "last_updated": now}
            store.upsert_event(ev)
            report["events"].append({"event_id": c["event_id"], "entity": c["entity"],
                                     "new_event": prior is None, "title": a["event"],
                                     "importance": a["importance"], "confidence": a["confidence"],
                                     "what_changed": a["what_changed"],
                                     "independent_sources": c["independent_sources"],
                                     "sources": [{"name": it["source_name"], "url": it["url"], "title": it["title"],
                                                  "published": datetime.fromtimestamp(it["ts"], timezone.utc).isoformat(),
                                                  "retrieved": report["run"]} for it in c["items"]],
                                     "analysis": a})
            digest_items.append({"cluster": c, "analysis": a, "prior": prior})
            for it in c["items"]:
                store.succeed(it["url"], it["thash"], "analyzed", json.dumps({"event_id": c["event_id"]}))
        else:
            report["quarantined"].append({"event_id": c["event_id"], "entity": c["entity"],
                                          "title": c["items"][0]["title"], "error": err})
            for it in c["items"]: store.fail(it["url"])
            print("QUARANTINED EVENT:", c["event_id"], "|", err)
        await asyncio.sleep(1)

    send_digest(digest_items, report)
    send_market_pulse()

    store.record_run(report["fetched"], report["new"], report["matched"], len(report["events"]))
    store_stats = store.stats()
    health = build_health(report, store_stats)
    with open(os.path.join(REPORTS, "run.json"), "w", encoding="utf-8") as f: json.dump(report, f, indent=2)
    with open(os.path.join(REPORTS, "health.json"), "w", encoding="utf-8") as f: json.dump(health, f, indent=2)

    es = report["events_summary"]
    mode = " [DRY RUN]" if DRY_RUN else ""
    print(f"FETCHED {report['fetched']} | NEW {report['new']} | MATCHED {report['matched']} | FP ARTICLES {len(front_page)} | EVENTS {es['clusters']} (new {es['new']} / upd {es['updated']}) | WIRE {len(report['wire'])} | QUARANTINED {len(report['quarantined'])}{mode}")
    note = (" — " + "; ".join(health["degraded"])) if health["degraded"] else ""
    print(f"HEALTH: {health['overall']}{note}")

if __name__ == "__main__":
    asyncio.run(main())
