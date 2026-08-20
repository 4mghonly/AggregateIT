"""Correctness baseline for AggregateIT POC. Run: python tests.py"""
import sys, os, json, time, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main, tv, briefing, market
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
    return {"totalCount": total, "data": [{"s": f"T{i}", "d": [f"Co {i}", "Tech", 1e9, 0, 1.0, 1e6, 1]} for i in range(start, min(end, total))]}
uni, total = tv.fetch_universe(post_fn=fake_post)
check("paginates to end", len(uni) == 2500 and total == 2500)

print("[T8] Movers scans merge by sort direction")
def fake_post2(body):
    if body["sort"]["sortOrder"] == "asc":
        return {"totalCount": 1, "data": [{"s": "BBB", "d": ["", "B", "T", 1, 0, 2, 100000, 1, -9, 91, "stock"]}]}
    return {"totalCount": 1, "data": [{"s": "AAA", "d": ["", "A", "T", 1, 0, 3, 100000, 1, 8, 108, "stock"]}]}
mv = tv.fetch_movers(post_fn=fake_post2)
check("movers merged", set(mv) == {"AAA", "BBB"}, sorted(mv))

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
b1 = dict(a1, url="https://www.reuters.com/tech/nvda-1")
b2 = dict(a1, url="https://feeds.reuters.com/tech/nvda-1", title="Nvidia earnings beat estimates on data center demand ")
c1 = main.cluster_events([b1, b2])
check("syndicated = 1 independent", c1[0]["independent_sources"] == 1, c1[0]["independent_sources"])
b3 = dict(a1, source_name="Bloomberg", url="https://www.bloomberg.com/news/nvda-1")
c2 = main.cluster_events([b1, b3])
check("two families = 2 independent", c2[0]["independent_sources"] == 2, c2[0]["independent_sources"])

print("[T35] Canonical domain strips www/feeds prefixes")
check("www stripped", main.canonical_domain("https://www.reuters.com/x") == "reuters.com")
check("feeds maps to family", main.source_family(main.canonical_domain("https://feeds.reuters.com/x")) == "reuters")

print("[T36] Multi-source claims downgraded without independent evidence")
a_obj = {"corroboration": "multi-source", "confidence": 90}
main.apply_corroboration_policy(a_obj, {"independent_sources": 1})
check("downgraded + capped", a_obj["corroboration"] == "single-source" and a_obj["confidence"] == 70, a_obj)

print("[T17] Event store continuity")
tmp2 = tempfile.mktemp(suffix=".db")
st2 = SQLiteStore(path=tmp2)
t0 = time.time() - 3600
ev = {"event_id": "evt1", "entity": "NVDA", "tokens_json": json.dumps(["nvidia", "earnings"]),
      "title": "NVDA earnings", "event_type": "earnings", "status": "active", "severity": "High",
      "confidence": 70, "source_count": 2, "assessment": "strong", "what_changed": "new",
      "urls_json": "[]", "first_seen": t0, "last_updated": t0}
st2.upsert_event(ev)
st2.upsert_event(dict(ev, confidence=85, source_count=5, last_updated=time.time()))
rows = st2.recent_events("NVDA", hours=72)
check("first_seen preserved", abs(rows[0]["first_seen"] - t0) < 1, rows[0]["first_seen"])
check("updated fields persist", rows[0]["confidence"] == 85 and rows[0]["source_count"] == 5)

print("[T18] Cross-run event resolution")
cl1 = {"entity": "NVDA", "tokens": {"nvidia", "earnings", "beat"}, "items": [a1], "event_id": "x"}
match = main.resolve_prior_event(cl1, st2)
check("similar stored event found", match is not None and match["event_id"] == "evt1", match)
cl2 = {"entity": "NVDA", "tokens": {"nvidia", "export", "restrictions", "asia"}, "items": [a3], "event_id": "y"}
check("different topic not matched", main.resolve_prior_event(cl2, st2) is None)

