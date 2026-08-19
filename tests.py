"""Correctness baseline for AggregateIT POC. Run: python tests.py"""
import sys, os, json, time, tempfile
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
         "what_changed": "New event - no prior coverage",
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
check("mover gets +4 boost", sc >= 7, f"score={sc}")
main.MOVERS = {}

print("[T13] L3 Confluence Boost")
i1 = item("NVDA earnings beat", "$NVDA is up")
sc1, labels1 = main.score_item(i1); i1["matched_categories"] = labels1
i2 = item("Nvidia reports record", "Nvidia wins")
sc2, labels2 = main.score_item(i2); i2["matched_categories"] = labels2
ticker_counts = {}
for i in [i1, i2]:
    for label in i.get("matched_categories", []):
        t = label.split(" ")[0]
        if len(t) <= 5 and t.isalpha(): ticker_counts[t] = ticker_counts.get(t, 0) + 1
check("confluence detected", ticker_counts.get("NVDA", 0) >= 2, f"{ticker_counts}")

print("[T14] L4 Front-Page Floor")
check("floor is 5", main.FRONT_PAGE_FLOOR == 5, f"actual={main.FRONT_PAGE_FLOOR}")

print("[T15] Event clustering groups same-topic reports")
a1 = {"title": "Nvidia earnings beat estimates on data center demand", "source_name": "Reuters",
      "url": "http://x/1", "ts": 1, "source_type": "rss", "text": "", "score": 8,
      "matched_categories": ["NVDA"], "keyword_ids": []}
a2 = {"title": "Nvidia earnings beat estimates as data center demand surges", "source_name": "Bloomberg",
      "url": "http://x/2", "ts": 2, "source_type": "rss", "text": "", "score": 7,
      "matched_categories": ["NVDA"], "keyword_ids": []}
a3 = {"title": "Nvidia faces new export restrictions in Asia", "source_name": "WSJ",
      "url": "http://x/3", "ts": 3, "source_type": "rss", "text": "", "score": 7,
      "matched_categories": ["NVDA"], "keyword_ids": []}
clusters = main.cluster_events([a1, a2, a3])
check("same topic clustered", any(len(c["items"]) == 2 for c in clusters), f"{len(clusters)} clusters")
check("different topic separate", len(clusters) == 2, f"{len(clusters)} clusters")

print("[T16] Syndicated copies don't inflate corroboration")
b1 = dict(a1, url="http://y/1")
b2 = dict(a1, url="http://y/2", title="Nvidia earnings beat estimates on data center demand ")
c1 = main.cluster_events([b1, b2])
check("same source = 1 independent", c1[0]["independent_sources"] == 1, c1[0]["independent_sources"])
b3 = dict(a1, source_name="Bloomberg", url="http://y/3")
c2 = main.cluster_events([b1, b3])
check("two sources = 2 independent", c2[0]["independent_sources"] == 2, c2[0]["independent_sources"])

print("[T17] Event store continuity")
tmp2 = tempfile.mktemp(suffix=".db")
st2 = SQLiteStore(path=tmp2)
ev = {"event_id": "evt1", "entity": "NVDA", "tokens_json": json.dumps(["nvidia", "earnings"]),
      "title": "NVDA earnings", "event_type": "earnings", "status": "active", "severity": "High",
      "confidence": 70, "source_count": 2, "assessment": "strong", "what_changed": "new",
      "urls_json": "[]", "first_seen": 1000.0, "last_updated": 1000.0}
st2.upsert_event(ev)
st2.upsert_event(dict(ev, confidence=85, source_count=5, last_updated=2000.0))
rows = st2.recent_events("NVDA", hours=10**9)
check("first_seen preserved", rows[0]["first_seen"] == 1000.0, rows[0]["first_seen"])
check("updated fields persist", rows[0]["confidence"] == 85 and rows[0]["source_count"] == 5)

print("[T18] Cross-run event resolution")
cl1 = {"entity": "NVDA", "tokens": {"nvidia", "earnings", "beat"}, "items": [a1], "event_id": "x"}
match = main.resolve_prior_event(cl1, st2)
check("similar stored event found", match is not None and match["event_id"] == "evt1", match)
cl2 = {"entity": "NVDA", "tokens": {"nvidia", "export", "restrictions", "asia"}, "items": [a3], "event_id": "y"}
check("different topic not matched", main.resolve_prior_event(cl2, st2) is None)

print(f"\nRESULTS: {PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
