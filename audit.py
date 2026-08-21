import asyncio, json, os
import aiohttp, feedparser

BASE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "NewsIntelEngine-Audit/0.1 (personal research)"}

def load(n):
    with open(os.path.join(BASE, "config", n), encoding="utf-8") as f: return json.load(f)

RAW = load("sources.json"); REDDIT = load("reddit.json")
seen = set(); RSS = []; GH = []
for s in RAW:
    u = s.get("Url", "").replace("http://", "https://").rstrip("/")
    if not u or u in seen: continue
    seen.add(u)
    (GH if "github.com/" in u else RSS).append({**s, "_url": u})

RESULTS = []

async def get(session, url, sem):
    async with sem:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as r:
            return r.status, (await r.text() if r.status == 200 else "")

async def check_rss(session, src, sem):
    try:
        status, txt = await get(session, src["_url"], sem)
        n = len(feedparser.parse(txt).entries) if txt else 0
        RESULTS.append({"kind": "RSS", "name": src.get("Source_name", "?"), "url": src["_url"],
                        "http": status, "items": n, "ok": status == 200 and n > 0})
    except Exception as e:
        RESULTS.append({"kind": "RSS", "name": src.get("Source_name", "?"), "url": src["_url"],
                        "http": "ERR", "items": 0, "ok": False, "err": str(e)[:80]})

async def check_reddit(session, sub, sem):
    try:
        status, txt = await get(session, f"https://www.reddit.com/r/{sub}/new/.rss", sem)
        n = len(feedparser.parse(txt).entries) if txt else 0
        RESULTS.append({"kind": "REDDIT", "name": "r/" + sub, "http": status, "items": n,
                        "comments": 0, "ok": status == 200 and n > 0})
    except Exception as e:
        RESULTS.append({"kind": "REDDIT", "name": "r/" + sub, "http": "ERR", "items": 0,
                        "comments": 0, "ok": False, "err": str(e)[:80]})

async def check_gh(session, repo, sem):
    try:
        status, txt = await get(session, f"https://api.github.com/repos/{repo}", sem)
        public = (json.loads(txt).get("private") is False) if txt else False
        RESULTS.append({"kind": "GITHUB", "name": repo, "http": status, "items": 1 if public else 0,
                        "ok": status == 200 and public})
    except Exception as e:
        RESULTS.append({"kind": "GITHUB", "name": repo, "http": "ERR", "items": 0, "ok": False, "err": str(e)[:80]})

async def main():
    sem, sem_rd = asyncio.Semaphore(10), asyncio.Semaphore(3)
    async with aiohttp.ClientSession(headers=UA) as s:
        await asyncio.gather(
            *[check_rss(s, x, sem) for x in RSS],
            *[check_reddit(s, x["sub"], sem_rd) for x in REDDIT],
            *[check_gh(s, x["_url"].split("github.com/")[1], sem) for x in GH])
    for r in sorted(RESULTS, key=lambda r: (r["kind"], r["name"])):
        tag = "OK  " if r["ok"] else "FAIL"
        extra = f"items={r.get('items')}" + (f" comments={r.get('comments')}" if r["kind"] == "REDDIT" else "")
        print(f"[{tag}] {r['kind']:6} {r['name']:45} http={r.get('http')} {extra} {r.get('err','')}")
    bad = [r for r in RESULTS if not r["ok"]]
    print(f"\nTOTAL {len(RESULTS)} | OK {len(RESULTS)-len(bad)} | FAIL {len(bad)}")
    print("FAILED SOURCES:")
    for r in bad: print(" -", r["kind"], "|", r["name"], "|", r.get("url", ""), "|", r.get("err", ""))
    with open("audit_report.json", "w") as f: json.dump(RESULTS, f, indent=2)

# ---- Update C: per-source health + auto-mute ----
import time as _time
HEALTH_FILE = os.path.join(BASE, "data", "source_health.json")
MUTED_FILE = os.path.join(BASE, "data", "muted.json")

def _load_json(p):
    try:
        with open(p, encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

def record(name, ok):
    if not name: return
    h = _load_json(HEALTH_FILE)
    e = h.setdefault(name, {"ok": 0, "fail": 0})
    e["ok" if ok else "fail"] += 1; e["ts"] = _time.time()
    with open(HEALTH_FILE, "w", encoding="utf-8") as f: json.dump(h, f)

def is_muted(name):
    return name in _load_json(MUTED_FILE)

def refresh_mutes():
    h = _load_json(HEALTH_FILE); m = _load_json(MUTED_FILE)
    for name, e in h.items():
        tot = e.get("ok", 0) + e.get("fail", 0)
        if tot >= 3 and e["ok"] / tot < 0.5: m[name] = _time.time()
        elif tot >= 3 and e["ok"] / tot >= 0.7: m.pop(name, None)
    with open(MUTED_FILE, "w", encoding="utf-8") as f: json.dump(m, f)

asyncio.run(main())
