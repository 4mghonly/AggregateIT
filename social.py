"""social.py v4 — bounded, balanced social and specialist-blog signal layer.
If SOCIAL_PROXY_URL is set, all Reddit/Twitter/StockTwits traffic routes through it
(bypasses datacenter IP blocks); otherwise falls back to direct calls.
Reddit: Arctic Shift + PullPush mirror, 3 lanes (NEW/TOP/RISING) + dual-axis comments.
Twitter/X: RSSHub rotation with 4s pre-check. StockTwits: trending + streams.
Writes data/social_pulse.json for the Gazette. Items match main.py schema."""
import os, json, time, re, calendar, requests, feedparser
from datetime import datetime, timezone, timedelta
from urllib.parse import quote, urlencode

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
PROXY = os.environ.get("SOCIAL_PROXY_URL", "").rstrip("/")
SHIFT_MIRRORS = [
    ("https://arctic-shift.philo.berkeley.edu/api/reddit", "arctic"),
    ("https://api.pullpush.io/reddit", "pullpush"),
]
RSSHUB = ["https://rsshub.rssforever.com", "https://hub.slarker.me", "https://rsshub.ktachibana.party", "https://rsshub.app", "https://rsshub.pseudoyu.com"]
UA = {"User-Agent": "Mozilla/5.0 (compatible; NewsIntelEngine/0.5)"}

def _route(url, params=None):
    if params:
        url = url + ("&" if "?" in url else "?") + urlencode(params)
    if PROXY:
        return PROXY + "/?target=" + quote(url, safe="")
    return url