print("[T19] Primary-listing filter removes preferreds/duplicate classes")
def fake_post3(body):
    return {"totalCount": 2, "data": [
        {"s": "NYSE:JPM", "d": ["", "JPMorgan", "Finance", 6e11, 0, 1.0, 500000, 1, 6.0, 106.0, "stock"]},
        {"s": "NYSE:JPM.PM", "d": ["", "JPMorgan Pfd", "Finance", 1e9, 0, 0.5, 100, 0, 0.5, 10.5, "fund"]}]}
p3 = tv.fetch_pulse(post_fn=fake_post3, cap=20)
check("non-primary excluded", all(m["t"] != "JPM.PM" for m in p3["mega_caps"]))
check("primary kept", any(m["t"] == "JPM" for m in p3["mega_caps"]))

print("[T20] Zero-snapshot validity gate")
def fake_post_zero(body):
    return {"totalCount": 2, "data": [
        {"s": "X1", "d": ["", "A", "T", 1e12, 0, 1.0, 0, 1, 0, 100, "stock"]},
        {"s": "X2", "d": ["", "B", "T", 9e11, 0, 1.0, 0, 1, 0, 100, "stock"]}]}
check("all-zero snapshot invalid", tv.fetch_pulse(post_fn=fake_post_zero)["valid"] is False)
def fake_post_live(body):
    return {"totalCount": 2, "data": [
        {"s": "X1", "d": ["", "A", "T", 1e12, 0, 1.0, 50000, 1, 2.5, 102.5, "stock"]},
        {"s": "X2", "d": ["", "B", "T", 9e11, 0, 1.0, 50000, 1, -1.0, 99.0, "stock"]}]}
check("live snapshot valid", tv.fetch_pulse(post_fn=fake_post_live)["valid"] is True)

print("[T21] Pulse mega-cap selection capped and sorted")
def fake_post_big(body):
    if body["sort"]["sortBy"] == "market_cap_calc":
        return {"totalCount": 30, "data": [{"s": f"S{i}", "d": ["", f"Co{i}", "T", 1e12 - i * 1e9, 0, 1.0, 10000, 1, 1.0, 101.0, "stock"]} for i in range(30)]}
    return {"totalCount": 0, "data": []}
p4 = tv.fetch_pulse(post_fn=fake_post_big, cap=20)
check("20 mega caps", len(p4["mega_caps"]) == 20, len(p4["mega_caps"]))
check("sorted by mcap", p4["mega_caps"][0]["mcap"] > p4["mega_caps"][-1]["mcap"])

print("[T22] Funds/ETFs excluded from stock lists")
NVDA_ROW = {"s": "NVDA", "d": ["", "Nvidia", "Tech", 1e12, 0, 1.0, 100000, 1, 1.0, 101.0, "stock"]}
XPP_ROW = {"s": "XPP", "d": ["", "ProShares", "Fund", 1e9, 0, 1.0, 100000, 1, 2.0, 102.0, "fund"]}
def fake_post6(body):
    return {"totalCount": 2, "data": [NVDA_ROW, XPP_ROW]}
p6 = tv.fetch_pulse(post_fn=fake_post6, cap=20)
check("fund excluded", all(m["t"] != "XPP" for m in p6["mega_caps"]))
check("stock kept", any(m["t"] == "NVDA" for m in p6["mega_caps"]))

print("[T23] Movers sorted client-side by magnitude")
ROW_A = {"s": "A", "d": ["", "A", "T", 1e11, 0, 1.0, 900000, 1, 5.0, 105.0, "stock"]}
ROW_B = {"s": "B", "d": ["", "B", "T", 1e11, 0, 1.0, 800000, 1, 9.0, 109.0, "stock"]}
ROW_C = {"s": "C", "d": ["", "C", "T", 1e11, 0, 1.0, 700000, 1, 1.0, 101.0, "stock"]}
def fake_post5(body):
    return {"totalCount": 3, "data": [ROW_A, ROW_B, ROW_C]}
p5 = tv.fetch_pulse(post_fn=fake_post5, cap=20)
check("gainers sorted desc", [m["t"] for m in p5["gainers"]] == ["B", "A", "C"],
      [m["t"] for m in p5["gainers"]])

