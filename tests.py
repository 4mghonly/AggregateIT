"""Correctness baseline for AggregateIT POC. Run: python tests.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main

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

print(f"\nRESULTS: {PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
