# AggregateIT V2 — B115 closure and B119 release-readiness audit

Date: **2026-11-05 UTC**. Branch: `rebuild/aggregateit-v2`. Read-only references: original V1 files on the comparison branch; **no main/production changes**. Release: **HOLD**.

## Delivered repairs

1. Commit `2d01b95e`: removed the simultaneous rendering directory collision. Native rendering uses an isolated temporary directory when a four-product archive is also required; the final five PNGs are retained in the expected archive root. Replaced destructive red header overlay with a separately reserved band preserving the complete original masthead and footer, using uniform scaling to preserve proportions.
2. Commit `53731976`: extended B115 same-capture receipts with safe per-article V2 selection-stage, reason and preselection-rank diagnostics. No publisher body, title or URL text is persisted in the paired receipts; all decisions remain hash-bound and no evidence gate is loosened.
3. Commit `e5a40056`: added B119 independent, fail-closed release-readiness audit, explicitly separating B115 dates, fixed-commit stability, V2 held rendering, B95 history, V1/V2 models, weekly reports, visual review and delivery.

## Evidence and test results

- [Original seven-date B115 collection, 5 Nov](https://github.com/4mghonly/AggregateIT/actions/runs/41966028138): seven consecutive UTC dates (30 October–5 November), each with positive V2 English and Arabic stories in one same-capture run. These dates span **different candidate commits**.
- [Reproduction tests, failed as expected](https://github.com/4mghonly/AggregateIT/actions/runs/41968463373): isolated combined rendering and masthead preservation failures.
- [Fixed rendering and four-product workflow](https://github.com/4mghonly/AggregateIT/actions/runs/41968702694): successful; five genuine 4K PNG pages archived, two English and three Arabic; native and four-product receipts present; no Discord posts.
- [Article-level diagnostics verified](https://github.com/4mghonly/AggregateIT/actions/runs/41969416456): successful; per-article capture identity hashes, extraction/relevance/selection stage and rank recorded.
- [B119 release-readiness matrix](https://github.com/4mghonly/AggregateIT/actions/runs/41969866264): successful; **HOLD**; 5 diagnostic gates passed and 9 release-relevant gates outstanding.

### Editorial-selection investigation

The audited seven date-specific run samples contained **15 English and 39 Arabic selection disagreements**. These totals represent distinct captures on each date, not model-quality measurements.

The enhanced 5 November same-capture run explains V1-only omissions without revealing text. In English, the two omitted V1 selections were admitted but ranked 7 and 8 outside the six-story V2 budget. In Arabic, V1-only omissions included article-body containers missing, ungrounded geographic attribution, editorial relevance rejections and a rank/diversity/page-budget exclusion. A reader cannot infer from identity hashes whether rejected titles were material or factually reliable. Do **not** relax body, geography or provenance gates merely to increase raw V1 agreement.

### Visual and delivery findings

The archived V2 pages now preserve their original top and bottom content; the objective 4K, PNG, SHA-256 and no-post warning checks pass. Their readability and Arabic layout still require independent human review at the intended display size; original V1 same-slot images were **not** available for parity. The English layout is comparatively dense and Arabic panels have uneven information density. All Discord packets are held synthetic previews; no live delivery or rollback equivalence is established.

### History semantics

Current B95 restore reports no conflicting hashes **within its bounded restored sample** but is not a complete seven-day authentic B95 history. Previously recorded 30 October B95 receipts contained different hashes for the same story counts; no receipt was deleted, discarded, altered or promoted to reconcile that discrepancy. B115 positive-date evidence remains valid independently of B95.

## Remaining release gates — explicit HOLD

1. **Fixed-SHA stability:** gather seven consecutive genuine UTC bilingual-positive dates on the same final candidate commit; do not backfill and do not count multiple runs on one date.
2. **Authentic weekly products:** generate English and Arabic seven-day weekly reports from authenticated persisted daily plans, not a one-day stand-in; verify both HTML and PDF and real publisher-source references.
3. **Editorial adjudication:** review V1-only and V2-only story selections against safely accessible original source evidence with expert relevance labels. Expand supported article-body extraction only when real publisher HTML patterns justify it; preserve factual gates, attribution and country-grounding rules.
4. **Full V1/V2 model and fallback:** execute comparable, frozen-input and history-aligned V1/V2 editions on a separately authorized, capped model environment; independently assess English, Arabic, translation, fallback, analysis quality, omissions, hallucinations, latency and cost. The no-post workflow sets LLM credentials to empty, so it cannot truthfully pass these gates.
5. **Visual parity:** obtain immutable same-slot V1 rendered pages and V2 pages; independently inspect fonts, RTL, clipping, readability, chart labels, empty-space use and page counts. Hash validity is insufficient.
6. **Delivery and rollback:** evaluate exact V1/V2 destinations, cadences, payloads, size limits, idempotency, retries and rollback using mocks first. Independently authenticated live receipts require separate explicit publication authorization; do not post in this acceptance workflow.
7. **B95 historical integrity:** reconcile or quarantine contradictory old same-day receipts with independently evidenced source lineage; never retroactively replace, synthesize or backfill dates.
8. **Publisher rights/provenance:** verify permission, publisher attribution, rights to render quotes and independent factual quality prior to production release.
9. **Owner decision:** obtain explicit owner cutover approval after every evidence gate passes; existing code must remain fail-closed.

## Safety and authority

Only `rebuild/aggregateit-v2` was modified. No main/production files, scheduled delivery, database provisioning, paid model calls, credentials or Discord messages were changed or used. The acceptance workflow retains empty model and Discord credentials and cannot grant release. Never treat B49 parser/headline equality or B115 positivity as full editorial-model, visual or delivery parity.

**Acceptance decision: HOLD. The software defects are corrected and test-proven; the remaining external/realtime evaluation scope is not complete.**
