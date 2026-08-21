"""social.py v2 — social signal layer (hardened for GitHub Actions egress).
Reddit: Arctic Shift primary + PullPush mirror; 3 lanes (NEW/TOP/RISING) + dual-axis comments.
Twitter/X: RSSHub rotation with a 4s pre-check (skip entirely if all instances blocked).
StockTwits: trending + per-symbol streams.
Writes data/social_pulse.json for the Gazette. Items match main.py schema."""
import os, json, time, re, calendar, requests, feedparser
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
SHIFT_MIRRORS = [
    ("https://arctic-shift.philo.berkeley.edu/api/reddit", "arctic"),
    ("https://api.pullpush.io/reddit", "pullpush"),
]
RSSHUB = ["https://rsshub.app", "https://rsshub.rssforever.com", "https://hub.slarker.me", "https://rsshub.pseudoyu.com"]
UA = {"User-Agent": "Mozilla/5.0 (compatible; NewsIntelEngine/0.5)"}

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
            r = requests.get(url, params=p, timeout=8, headers=UA)
            if r.status_code == 200: return r.json().get("data", [])
        except Exception: continue
    return []

def _parse_ts(s):
    try: return datetime.fromisoformat((s or "").replace("Z", "+00:00")).timestamp()
    except Exception: return time.time()

def _reddit_items(since_ts):
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
        for lane, sort, aft in (("new", "created_utc:desc", after), ("top", "score:desc", after), ("rising", "score:desc", rising_after)):
            rows = _shift_get("/submissions/search", {"subreddit": sub, "after": aft, "sort": sort, "limit": per_lane})
            for row in rows:
                if lane == "rising" and (row.get("score") or 0) < 10: continue
                add(row, lane)
        time.sleep(0.2)

    for q in chat.get("queries", [])[:12]:
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
            r = requests.get(inst, timeout=4, headers=UA)
            if r.status_code < 500: return inst
        except Exception: continue
    return None

def _twitter_items(since_ts):
    inst = _get_working_rsshub()
    if not inst:
        print("SOCIAL: all RSSHub instances unreachable - skipping Twitter this run")
        return []
    chat = _load_chatter()
    per = chat.get("caps", {}).get("tweets_per_handle", 5)
    out = []
    for cat, hs in chat.get("twitter_handles", {}).items():
        for h in hs:
            try:
                r = requests.get(f"{inst}/twitter/user/{h}", timeout=6, headers=UA)
                if r.status_code == 200:
                    for e in feedparser.parse(r.text).entries[:per]:
                        out.append({"source_type": "twitter", "source_name": "X:@" + h, "category": "Twitter/" + cat,
                                    "url": e.get("link", ""), "title": (e.get("title") or "")[:200],
                                    "text": re.sub("<[^>]+>", "", e.get("summary", ""))[:4000],
                                    "ts": calendar.timegm(e.published_parsed) if e.get("published_parsed") else time.time()})
            except Exception: pass
            time.sleep(0.2)
    return out

def _stocktwits_items():
    out = []
    try:
        r = requests.get("https://api.stocktwits.com/api/2/trending/symbols.json", timeout=5)
        syms = [s.get("symbol") for s in r.json().get("symbols", [])[:10]]
    except Exception:
        syms = []
    for t in syms:
        try:
            r = requests.get(f"https://api.stocktwits.com/api/2/streams/symbol/{t}.json", timeout=5)
            for m in r.json().get("messages", [])[:3]:
                out.append({"source_type": "stocktwits", "source_name": "ST:$" + str(t), "category": "StockTwits",
                            "url": f"https://stocktwits.com/symbol/{t}", "title": f"${t}: " + (m.get("body") or "")[:70],
                            "text": (m.get("body") or "")[:4000], "ts": _parse_ts(m.get("created_at"))})
        except Exception: pass
        time.sleep(0.2)
    return out

def fetch_all(since_ts):
    rd = _reddit_items(since_ts)
    tw = _twitter_items(since_ts)
    st = _stocktwits_items()
    print("SOCIAL FETCH: reddit=%d twitter=%d stocktwits=%d" % (len(rd), len(tw), len(st)))
    out = (rd + tw + st)[: _load_chatter().get("caps", {}).get("total", 60)]
    try:
        os.makedirs(DATA, exist_ok=True)
        sp = {"ts": time.time(), "counts": {}, "top": []}
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