print("[T24] Engine->briefing integration (schema contract)")
tmp3 = tempfile.mktemp(suffix=".db")
st3 = SQLiteStore(path=tmp3)
ev3 = {"event_id": "evt9", "entity": "NVDA", "tokens_json": json.dumps(["nvidia"]),
       "title": "Nvidia beats estimates", "event_type": "earnings", "status": "active",
       "severity": "High", "confidence": 75, "source_count": 2,
       "assessment": "Strong beat", "what_changed": "new", "urls_json": json.dumps(["http://z/1"]),
       "first_seen": time.time(), "last_updated": time.time(),
       "sentiment": "bullish", "triggers_json": json.dumps(["NVDA", "MK-01 · Mega-Cap Earnings"]),
       "sources_json": json.dumps([{"name": "Reuters", "url": "http://z/1", "title": "Nvidia beats"}]),
       "score": 9}
st3.upsert_event(ev3)
bi = briefing.load_events(st3, 24)
check("briefing consumes engine events", len(bi) == 1 and bi[0]["title"] == "Nvidia beats estimates", bi)
check("triggers flow to theme chart", briefing.theme_counts(bi).get("MK") == 1, briefing.theme_counts(bi))
check("sentiment flows to gauge", "🟢" in briefing.sentiment_gauge(bi), briefing.sentiment_gauge(bi))

print("[T25] Shared market pulse embed honesty")
p_invalid = {"updated": time.time(), "valid": False, "session_open": False,
             "mega_caps": [], "gainers": [], "losers": []}
check("invalid -> grey no-data", market.build_pulse_embed(p_invalid)["color"] == 0x95A5A6)
p_closed = {"updated": time.time(), "valid": True, "session_open": False,
            "mega_caps": [{"t": "NVDA", "pct": 1.0, "relvol": 1.0}], "gainers": [], "losers": []}
check("closed -> previous session label", "previous session" in market.build_pulse_embed(p_closed)["description"])

print("[T26] Percent taken directly from scanner 'change' column")
ROW_NVDA = {"s": "NVDA", "d": [None, "NVIDIA Corporation", "Electronic Technology", 5.26e12, None, 0.9, 96792772, True, -0.9920815509238221, 217.56, "stock"]}
ROW_MOON = {"s": "MRNA", "d": [None, "Moderna", "Health", 1e10, None, 2.0, 5000000, True, 125.0, 45.0, "stock"]}
ROW_MISSING = {"s": "MISS", "d": [None, "Miss", "Tech", 1e9, None, 1.0, 100000, True, None, None, "stock"]}
r1 = tv._row(ROW_NVDA); r2 = tv._row(ROW_MOON); r3 = tv._row(ROW_MISSING)
check("nvda shows -0.99%", r1["pct"] is not None and abs(r1["pct"] + 0.992) < 0.01, r1["pct"])
check("violent move kept uncapped", r2["pct"] == 125.0, r2["pct"])
check("missing change -> None", r3["pct"] is None, r3["pct"])

print("[T27] Strict enum enforcement")
valid_base = {"event": "Fed holds", "event_type": "macro", "facts": ["held"], "assessment": "pause",
         "what_changed": "New event - no prior coverage",
         "importance": "High", "confidence": 80, "sentiment": "neutral", "entities": ["Fed"],
         "tickers": ["NVDA"], "evidence": ["held"], "corroboration": "multi-source",
         "source_reliability": "High", "gaps": []}
bad_evt = dict(valid_base); bad_evt["event_type"] = "merger"
ok, _, _ = main.validate_analysis(bad_evt)
check("event_type enum enforced", not ok)
bad_cor = dict(valid_base); bad_cor["corroboration"] = "partial"
ok, _, _ = main.validate_analysis(bad_cor)
check("corroboration enum enforced", not ok)

print("[T28] Ticker-in-evidence stripping")
good_t = dict(valid_base); good_t["tickers"] = ["NVDA", "FAKE"]
ok, obj, _ = main.validate_analysis(good_t, evidence_text="Nvidia ($NVDA) reported strong earnings.")
check("fake ticker stripped", "FAKE" not in obj["tickers"], obj["tickers"])
check("real ticker kept", "NVDA" in obj["tickers"], obj["tickers"])