def _load_chatter():
    try:
        with open(os.path.join(BASE, "config", "chatter.json"), encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

def _shift_get(path, params):
    for base, kind in SHIFT_MIRRORS:
        url = base + path
        p = dict(params)
        if kind == "pullpush":
            url = url.replace("/submissions/search", "/search/submission").replace("/comments/search", "/search/comment")
            p["size"] = p.pop("limit", 5)
        try:
            r = requests.get(_route(url, p), timeout=8, headers=UA)
            if r.status_code == 200: return r.json().get("data", [])
        except Exception: continue
    return []

def _parse_ts(s):
    try: return datetime.fromisoformat((s or "").replace("Z", "+00:00")).timestamp()
    except Exception: return time.time()

def _entry_ts(entry):
    """Return a feed entry timestamp without turning undated items into fresh news."""
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    return calendar.timegm(parsed) if parsed else 0

def _rotating_sample(values, limit, salt=""):
    """Bound large watchlists while rotating coverage every hour."""
    values = list(values or [])
    limit = max(0, int(limit or 0))
    if not limit or len(values) <= limit: return values
    slot = int(time.time() // 3600) + sum(ord(c) for c in salt)
    start = slot % len(values)
    return (values[start:] + values[:start])[:limit]

def _reddit_items(since_ts, expired=None):
    chat = _load_chatter()
    caps = chat.get("caps", {})
    per_lane = caps.get("reddit_per_lane", 5)
    subs = chat.get("reddit_subs", [])
    out = []; seen = set()
    now = time.time()
    after = datetime.fromtimestamp(since_ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rising_after = datetime.fromtimestamp(now - 6 * 3600, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def add(row, lane, is_comment=False):
        pid = row.get("id") or row.get("permalink") or ""
        if not pid or pid in seen: return
        seen.add(pid)
        url = row.get("permalink") or ""
        if url and not url.startswith("http"): url = "https://www.reddit.com" + url
        title = row.get("title") or ("Comment: " + (row.get("body") or "")[:70])
        out.append({"source_type": "reddit_comment" if is_comment else "reddit",
                    "source_name": "r/" + (row.get("subreddit") or "?"), "category": "Reddit",
                    "url": url or ("https://redd.it/" + pid), "title": (title or "")[:200],
                    "text": (row.get("selftext") or row.get("body") or "")[:4000],
                    "ts": row.get("created_utc") or since_ts, "lane": lane})

    for sub in subs:
        if expired and expired(): break
        for lane, sort, aft in (("new", "created_utc:desc", after), ("top", "score:desc", after), ("rising", "score:desc", rising_after)):
            rows = _shift_get("/submissions/search", {"subreddit": sub, "after": aft, "sort": sort, "limit": per_lane})
            for row in rows:
                if lane == "rising" and (row.get("score") or 0) < 10: continue
                add(row, lane)
        time.sleep(0.2)

    for q in chat.get("queries", [])[:12]:
        if expired and expired(): break
        rows = _shift_get("/comments/search", {"q": q, "after": after, "sort": "score:desc", "limit": caps.get("comments_per_query", 5)})
        for row in rows:
            if (row.get("score") or 0) < 3: continue
            if row.get("subreddit") not in subs: continue
            add(row, "comment", is_comment=True)
        time.sleep(0.2)
    return out

def _get_working_rsshub():
    for inst in RSSHUB:
        try:
            r = requests.get(_route(inst), timeout=4, headers=UA)
            if r.status_code < 500: return inst
        except Exception: continue
    return None

def _twitter_items(since_ts, inst=None, expired=None):
    if inst is None: inst = _get_working_rsshub()
    if not inst:
        print("SOCIAL: all RSSHub instances unreachable - skipping Twitter this run")
        return []
    chat = _load_chatter()
    caps = chat.get("caps", {})
    per = caps.get("tweets_per_handle", 5)
    per_category = caps.get("handles_per_category", 4)
    out = []
    for cat, hs in chat.get("twitter_handles", {}).items():
        if expired and expired(): break
        for h in _rotating_sample(hs, per_category, "twitter:" + cat):
            if expired and expired(): break
            try:
                r = requests.get(_route(f"{inst}/twitter/user/{h}"), timeout=6, headers=UA)
                if r.status_code == 200:
                    for e in feedparser.parse(r.text).entries[:per]:
                        ts = _entry_ts(e)
                        if not ts or ts < since_ts: continue
                        out.append({"source_type": "twitter", "source_name": "X:@" + h, "category": "Twitter/" + cat,
                                    "url": e.get("link", ""), "title": (e.get("title") or "")[:200],
                                    "text": re.sub("<[^>]+>", "", e.get("summary", ""))[:4000],
                                    "ts": ts})
            except Exception: pass
            time.sleep(0.2)
    return out

RSSHUB_ROUTES = {
    "bluesky":  lambda h: f"/bluesky/user/{h}",
    "mastodon": lambda h: f"/mastodon/account/{h}",
    "telegram": lambda h: f"/telegram/channel/{h}",
    "youtube":  lambda h: f"/youtube/channel/{h}",
}
RSSHUB_PREFIX = {"bluesky": "BSKY:", "mastodon": "MASTO:", "telegram": "TG:", "youtube": "YT:"}

def _rsshub_items(since_ts, inst=None, expired=None):
    if inst is None: inst = _get_working_rsshub()
    if not inst: return []
    chat = _load_chatter()
    caps = chat.get("caps", {})
    per = caps.get("rsshub_per_source", 3)
    per_platform = caps.get("rsshub_sources_per_platform", 6)
    out = []
    for platform, handles in chat.get("rsshub_sources", {}).items():
        if expired and expired(): break
        route = RSSHUB_ROUTES.get(platform)
        if not route: continue
        for h in _rotating_sample(handles, per_platform, "rsshub:" + platform):
            if expired and expired(): break
            try:
                r = requests.get(_route(inst + route(h)), timeout=6, headers=UA)
                if r.status_code == 200:
                    for e in feedparser.parse(r.text).entries[:per]:
                        ts = _entry_ts(e)
                        if not ts or ts < since_ts: continue
                        out.append({"source_type": platform, "source_name": RSSHUB_PREFIX[platform] + h,
                                    "category": platform.capitalize(),
                                    "url": e.get("link", ""), "title": (e.get("title") or "")[:200],
                                    "text": re.sub("<[^>]+>", "", e.get("summary", ""))[:4000],
                                    "ts": ts})
            except Exception: pass
            time.sleep(0.2)
    return out

def _stocktwits_items():
    out = []
    try:
        r = requests.get(_route("https://api.stocktwits.com/api/2/trending/symbols.json"), timeout=5)
        syms = [s.get("symbol") for s in r.json().get("symbols", [])[:10]]
    except Exception:
        syms = []
    for t in syms:
        try:
            r = requests.get(_route(f"https://api.stocktwits.com/api/2/streams/symbol/{t}.json"), timeout=5)
            for m in r.json().get("messages", [])[:3]:
                out.append({"source_type": "stocktwits", "source_name": "ST:$" + str(t), "category": "StockTwits",
                            "url": f"https://stocktwits.com/symbol/{t}", "title": f"${t}: " + (m.get("body") or "")[:70],
                            "text": (m.get("body") or "")[:4000], "ts": _parse_ts(m.get("created_at"))})
        except Exception: pass
        time.sleep(0.2)
    return out

def _blog_items(since_ts, expired=None):
    """Fetch verified public specialist and institutional feeds from chatter.json."""
    chat = _load_chatter(); out = []
    per = chat.get("caps", {}).get("blog_items_per_feed", 3)
    for src in chat.get("blog_feeds", []):
        if expired and expired(): break
        try:
            r = requests.get(_route(src["url"]), timeout=8, headers=UA)
            if r.status_code != 200: continue
            for e in feedparser.parse(r.content).entries[:per]:
                ts = _entry_ts(e)
                if not ts or ts < since_ts: continue
                out.append({"source_type": "blog", "source_name": "BLOG:" + src["name"],
                            "category": "Blog/" + src.get("category", "Analysis"),
                            "url": e.get("link", ""), "title": (e.get("title") or "")[:200],
                            "text": re.sub("<[^>]+>", "", e.get("summary", ""))[:4000], "ts": ts})
        except Exception: pass
    return out

def _balanced_merge(streams, total, quotas):
    """Prevent the first (normally Reddit) stream from consuming the global cap."""
    picked, leftovers = [], []
    for name, items in streams.items():
        cap = max(0, int(quotas.get(name, total)))
        picked.extend(items[:cap]); leftovers.extend(items[cap:])
    if len(picked) < total:
        picked.extend(sorted(leftovers, key=lambda x: -x.get("ts", 0))[:total - len(picked)])
    return sorted(picked, key=lambda x: -x.get("ts", 0))[:total]

def fetch_all(since_ts):
    # Wall-clock budget: expanded source surface means a degraded-mirror day
    # could otherwise starve the hourly engine job (25-min timeout, 2 passes).
    deadline = time.time() + float(os.environ.get("SOCIAL_BUDGET_S", "600"))
    def expired(): return time.time() > deadline
    rd = _reddit_items(since_ts, expired)
    inst = _get_working_rsshub()
    tw = [] if expired() else _twitter_items(since_ts, inst, expired)
    rs = [] if expired() else _rsshub_items(since_ts, inst, expired)
    st = _stocktwits_items()
    bg = [] if expired() else _blog_items(since_ts, expired)
    chat = _load_chatter(); caps = chat.get("caps", {})
    total = caps.get("total", 100)
    quotas = caps.get("platform_quotas", {"reddit": 30, "twitter": 25, "rsshub": 20, "stocktwits": 10, "blogs": 15})
    streams = {"reddit": rd, "twitter": tw, "rsshub": rs, "stocktwits": st, "blogs": bg}
    print("SOCIAL FETCH: reddit=%d twitter=%d rsshub=%d stocktwits=%d blogs=%d" % (len(rd), len(tw), len(rs), len(st), len(bg)))
    out = _balanced_merge(streams, total, quotas)
    try:
        os.makedirs(DATA, exist_ok=True)
        sp = {"ts": time.time(), "counts": {}, "coverage": {k: len(v) for k, v in streams.items()}, "top": []}
        for i in out:
            lane = (":" + i["lane"]) if i.get("lane") else ""
            k = i.get("source_type", "?") + lane
            sp["counts"][k] = sp["counts"].get(k, 0) + 1
        for i in sorted(out, key=lambda x: -x.get("ts", 0))[:12]:
            sp["top"].append({"t": (i.get("title") or "")[:90], "src": i.get("source_name", ""),
                              "lane": i.get("lane", ""), "type": i.get("source_type", "")})
        with open(os.path.join(DATA, "social_pulse.json"), "w", encoding="utf-8") as f:
            json.dump(sp, f)
    except Exception:
        pass
    return out
