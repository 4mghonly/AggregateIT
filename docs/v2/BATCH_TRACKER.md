# AggregateIT V2 — Batch Tracker
Working branch: rebuild/aggregateit-v2  
No production integration before owner-approved B8.

| Batch | State as of 23 Oct 2026 | Evidence and exit gate |
| --- | --- | --- |
| B0 Foundation | IN PROGRESS — docs and fixtures prepared, publication/verification pending | MASTER_PLAN_V2, QUALITY_BASELINE, ARCHITECTURE_V2, fixtures, HANDOFF, branch/base comparison |
| B1 Reliability | NOT STARTED | Offline route/error tests; translation budgets; audit dependency fix; no live calls or posts |
| B2 Source inventory | NOT STARTED | Versioned joint registry, validated publisher independence, freshness/rights/region floor |
| B3 Evidence core | NOT STARTED | Article/excerpt/claim/event provenance and stable delta regression |
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
- [ ] Commit isolated documents and synthetic fixtures.
- [ ] Verify branch ancestry and that diff contains ONLY docs/fixtures.
- [ ] Verify JSON schema structure and uniqueness of fixture IDs.
- [ ] Verify main still points to unchanged base (it may independently advance via source bot; compare against pinned SHA, do not alter).

## B1 planning and work packages (next)
1. B1a characterize response handling: primary/fallback 403, invalid/truncated/empty, timeouts and success; add deterministic test fixtures and no-live-call harness.
2. B1b close scoped route robustness gaps with provider-independent circuit/timeout and error metadata. No model-change directive or new key.
3. B1c repair English audit missing dependencies and separate audit result from registry-write state (in isolated branch only).
4. B1d characterize Arabic translation selection/budget, prevent silent geographic loss, preserve original-language provenance.
5. B1e run focused tests and an isolated read-only simulated briefing; present failures before B2.

## Change log
- 23 Oct 2026 — B0 started and current-production baseline pinned; no production changes authorized.
