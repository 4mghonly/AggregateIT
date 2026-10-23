# AggregateIT V2 — Master Rebuild Plan
Date: 23 October 2026 (UAE)  
Status: isolated program plan; NOT approved for production cutover  
Original production baseline: main @ 6deea127bbbd645cc5a4969a5397e745839a95ce  
Working branch: rebuild/aggregateit-v2

## Decision and rationale
Recommendation: progressive modular replacement (strangler approach) under one evidence contract, not a wholesale one-shot rewrite. The evidence already indicates independent failures in source freshness, model outputs, editorial selection, layout readability, state durability and publication monitoring. A full rewrite before comparison would discard working collectors, market logic and confirmed Discord receipts; patching only presentation would preserve quality defects.

Alternatives:
1. Keep patching main: fastest emergency recovery, but fragmented registries and end-to-end observability remain.
2. Isolated V2 pipeline with reusable adapters (SELECTED): measurable improvements, reversible, current production continues.
3. Clean-sheet replacement in one cutover: maximum design freedom, highest regression and rollback risk; reject until V2 proves superior.

## Product boundaries
- English: market/geopolitical/finance intelligence, two-page Gazette; preserve observed data vs assessment and avoid investment advice.
- Arabic: geopolitical/security command brief, three pages, full target geography and UAE-first intelligence where supported; no unrelated financial/lifestyle stories.
- One evidence/event substrate, TWO independent editorial selection and presentation policies.
- Product answers: what happened, what changed since prior edition, which independent sources support it, what is uncertain, what to monitor.
- Human-readable sourced claims; do not create new facts by translation, analysis, or page design.
- Low cost and provider independence. Source rights, licensing and terms are checked before collection or redistribution.

## Non-negotiable controls
1. Do not edit or merge production main, Arabic production branches, schedules, GitHub Actions secrets, Discord webhooks, or Cloudflare deployment during B0-B7.
2. No new production posts, workflow dispatch, credential probing, paid APIs/infrastructure, or scheduled GitHub Actions in the rebuild branch.
3. Record branch/head, raw evidence links, focused test results, failures, costs, and handover after each batch.
4. Preserve current English and Arabic cadence/recipient separation until explicit B8 approval.
5. Do not infer quality from a successful workflow status. Separate delivery, timeliness, coverage, evidence integrity, language completeness, analysis health and visual legibility.
6. Synthetic fixtures and shadow output must be conspicuously labelled; no synthetic facts enter live intelligence.
7. Keep existing collectors/readable logic as candidates for selective reuse, subject to license, correctness and measured comparison.

## Target architecture
1. Source Registry: origin/family, languages, region, rights, adapter, freshness, health history, quarantine and independent alternate.
2. Collection: bounded per-source retries, normalization, immutable article ID/URL/timestamp/original text, adapters with outcome codes.
3. Evidence Core: immutable excerpts and claim links, cross-language event identity, clustering, dedup, independent-source corroboration, lifecycle.
4. Editorial: deterministic geography/relevance/recency/admission plus LLM-only structured interpretation/translation where justified.
5. Product renderers: strict Arabic and English page contracts; adaptive text-fitting and density caps; LLM NEVER chooses coordinates or page geometry.
6. Quality Gates: schema, exact citations, geography, discrepancy checks, bilingual completeness, layout/RTL/font snapshots.
7. Delivery ledger: schedule slot -> edition ID -> accepted render -> single Discord receipt; observability with one error budget per product.
8. Durable state: choose based on evidence, operational cost and rollback; no database vendor decision in B0.

See ARCHITECTURE_V2.md for schemas and trust boundaries.

