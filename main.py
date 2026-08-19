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
    th = title_hash(item.get("title
