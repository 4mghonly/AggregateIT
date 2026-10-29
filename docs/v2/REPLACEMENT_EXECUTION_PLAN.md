# AggregateIT V2 — Production Replacement Execution Plan (Option A)
Updated: 2026-10-29. Branch: `rebuild/aggregateit-v2`. **Production remains V1**.

## Goal
Ship a complete, visibly better, operationally reliable replacement for the existing English and Arabic products. "More green workflows" is not an outcome; an English and Arabic edition that is accurate, legible, complete, recovered after a fault, and delivered on the existing routes is the outcome.

## Immutable operator-approved V1 product contract
These specifications were read from `main` and are checked on V2 by `v2_replacement_contract.py`:
- English engine: `.github/workflows/engine.yml` at UTC :07 hourly; canonical event/market state, engine legacy digest delivery off.
- English Gazette: `.github/workflows/slide.yml` at 11:30 UTC / 15:30 UAE; **two pages**, existing `DISCORD_WEBHOOK` and channel validation, existing English LLM primary/fallback and market-refresh dependencies.
- Arabic briefing: `.github/workflows/arabic-scheduler.yml` at 02:00/08:00/14:00/20:00 UTC (06:00/12:00/18:00/00:00 UAE); **three 3840×2160 slides**, existing `DISCORD_WEBHOOK_ARABIC` and channel validation, primary/fallback routing, original Arabic article integrity and attribution rules.
- Market refresh: `.github/workflows/tv_refresh.yml` current Monday, weekday pulse and close slots.
- Backup: `.github/workflows/backup.yml` Sunday 06:00 UTC / 10:00 UAE.
- Unscheduled legacy products are NOT to be activated just to make a V2 parity claim.

## One integrated critical path, not more standalone probes

### 1. Replacement spine: **IMPLEMENTED / HOSTED PASS**
`v2_b46_live_editorial_runner.py` now runs genuine publisher feed -> actual HTML -> article evidence -> original-language editorial compiler -> held five-page render. `SOURCE_CATALOG` in `v2_b46_live_editorial.py` assigns a distinct source ID to every primary/secondary publisher. English BBC -> DW; Arabic Al Jazeera -> BBC Arabic. Fallback executes only when a primary yields zero eligible articles. The evidence compiler independently revalidates the article and does not impersonate another publisher.

Evidence: hosted #40849710796: English 3 articles (BBC), Arabic primary 0 eligible, fallback BBC Arabic 2 eligible, 5 source-backed editorial articles, five 4K pages rendered. `tests/test_v2_replacement_pipeline.py` exercises simultaneous primary outage and independent source identity with captured HTML. **Not a full release test.**

### 2. Intelligence/product parity: **IN PROGRESS — V1 market cache bridge integrated**
A read-only adapter `v2_market_bridge.py` consumes V1's existing TradingView pulse cache, validates freshness and numeric prices, and passes source-labelled observations into the English editorial compiler and held English Gazette. The Arabic financial lane remains prohibited. This does **not** yet supply V1-equivalent market regime analysis, fully tested live provider routing, or source-family corroborated event merging.

Remaining work:
Map the V1 engine's scoring, event lifecycle, deduplication, market/macro context, source family corroboration and actual LLM analysis onto the replacement's editorial plan. Preserve the V1 Gazette and Arabic final-product obligations; do not substitute quote-only laboratory pages for finished analysis. Deduplicate across actual source articles without conflating distinct events. Designate final English and Arabic edition generation as the only product output path. Show unavailable data honestly.

### 3. Final product rendering: **INCOMPLETE**
Replace held laboratory template/content with polished English Gazette (two pages) and Arabic briefing (three 4K slides), including actual facts/citations, separate assessment, region priorities, UAE emphasis, large readable RTL typography and no clipping. Run automated geometry checks **and** inspect the real rendered images. Respect Arabic `PRODUCT_RULES.md`.

#### Actual visual review, not just PNG acceptance
The five 4K held pages from hosted #40850880405 were inspected as a contact sheet on 2026-10-29. They were technically valid, but **not acceptable as final publications**: English pages retain the unverified laboratory masthead and multiple empty market/analysis panels; Arabic pages have large empty panels and text too small relative to the available area. Reuse of V1 market snapshot/chart geometry is being integrated, but editorial summaries, RTL typography and meaningful panel density still require final-product redesign. Do not count this inspection as an independent approval of the final design.

#### Actual V1 cadence caveat
The reviewed successful `main` runs #40733833078 (English Gazette) and #40839644622 (Arabic) had successful cadence jobs but the actual `slide`/`publish` jobs were **skipped**. A green workflow conclusion alone is not a delivery receipt; obtaining successful real V1 edition artifacts/Discord receipts remains part of the true parity baseline.

### 4. Durable operation: **INCOMPLETE**
Persist sanitized evidence, event/market history, 7-day source-backed weekly inputs and recovery snapshots within a zero-paid-resource budget. Integrate V1's proven cache/SQLite/market refresh and alerting where appropriate. Verify restore, bounded cleanup, duplicate-run guards, source failover, LLM primary/fallback, missed-job detection and Discord delivery rehearsal without using production routes.

### 5. Production-grade V1/V2 shadow comparison: **INCOMPLETE**
Run V2 at the same **logical** edition slots with outbound publishing disabled; test a minimum of seven distinct qualifying dates. Compare story selection, timestamps, factuality, Arabic/English quality, design, market analysis, actual source recovery, LLM recovery, engine health and run costs. Publish a comparison report with evidence and unresolved gaps.

### 6. Controlled production swap: **NOT AUTHORIZED YET**
Require all critical gates green and a separate final production cutover approval. Back up state and V1 configuration; wire V2 to the **same** V1 schedules and Discord destinations; disable corresponding V1 senders atomically; confirm first live receipts; retain tested V1 rollback. Never allow both versions to publish to the same destination in the same slot.

## Definition of done / release gates
- Both languages have source-backed complete editions, not headline-only/synthetic or empty editions.
- Primary-source and primary-LLM outage each have independently observed recovery/degradation evidence.
- Actual English and Arabic editions demonstrably improve clarity, selection and accuracy against V1; regional coverage is reported honestly rather than invented.
- Schedules, webhook variables, channel validation, output count, and production continuity checks match V1 until approved cutover.
- Image readability/RTL/clipping reviewed; manual image QA cannot be replaced by checking PNG dimensions.
- Real persisted history and safe restore; true seven distinct days and weekly edition generation.
- Test-only Discord delivery, idempotency/alerts, and production rollback rehearsal pass.
- Zero paid resources unless operator separately authorizes an exception.
- Production/main preserved during development; all test routes remain NO-POST.

## Workflow discipline
1. Modify the actual integrated execution path or output; avoid proliferating diagnostic modules.
2. Add a focused regression for the real failure, run it, then run ONE hosted integrated acceptance suite.
3. Keep tracker/handoff short, cite commit and hosted evidence, and do not call source-feed availability a completed editorial product.
4. Stop only on a genuine blocker or required operator decision, then present a short options/recommendation.