print("[T29] Prompt injection shielding structure")
check("system role defined", "EVENT_SYSTEM_PROMPT" in dir(main))
check("xml reports tag used", "<reports>" in main.EVENT_USER_PROMPT)

print("[T30] Score components are tracked for explainability")
i_test = item("NVDA earnings beat", "$NVDA is up")
sc, labels = main.score_item(i_test)
check("components dict exists", isinstance(i_test.get("score_components"), dict))
check("ticker/mover component tracked", i_test.get("score_components", {}).get("ticker", 0) > 0 or i_test.get("score_components", {}).get("mover", 0) > 0)

print("[T31] Deferred state is retriable (not terminal)")
tmp4 = tempfile.mktemp(suffix=".db")
st4 = SQLiteStore(path=tmp4)
st4.register("http://defer", "h_def", "deferred", 4)
check("deferred is retriable", st4.url_active("http://defer"))
st4.register("http://filt", "h_filt", "filtered", 0)
check("filtered is terminal", not st4.url_active("http://filt"))

print("[T32] Multi-signal clustering (ticker + keyword + time)")
i1 = {"title": "Nvidia earnings beat estimates", "source_name": "Reuters", "url": "http://x/1", 
      "ts": time.time(), "source_type": "rss", "text": "", "score": 8,
      "matched_categories": ["NVDA", "MK-01 · Mega-Cap Earnings"], "keyword_ids": ["MK-01"]}
i2 = {"title": "Nvidia reports strong data center demand", "source_name": "Bloomberg", "url": "http://x/2",
      "ts": time.time() + 3600, "source_type": "rss", "text": "", "score": 7,
      "matched_categories": ["NVDA", "MK-01 · Mega-Cap Earnings"], "keyword_ids": ["MK-01"]}
clusters = main.cluster_events([i1, i2])
check("same ticker+keyword clustered", len(clusters) == 1 and len(clusters[0]["items"]) == 2, f"{len(clusters)} clusters")

print("[T33] Anti-drift guard prevents chain-merging")
a = {"title": "Apple iPhone sales strong", "source_name": "Reuters", "url": "http://a/1",
     "ts": time.time(), "source_type": "rss", "text": "", "score": 8,
     "matched_categories": ["AAPL"], "keyword_ids": ["MK-01"]}
b = {"title": "Tech sector earnings overview", "source_name": "Bloomberg", "url": "http://b/1",
     "ts": time.time() + 1800, "source_type": "rss", "text": "", "score": 7,
     "matched_categories": ["AAPL", "MSFT"], "keyword_ids": ["MK-01"]}
c = {"title": "Microsoft Azure cloud growth", "source_name": "WSJ", "url": "http://c/1",
     "ts": time.time() + 3600, "source_type": "rss", "text": "", "score": 7,
     "matched_categories": ["MSFT"], "keyword_ids": ["MK-01"]}
clusters = main.cluster_events([a, b, c])
check("A and C stay separate", len(clusters) >= 2, f"{len(clusters)} clusters")

print("[T34] Time proximity bonus in clustering")
i_old = {"title": "Fed rate decision", "source_name": "Reuters", "url": "http://old/1",
         "ts": time.time() - 86400, "source_type": "rss", "text": "", "score": 8,
         "matched_categories": ["CB-01 · Fed Communications"], "keyword_ids": ["CB-01"]}
i_new = {"title": "Federal Reserve holds rates", "source_name": "Bloomberg", "url": "http://new/1",
         "ts": time.time(), "source_type": "rss", "text": "", "score": 7,
         "matched_categories": ["CB-01 · Fed Communications"], "keyword_ids": ["CB-01"]}
clusters = main.cluster_events([i_old, i_new])
check("24h-apart items cluster with strong signals", len(clusters) == 1, f"{len(clusters)} clusters")

print(f"\nRESULTS: {PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
