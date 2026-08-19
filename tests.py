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
for txt in ["The app has a pool near the well",
            "Ice cream cost a lot now",
            "The tech doc was on the ball",
            "We saw a fox in the para"]:
    sc, labels = main.score_item(item(txt, txt))
    check(f"'{txt[:40]}'", sc == 0, f"score={sc} labels={labels}")

print("[T2] $TICKER cashtags must match")
for txt, sym in [("$NVDA jumps on earnings", "NVDA"),
                 ("Breaking: $TSLA recall news", "TSLA"),
                 ("$GME squeeze again", "GME")]:
    sc, labels = main.score_item(item(txt, txt))
    check(f"'{txt[:40]}'", sc > 0 and any(sym in l for l in labels), f"score={sc} labels={labels}")

print("[T3] Company names must match")
for txt in ["Nvidia reports record revenue", "Microsoft announces AI features"]:
    sc, labels = main.score_item(item(txt, txt))
    check(f"'{txt[:40]}'", sc > 0, f"score={sc} labels={labels}")

print("[T4] Title normalization and dedup hashing")
a = main.normalize_title("Breaking: NVDA Jumps 5% on Earnings!")
b = main.normalize_title("breaking  nvda jumps 5% on earnings")
check("normalize equal", a == b, f"'{a}' vs '{b}'")
check("hash equal", main.title_hash("Oil prices surge on OPEC cuts") ==
                     main.title_hash("oil prices  surge on opec cuts!"))
check("hash differs", main.title_hash("Oil prices surge") != main.title_hash("Gold prices fall"))

print("[T5] Keyword clusters match independently (F-03)")
sc, labels = main.score_item(item("Strait of Hormuz blockade feared",
                                  "Tanker seizures reported amid rising tensions"))
check("ME-04 matched", any("ME-04" in l for l in labels), f"labels={labels}")

print("[T6] Priority sources get boosted")
sc, labels = main.score_item(item("Press release", "Routine announcement", source="Federal Reserve"))
check("Fed boosted", sc >= 5, f"score={sc}")

print("[T7] TradingView 'Load More' pagination reaches totalCount")
def fake_post(body):
    start, end = body["range"]; total = 2500
    rows = [{"s": f"T{i}", "d": [f"Company {i}", "Technology", 1e9, 1.0, 1.0, 1e6]}
            for i in range(start, min(end, total))]
    return {"totalCount": total, "data": rows}
uni, total = tv.fetch_universe(post_fn=fake_post)
check("paginates to end", len(uni) == 2500 and total == 2500, f"len={len(uni)} total={total}")

print("[T8] Movers scans merge and dedupe")
calls = []
def fake_post2(body):
    calls.append(body)
    f = body.get("filter", [])
    if f and f[0]["operation"] == "less":
        return {"totalCount": 1, "data": [{"s": "BBB", "d": ["B Co", "Tech", 1e9, -9.0, 2.5, 1e6]}]}
    return {"totalCount": 1, "data": [{"s": "AAA", "d": ["A Co", "Tech", 1e9, 8.0, 3.0, 1e6]}]}
mv = tv.fetch_movers(post_fn=fake_post2)
check("movers merged", set(mv) == {"AAA", "BBB"}, f"{sorted(mv)}")
check("3 scans issued", len(calls) == 3, f"{len(calls)}")

print("[T9] Qwen schema validation (F-07/F-08)")
valid = {"event": "Fed holds rates", "event_type": "macro",
         "facts": ["The Fed held rates steady"],
         "assessment": "Likely pause through Q4", "importance": "High", "confidence": 80,
         "sentiment": "neutral", "entities": ["Federal Reserve"],
         "tickers": ["NVDA", "notarealticker123"],
         "evidence": ["held rates steady"], "corroboration": "multi-source",
         "source_reliability": "High", "gaps": []}
ok, obj, errs = main.validate_analysis(dict(valid))
check("valid response passes", ok, errs)
check("hallucinated ticker stripped", obj["tickers"] == ["NVDA"], obj["tickers"])
bad = dict(valid); del bad["assessment"]
ok, _, errs = main.validate_analysis(bad)
check("missing field rejected", not ok, errs)
bad = dict(valid); bad["importance"] = "EXTREME"
ok, _, errs = main.validate_analysis(bad)
check("bad enum rejected", not ok, errs)
bad = dict(valid); bad["confidence"] = 150
ok, _, errs = main.validate_analysis(bad)
check("confidence range enforced", not ok, errs)
single = dict(valid); single["corroboration"] = "none"; single["confidence"] = 90
ok, obj, errs = main.validate_analysis(single)
check("single-source capped at 60", ok and obj["confidence"] == 60, obj.get("confidence"))

print("[T10] Storage state machine (F-06)")
tmp = tempfile.mktemp(suffix=".db")
st = SQLiteStore(path=tmp)
st.register("http://a", "h1", "discovered", 5)
check("discovered retriable", st.url_active("http://a"))
st.fail("http://a")
check("failed retriable (retry next run)", st.url_active("http://a"))
st.succeed("http://a", "h1", "analyzed", "{}")
check("analyzed terminal", not st.url_active("http://a"))
check("title marked only on success", not st.title_active("h1"))
st.register("http://b", "h2", "filtered", 0)
check("filtered terminal", not st.url_active("http://b"))
check("unseen title active", st.title_active("h9"))
stats = st.stats()
check("stats report states", stats["items_by_state"].get("analyzed") == 1, stats)

print("[T11] System health visibility")
main.HEALTH.update({"rss_ok": 90, "rss_fail": 5, "reddit_ok": 0, "reddit_fail": 32,
                    "github_ok": 5, "github_fail": 0, "qwen_ok": 3, "qwen_fail": 0,
                    "qwen_invalid": 0, "discord_ok": 3, "discord_fail": 0, "discord_skipped": 0})
h = main.build_health({"run": "x", "new": 1, "matched": 3}, {"fresh_init": False})
check("degraded = YELLOW", h["overall"] == "YELLOW", h["overall"])
check("failures listed", any("RSS" in d for d in h["degraded"]), h["degraded"])
main.HEALTH.update({"qwen_fail": 5, "qwen_ok": 0})
h2 = main.build_health({"run": "x", "new": 1, "matched": 3}, {"fresh_init": False})
check("Qwen hard-fail = RED (live)", h2["overall"] == "RED" or main.DRY_RUN, h2["overall"])

print(f"\nRESULTS: {PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
