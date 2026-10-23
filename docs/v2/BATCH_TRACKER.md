# AggregateIT V2 — Batch Tracker
Working branch: rebuild/aggregateit-v2  
No production integration before owner-approved B8.

| Batch | State as of 23 Oct 2026 | Evidence and exit gate |
| --- | --- | --- |
| B0 Foundation | COMPLETE — seven planning/fixture files committed and verified | MASTER_PLAN_V2, QUALITY_BASELINE, ARCHITECTURE_V2, fixtures, HANDOFF, branch/base comparison |
| B1 Reliability | PARTIAL — isolated code/test package, 10 offline regressions passed; installed/e2e tests pending | Route failover, safe diagnostics, audit dependency/isolation, degraded-state marking; B1_RELIABILITY_REPORT.md |
| B2 Source inventory | PARTIAL — offline joint snapshot and 14 stdlib tests PASS; live health, rights and family verification pending | 222 records, 8 cross-product duplicate feeds, 18 region snapshots, 4 dated-freshness deficits plus UAE-host gap; B2_SOURCE_INVENTORY_REPORT.md |
| B3 Evidence core | PARTIAL — in-memory evidence/claim/event contracts and 19 synthetic regression tests PASS; integration/durable provenance pending | v2_evidence.py, tests/test_b3_evidence_core.py, B3_EVIDENCE_REPORT.md |
| B4 Editorial engines | NOT STARTED | Structured Arabic and English editor, cross-lingual QA, abstention contract |
| B5 Layout | NOT STARTED | Preview-scale screenshot suite, typography/RTL, fixed page count with no clipping |
| B6 Operations | NOT STARTED | Durable scheduling, receipts and semantic health, fault-injection and rollback |
| B7 Shadow | NOT STARTED | Same-window scorecard, no real Discord publishing |
| B8 Cutover | BLOCKED — requires user approval | Canary, successful SLO, migration and rollback |

## B0 acceptance checklist
- [x] Review main branch/file inventory, schedules, source audit, recent workflow evidence.
- [x] Select a separate branch directly from pinned production main.
- [x] Select progressive modular replacement and spell out reject alternatives.
- [x] Define quality measures and observed vs unknown categories.
- [x] Commit isolated documents and synthetic fixtures.
- [x] Verify branch ancestry and that diff contains ONLY docs/fixtures (ahead by one at evidence commit 21380a6e).
- [x] Verify JSON structure, declared decisions, eight synthetic fixtures and unique IDs; no runtime tests claimed.
- [x] Verify main still at pinned 6deea127 at closure, with no V2 production edits.

## B1 planning and work packages (next)
1. B1a characterize response handling: primary/fallback 403, invalid/truncated/empty, timeouts and success; add deterministic test fixtures and no-live-call harness.
2. B1b close scoped route robustness gaps with provider-independent circuit/timeout and error metadata. No model-change directive or new key.
3. B1c repair English audit missing dependencies and separate audit result from registry-write state (in isolated branch only).
4. B1d characterize Arabic translation selection/budget, prevent silent geographic loss, preserve original-language provenance.
5. B1e run focused tests and an isolated read-only simulated briefing; present failures before B2.

## Change log
- 23 Oct 2026 — B0 started and current-production baseline pinned; no production changes authorized.

## B0 verification record
- Branch initial evidence commit: 21380a6e5721ad7793a793d58a8ca2290dee8bf9, parent 6deea127; seven added files, zero modifications or deletions; main unchanged at verification.
- Remote fetch content comparison for plan and fixture: exact match; fixture JSON parsed, unique B0-01..B0-08, all have supported expected decisions.
- Branch-specific GitHub Actions runs: 0 at verification. No production run, Discord delivery, model call, or paid resource was triggered by this batch.
- These are static contract checks, NOT end-to-end simulation or B1 behavior evidence.

## Accepted analytics amendment — 23 October 2026
- B1: specify structured telemetry events and simulate budget/overflow handling offline; no D1 resources yet.
- B2: source freshness and regional coverage metrics become the first dashboard datasets.
- B3–B5: append evidence/editorial/translation/layout measurements; separate analytics outage from product failure.
- B6: build free-tier D1 ingestion and read-only dashboard, with daily dry-run cleaning first; gated live retention and manual export/restore after explicit approval.
- B7: compare V1/V2 using the same definitions and captured denominators.
- Account-level cost and storage gates: see ANALYTICS_STORAGE_POLICY.md. No database, Cron trigger or deletion has been enabled by this amendment.

## B1 package record — 23 October 2026
- Source edits: `llm.py`, `arabic_newsletter/editor.py`, `arabic_newsletter/run.py`, `audit.py`, `.github/workflows/audit.yml`.
- New contracts/tests: `v2_route_health.py`, `tests/test_b1_reliability.py`, `docs/v2/B1_RELIABILITY_REPORT.md`.
- Offline test result: 10/10 focused Python unittest cases PASS, with in-memory mocked network and stubbed unavailable external imports; no installed-dependency or end-to-end run claimed.
- Main, production schedules, DB, Actions and Discord untouched. B1 remains PARTIAL until an isolated dependency-installed suite and no-post product rehearsal pass.

## B2 inventory package record — 23 October 2026
- Versioned joint source snapshot in `config/v2/source_registry.json` from the three historical source-of-record inputs; 104 English + 118 Arabic = 222 stable IDs.
- Cross-product duplicate feed URLs identified (8). HTML adapters with no dated recent entries never count toward dated freshness; independent publisher families/rights stay explicitly unverified.
- Coverage analysis: historic dated recent count below provisional target in Somalia, Yemen, Egypt and Jordan; UAE has only two distinct dated host candidates vs target of three independent families.
- Standalone `v2_sources.py` validator and 14 Python stdlib regression tests passed in an in-memory session; branch-file test after publish still to confirm. No HTTP probes or external writes.
- B2 gate remains PARTIAL until bounded live compatibility/freshness, editorial-source rights and publisher independence review succeed. B3 isolated evidence schema prototyping may proceed without interpreting B2 as complete.

- Follow-up evidence (main audit bot @ c7a53e9, 2026-10-23 06:02 UTC) copied as a **branch-local audit update**. Historical compatible 61/118, dated-recent 52/118. Latest dated-freshness gaps are Somalia, Yemen, Egypt, Jordan, plus UAE-country publisher-host candidate deficit; B2 acceptance unchanged (partial).

## B3 isolated evidence prototype — 23 October 2026
- Added `v2_evidence.py`: deterministic article/revision/observation/excerpt/claim/event identities, explicit close/delta handling, source-span and record-integrity checks, and unverified translation candidate linkage. Does not collect, store, classify language or call models.
- `tests/test_b3_evidence_core.py`: 19/19 synthetic standard-library tests PASS in an in-memory Python runtime; no installed full suite claimed. B3 remains PARTIAL until real source-grounded integration and append-only verification.