## Delivery batches
| Batch | Objective | Exit gate | Dependencies |
| --- | --- | --- | --- |
| B0 — Foundation | Pin production baseline, branch isolation, current architecture and quality rubric, synthetic comparison fixtures, tracker/handoff | All documentation and fixture contracts committed on isolated branch; main unchanged | None |
| B1 — Reliability | Diagnose/repair route failures offline; bounded retries, circuit breaker, structured result classification, audit dependency parity | Deterministic failure-path tests for 403, blank/truncated JSON, timeout, omitted regions; no Discord posts | B0 |
| B2 — Sources | Unified English/Arabic registry, adapter and freshness probes, rights/independence, country floors and alternate-source policy | Evidence-backed inventory and >=2 usable independent families per target region, >=3 for priority UAE/GCC where available; explicitly mark gaps | B1 |
| B3 — Intelligence | Stable article/claim/event IDs, source excerpts, event lifecycle, multilingual clustering and delta persistence | Realistic golden cases prove provenance and dedup; no headline evidence mismatches | B2 |
| B4 — Editorial | Separate product policies and schema-validated LLM translation/assessment; deterministic non-inventive degraded mode | Golden bilingual/editorial tests and explicit abstention behavior pass | B3 |
| B5 — Design | Deterministic command brief/Gazette system with responsive typography, RTL, stable templates and page budget | All golden renders pass clipping, readability, attribution and single-development checks at Discord viewing scale | B4 |
| B6 — Operations | Durable state, scheduler idempotency, source health, semantic publication gates, delivery receipts, alerts and rollback | Fault-injection across missed schedule, partial collection, duplicate trigger and Discord uncertainty | B3-B5 |
| B7 — Shadow comparison | Run isolated V2 with comparable source windows and zero production delivery | Predeclared quality gates met over representative cycles; costs and regressions documented | B6 |
| B8 — Controlled migration | Explicit owner-approved production cutover with canary, receipt reconciliation and rollback | Canary meets goals; rollback rehearsed; owner approves | B7 + separate authorization |

## Provisional measurable acceptance criteria
Baselines are incomplete; these are design targets, not claimed present behavior.
- >=99% on-time **accepted and receipt-confirmed** scheduled editions over >=60 eligible slots, excluding documented platform-wide outages; separately report degraded editions.
- 100% of published factual assertions linked to exact article and supporting excerpt; unsupported claims rejected.
- 100% of published headlines aligned with their factual first sentence; ambiguous sources attributed.
- Source coverage: >=2 independently operated usable publishers per target region, >=3 for UAE/GCC; no silent masking of gaps. Freshness must be measured, not inferred from HTTP 200.
- Translation: >=98% of selected non-Arabic articles either accurately translated by the edition deadline or explicitly rejected with a reason; report both translated yield and selection attrition to prevent gaming.
- Layout: no material clipping, overlap, missing-glyph rendering, or unreadable secondary text at tested Discord preview size. No repetition of a single development across news slots.
- Publication idempotency: one confirmed Discord message per product/slot, including all pages; ambiguous receipts treated as unknown and reconciled before retry.
- Model availability is not a release gate if explicit verified facts can be published in a labelled degraded mode; analytical claims are withheld when validation fails.

Quality goals must be tested on sufficient dates, languages, sources and source outages; green unit tests alone do not establish operational reliability.

## Promotion / stop rules
- End each batch with exact commit SHA, changed files, tests, sample outputs, unresolved risks, cost and updated HANDOFF.
- Stop on secrets, legal/rights uncertainty, protected workflow changes, irreversible schema decisions or paid dependencies.
- Never mark B7 acceptance based only on synthetic fixtures; maintain a frozen current-production comparison.
- B8 is a separate decision after the measured comparison. No automatic branch merge or auto deployment.

## Accepted analytics-storage amendment (23 Oct 2026)
Add a dedicated, free-tier-bounded telemetry store and operator dashboard. Cloudflare D1 Free is the provisional backend; PocketBase remains a self-hosted alternative, not a dependency. Telemetry is separate from raw article/evidence storage. Record ingestion/probe outcomes beginning in B1/B2, then deploy and activate retention only in B6 with independent approval. Enforce internal limits lower than D1 Free caps (250 MB warning, 300 MB optional-detail throttle, 350 MB analytics write stop, 20k writes/day, 250k rows scanned/day). Roll up detail, dry-run deletion first, and never delete existing raw source/evidence. Manual export to Google Drive and restore validation are required before live retention. Full policy: ANALYTICS_STORAGE_POLICY.md.
