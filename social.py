"""social.py — social signal layer (Update C).
Reddit via Arctic Shift in 3 lanes (NEW/TOP/RISING) + dual-axis comments,
X via RSSHub instance rotation, StockTwits trending + streams.
Items match main.py schema."""
import os, json, time, re, calendar, requests, feedparser
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
SHIFT = "https://arctic-shift.philo.berkeley.edu/api/reddit"
RSSHUB = ["https://rsshub.app", "https://rsshub.rssforever.com", "https://hub.slarker.me"]

def _load_chatter():
    try:
        with open(os.path.join(BASE, "config", "chatter.json"), encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

def _shift_get(path, params):
    for attempt in (1, 2):
        try:
            r = requests.get(SHIFT + path, params=params, timeout=20)
            r.raise_for_status()
            return r.json().get("data", [])
        except Exception:
            if attempt == 2: return []
            time.sleep(1)

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
        time.sleep(0.3)

    for q in chat.get("queries", [])[:12]:
        rows = _shift_get("/comments/search", {"q": q, "after": after, "sort": "score:desc", "limit": caps.get("comments_per_query", 5)})
        for row in rows:
            if (row.get("score") or 0) < 3: continue
            if row.get("subreddit") not in subs: continue
            add(row, "comment", is_comment=True)
        time.sleep(0.3)
    return out

def _twitter_items(since_ts):
    chat = _load_chatter()
    per = chat.get("caps", {}).get("tweets_per_handle", 5)
    out = []
    for cat, hs in chat.get("twitter_handles", {}).items():
        for h in hs:
            xml = None
            for inst in RSSHUB:
                try:
                    r = requests.get(f"{inst}/twitter/user/{h}", timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                    if r.status_code == 200: xml = r.text; break
                except Exception: continue
            if not xml: continue
            for e in feedparser.parse(xml).entries[:per]:
                out.append({"source_type": "twitter", "source_name": "X:@" + h, "category": "Twitter/" + cat,
                            "url": e.get("link", ""), "title": (e.get("title") or "")[:200],
                            "text": re.sub("<[^>]+>", "", e.get("summary", ""))[:4000],
                            "ts": calendar.timegm(e.published_parsed) if e.get("published_parsed") else time.time()})
            time.sleep(0.5)
    return out

def _stocktwits_items():
    out = []
    try:
        r = requests.get("https://api.stocktwits.com/api/2/trending/symbols.json", timeout=10)
        syms = [s.get("symbol") for s in r.json().get("symbols", [])[:10]]
    except Exception:
        syms = []
    for t in syms:
        try:
            r = requests.get(f"https://api.stocktwits.com/api/2/streams/symbol/{t}.json", timeout=10)
            for m in r.json().get("messages", [])[:3]:
                out.append({"source_type": "stocktwits", "source_name": "ST:$" + str(t), "category": "StockTwits",
                            "url": f"https://stocktwits.com/symbol/{t}", "title": f"${t}: " + (m.get("body") or "")[:70],
                            "text": (m.get("body") or "")[:4000], "ts": _parse_ts(m.get("created_at"))})
        except Exception: pass
        time.sleep(0.3)
    return out

def fetch_all(since_ts):
    out = _reddit_items(since_ts) + _twitter_items(since_ts) + _stocktwits_items()
    cap = _load_chatter().get("caps", {}).get("total", 60)
    return out[:cap]
