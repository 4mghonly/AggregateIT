"""Correctness baseline for AggregateIT POC. Run: python tests.py"""
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main, tv
from storage import SQLiteStore

PASS = 0; FAIL = 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  [PASS] {name}")
    else: FAIL += 1; print(f"  [FAIL] {name} :: {detail}")

def item(title, text="", source="Test Source"):
    return {"title": title, "text": text, "source_name": source,
            "source_type": "rss", "url": "http://example.com/t"}

print("[T1] Common-word ticker false positives must score 0")
for txt in ["The app has a pool near the well", "Ice cream cost a lot now"]:
    sc, labels = main.score_item(item(txt, txt))
    check(f"'{txt[:40]}'", sc == 0, f"score={sc} labels={labels}")

print("[T2] $TICKER cashtags must match")
for txt, sym in [("$NVDA jumps on earnings", "NVDA"), ("$TSLA recall news", "TSLA")]:
    sc, labels = main.score_item(item(txt, txt))
    check(f"'{txt[:40]}'", sc > 0 and any(sym in l for l in labels), f"score={sc}")

print("[T3] Company names must match")
for txt in ["Nvidia reports record revenue", "Microsoft announces AI features"]:
    sc, labels = main.score_item(item(txt, txt))
    check(f"'{txt[:40]}'", sc > 0, f"score={sc}")

print("[T4] Title normalization and dedup hashing")
check("normalize equal", main.normalize_title("Breaking: NVDA Jumps!") == main.normalize_title("breaking nvda jumps"))
check("hash differs", main.title_hash("Oil prices surge") != main.title_hash("Gold prices fall"))

print("[T5] Keyword clusters match independently")
sc, labels = main.score_item(item("Strait of Hormuz blockade feared", "Tanker seizures"))
check("ME-04 matched", any("ME-04" in l for l in labels), f"labels={labels}")

print("[T6] Priority sources get boosted")
sc, labels = main.score_item(item("Press release", "Routine", source="Federal Reserve"))
check("Fed boosted", sc >= 5, f"score={sc}")

print("[T7] TradingView 'Load More' pagination")
def fake_post(body):
    start, end = body["range"]; total = 2500
    return {"totalCount": total, "data": [{"s": f"T{i}", "d": [f"Co {i}", "Tech", 1e9, 1.0, 1.0, 1e6]} for i in range(start, min(end, total))]}
uni, total = tv.fetch_universe(post_fn=fake_post)
check("paginates to end", len(uni) == 2500 and total == 2500)

print("[T8] Movers scans merge")
def fake_post2(body):
    f = body.get("filter", [])
    if f and f[0]["operation"] == "less": return {"totalCount": 1, "data": [{"s": "BBB", "d": ["B", "T", 1, -9, 2, 1]}]}
    return {"totalCount": 1, "data": [{"s": "AAA", "d": ["A", "T", 1, 8, 3, 1]}]}
mv = tv.fetch_movers(post_fn=fake_post2)
check("movers merged", set(mv) == {"AAA", "BBB"})

print("[T9] Qwen schema validation")
valid = {"event": "Fed holds", "event_type": "macro", "facts": ["held"], "assessment": "pause",
         "importance": "High", "confidence": 80, "sentiment": "neutral", "entities": ["Fed"],
         "tickers": ["NVDA"], "evidence": ["held"], "corroboration": "multi-source",
         "source_reliability": "High", "gaps": []}
ok, obj, _ = main.validate_analysis(dict(valid))
check("valid passes", ok)
bad = dict(valid); bad["confidence"] = 150
ok, _, _ = main.validate_analysis(bad)
check("range enforced", not ok)
single = dict(valid); single["corroboration"] = "none"; single["confidence"] = 90
ok, obj, _ = main.validate_analysis(single)
check("single-source capped", ok and obj["confidence"] == 60)

print("[T10] Storage state machine")
tmp = tempfile.mktemp(suffix=".db")
st = SQLiteStore(path=tmp)
st.register("http://a", "h1", "discovered", 5)
check("discovered retriable", st.url_active("http://a"))
st.fail("http://a")
check("failed retriable", st.url_active("http://a"))
st.succeed("http://a", "h1", "analyzed", "{}")
check("analyzed terminal", not st.url_active("http://a"))

print("[T11] System health visibility")
main.HEALTH.update({"rss_ok": 90, "rss_fail": 5, "reddit_ok": 0, "reddit_fail": 32, "github_ok": 5, "github_fail": 0,
                    "qwen_ok": 3, "qwen_fail": 0, "qwen_invalid": 0, "discord_ok": 3, "discord_fail": 0, "discord_skipped": 0,
                    "tv_movers_loaded": 10, "tv_universe_loaded": 100})
h = main.build_health({"run": "x", "new": 1, "matched": 3}, {"fresh_init": False})
check("degraded = YELLOW", h["overall"] == "YELLOW")

print("[T12] L2 Market-Movers Boost")
main.MOVERS = {"XYZ": {"pct": 15.0}}
sc, labels = main.score_item(item("XYZ stock explodes today", "$XYZ is up"))
check("mover gets +4 boost", sc >= 7, f"score={sc}") # 3 (cashtag) + 4 (mover) = 7
main.MOVERS = {}

print("[T13] L3 Confluence Boost")
i1 = item("NVDA earnings beat", "$NVDA is up")
sc1, labels1 = main.score_item(i1); i1["matched_categories"] = labels1
i2 = item("Nvidia reports record", "Nvidia wins")
sc2, labels2 = main.score_item(i2); i2["matched_categories"] = labels2
# Simulate main loop confluence logic
ticker_counts = {}
for i in [i1, i2]:
    for label in i.get("matched_categories", []):
        t = label.split(" ")[0]
        if len(t) <= 5 and t.isalpha(): ticker_counts[t] = ticker_counts.get(t, 0) + 1
check("confluence detected", ticker_counts.get("NVDA", 0) >= 2, f"{ticker_counts}")

print("[T14] L4 Front-Page Floor")
check("floor is 5", main.FRONT_PAGE_FLOOR == 5)

print(f"\nRESULTS: {PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
