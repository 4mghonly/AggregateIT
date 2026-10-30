# B115 — immutable publisher capture, paired editorial decisions and daily evidence

Scope: `rebuild/aggregateit-v2` only, no production/main changes or Discord posts.

## Actual path

1. The existing B80 collector makes its bounded RSS and article HTML requests once, retaining the original bytes **in memory only** until compilation. The B115 comparison replays the exact captured article-attempt set through V1's original deterministic English `main.score_item`/`cluster_events`/front-page controls, and Arabic `arabic_live_v2._item`/`impact_score`/`select`, with V1 source code blob checks and a frozen selection clock. It independently replays those same bytes through the actual V2 `compile_captured_articles` and editorial plan.
2. Every article must match a candidate from the frozen RSS buffer for that publisher; source IDs, hosts, raw hashes, canonical article identities and bounds are checked before comparison. No second publisher fetch occurs for B115. The sanitized receipt gives source-byte digests; V1/V2 selected counts, overlap, V1-only/V2-only article identity hashes; V1 scores/trigger IDs, V2 priorities/topics, Arabic geography and per-item decisions. Selection differences remain evidence, not automatic defects or quality wins.
3. The paired run receipt binds the UTC date, GitHub run ID, branch commit and source manifest digest. Restored receipts remain keyed by run ID **and** date, keeping same-day variants independent. The seven-day summary counts distinct dates once and tracks positive story evidence separately for English and Arabic. GitHub run provenance does not independently prove that publishers authored the content.
4. Existing B83 parser/headline comparison still runs independently and is not counted as B115's same-capture editorial proof. B115 remains a distinct, stricter measurement in the live collector. Old B114 evidence cannot be retroactively converted into B115 evidence.

## Qualification limits

- This compares the bounded article pages the live collector actually attempted, **not all stories on all V1 feeds**. V1 complete source set, social/GitHub ingestion, database-based event history, complete market regime, external LLM analysis/translation, final native rendering and Discord delivery are **not compared**.
- Source-backed article capture is evidence of what the publisher HTML returned, not independent verification of factual truth or legal provenance. Model-free scoring/ranking numbers are not intrinsically comparable scales.
- Genuine seven-day evidence can only accrue through separately observed UTC dates; several successful CI runs on one date still provide one day. The report requires 7/7 distinct dated paired captures and reports 7/7 positive bilingual dates separately. No synthetic dates or backfilling.
- `schedule:` in a non-default GitHub branch does **not** run. A daily **external branch-targeted** workflow dispatch is required until the observation window is complete. The B80 workflow stays `workflow_dispatch`/branch-push only and outbound publishing remains disabled.

## Verification and next gates

- Ten new B115 regressions pass: byte lineage, one shared network capture, deterministic replay, identity refusal, bounded/dated receipts, same-day duplicate guard and seven-day honesty.
- An expanded 631-test V2 discovery run produced six **unrelated** existing errors (missing `langdetect` in this local environment and five outdated B46/B47 renderer mock signatures). These files were not changed by B115; do not report full-suite green.
- Hosted run and daily collection results must be cited by run ID **after completion**. Until then, all B115 real paired days = 0, release HOLD.

Remaining release gates: full actual V1/V2 model/render/delivery parity, genuine seven-day bilingual product evidence, source breadth, LLM failover, visual QA/RTL, independent delivery receipts, resilience and separately approved cutover.
