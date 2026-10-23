# AggregateIT V2 — Batch Tracker
Working branch: rebuild/aggregateit-v2  
No production integration before owner-approved B8.

| Batch | State as of 23 Oct 2026 | Evidence and exit gate |
| --- | --- | --- |
| B0 Foundation | COMPLETE — seven planning/fixture files committed and verified | MASTER_PLAN_V2, QUALITY_BASELINE, ARCHITECTURE_V2, fixtures, HANDOFF, branch/base comparison |
| B1 Reliability | PARTIAL — 178/178 installed V2 tests PASS and 55/55 Arabic app tests PASS after explicit V2-only legacy-contract reconciliation; actual Arabic synthetic long no-send CLI passed | Main had 14 identical original failures; V2 adjusted obsolete fixtures/expectations without changing sender/workflow or relaxing geography/review; genuine content and service e2e pending |
| B2 Source inventory | PARTIAL — 222-record ledger unchanged; robots-first capped candidates plus Global Voices CC BY Arabic candidate reviewed; 0 registry/family promotions | Global Voices Arabic feed available but 96k truncated sample showed 6–11 Oct only (not current); media-specific rights and policy-link caveat; B1_B2_B3_B5_CONTINUATION_2026-10-23.md |
| B3 Evidence core | PARTIAL — local POSIX exclusive writer + atomically persisted independent head receipt + nine fault/lock tests PASS; authenticated publisher/off-host receipts pending | v2_evidence_store.py, tests/test_b3_exclusive_store.py, file-backed journal tests; manual reconciliation on journal/receipt split |
| B4 Editorial engines | PARTIAL — native-language admission checks pass; English-only Ammon and Somali/English Radio Ergo cannot satisfy Arabic-native floor without validated translation | v2_editorial.py; source language evidence recorded, no live extraction or translation fidelity proof |
| B5 Layout | PARTIAL — actual Arabic three-page long sample CLI and visual inspection; UAE headline contrast improved from 2.17:1 to 4.79:1; 3 contrast/sample-marking regression cases PASS | Sample footers visibly marked synthetic; DejaVu fallback only; Noto/Siraj deferred, mobile-scale dense cards remain a quality gate; B1_B2_B3_B5_CONTINUATION_2026-10-23.md |
| B6 Operations | PARTIAL — 12 analytics plus 6 no-network receipt-gate tests PASS | v2_analytics_controls.py, v2_delivery_gate.py; no D1, durable sender/scheduler or deletion |
| B7 Shadow | PARTIAL — 7 deterministic same-window comparison tests PASS; live captures unavailable | v2_shadow_scorecard.py; no real V1/V2 shadow execution or Discord publishing |
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

## B3b in-memory referential ledger — 23 October 2026
- `v2_evidence_ledger.py`: bounded observation graph, append-only event revisions, idempotent registration, strict source-revision/excerpt/claim/event reference checks, and explicit-only contradiction/correction relations.
- Excerpt identity now includes source ID to preserve dual English/Arabic collector provenance; core 19/19 retested, ledger 15/15 passed in isolated Python 3.12.
- B3 still PARTIAL: memory-only; no replay/persistence, rights-cleared authentic fixture, full collector integration or publisher ownership attestation.

## 23 October 2026 — B3c/B4/B5a/B6a isolated continuation
- Added source-bound journal replay, separate editorial admission policies, fixed-page layout budget prototype and fail-closed no-resource analytics budget/retention preview.
- Focused offline result: **83/83** Python unit cases PASS (34 existing + 14 journal + 15 editorial + 8 layout + 12 budget). All cases synthetic, all modules executed from in-memory source; not installed full suite or production e2e.
- Exact files and remaining acceptance gates: `docs/v2/B3_B6_OFFLINE_BATCH_REPORT.md`.
- No main updates, scheduled workflows, model/source/network requests, Discord, D1, PocketBase, Drive backup, data deletion or paid resources.

## B6b/B7a no-post continuation — 23 October 2026
- Added product/slot receipt state machine with symbolic English/Arabic destination separation and ambiguous-send retry refusal, plus same-window multi-metric quality scorecard with explicit geographic losses.
- Combined focus run 96/96 synthetic in-memory Python unittests PASS. Details: `docs/v2/B6_B7_NO_POST_REPORT.md`.
- Real receipts, time-window captures, durable transactions, deployment, source-quality proof and B8 cutover remain explicitly pending.

## B2 source gate + B3–B7 integrated NO-POST continuation — 23 October 2026
- Added `v2_source_gate.py`, `v2_offline_rehearsal.py`, `tests/test_b2_source_gate.py`, `tests/test_b3_b7_offline_rehearsal.py` and `docs/v2/B2_B7_OFFLINE_INTEGRATION_REPORT.md`.
- **117/117** focused B3–B7/B2-gate synthetic Python `unittest` cases passed in an in-memory execution; includes 11 genuine module-collaboration rehearsal cases and 10 source-triage cases. Previous source-reconciliation and B1 isolated tests were not rerun in this combined count.
- B2 gap candidates: Somalia only one compatible dated source, Yemen/Egypt/Jordan one each with one stale alternative, UAE two dated hosts. All live current checks, usage rights and independent publisher families UNVERIFIED. No source probe executed.
- Offline bilingual fixture passes evidence → journal replay → distinct English/Arabic editorial admission → immutable layout → fail-closed analytics → unsent delivery reservation. Persian without verified native translation is explicitly withheld. No live model, source, storage, publishing or real E2E verification.
- **Status unchanged:** B1–B7 PARTIAL; B8 BLOCKED. File-backed crash tests, dependency-installed no-post run, publisher rights, language fidelity, rendered-slide QA, durable delivery and same-window genuine shadow remain gates.

## B5b in-memory bilingual raster preview — 23 October 2026
- New `v2_raster_preview.py` and 8 Pillow/RAQM pixel-geometry/regression tests; **125/125** current offline tests PASS when combined with the B3–B7 + B2 source-gate suite.
- Actual 3840x2160 Arabic (3) and 2480x3508 English (2) PNG bytes and smaller scale previews generated **in memory only**. One-item synthetic layouts visually inspected at reduced scale; Arabic six-card synthetic stress fixture passes without clipping; missing fonts/overlong tokens fail closed.
- DejaVu Sans was used because Siraj Noir is absent; no genuine article text, release font, authentic screenshot/Discord delivery proof, user-approved legibility QA or production rendering. B5 still PARTIAL. See `docs/v2/B5_RASTER_NOPOST_REPORT.md`.

## B6c SQLite metadata lab and backup/retention rehearsal — 23 October 2026
- Added `v2_analytics_sqlite_lab.py`, `tests/test_b6_sqlite_lab.py`, `docs/v2/B6_SQLITE_NORESOURCE_REPORT.md`; parameterized SQLite **`:memory:` only**, no external persistence.
- Approved telemetry is keyed/idempotent, independently grouped by English/Arabic. Unknown free-tier account headroom prevents writes; policy at 250/300/350 MB and daily 20k/250k app limits exercised with synthetic usage; all real D1 usage remains unknown.
- Local JSON+SHA-256 export/restore and 30-day detail retention **DRY_RUN_ONLY** work without SQL delete, Cron, Drive, D1 or Cloudflare. Two genuine synthetic pipeline telemetry records survive the in-memory roundtrip.
- 13 new SQLite cases; combined B2/B3–B7/B5/B6 focused tests **138/138 PASS**. B6 PARTIAL until approved D1 resources, actual quotas/remote parity, durable receipts, authenticated dashboard and independently tested backup/restore. Production/Drive/cleanup unchanged.

## 23 October 2026 — B1/B2/B3/B4 installed and bounded external evidence
- Isolated branch checkout `0f252ce`, Python 3.12 virtualenv with both declared requirements files. `python -B -m unittest discover -s tests -p 'test_*.py' -q`: **162/162 PASS** (B1–B7 focused suite; no live application call).
- Separate pre-existing Arabic suite `python -B -m unittest arabic_newsletter.test_arabic -q`: **41 PASS / 11 FAIL / 3 ERROR** on V2. Same **exact 14 named failures/errors** reproduced on unchanged main `c7a53e9`. Not a newly observed V2 regression, but still a B1 release blocker. Do not blanket-ignore failures.
- B3 disposable real-file `fsync`, replay, partial-frame rejection and external-head receipt proof: **4/4 PASS**; persisted as `tests/test_b3_file_backed_recovery.py`. No exclusive multi-writer, power-loss fault injection, crash-atomic receipt storage or production storage proof.
- B2 bounded robots-first metadata samples: `ar-s056` Radio Ergo RSS HTTP 200, 10/10 entries sampled and 3 dated within 72h; `ar-s108` Masrawy RSS HTTP 200, 10 entries and 0 dated; `ar-s082` South24 HTTP 200 HTML, **not RSS**. `ar-s081`, `ar-s101`, `ar-s070` were not fetched because robots unavailable. Max 96,000 bytes per candidate feed; no article bodies persisted.
- Official terms: `ar-s017` The National, `ar-s118` Abu Dhabi Media Office and `ar-s046` Mada Masr have material automated-use/republishing restrictions; excluded from direct feed probes, permission required before proposed reuse. No source family or publication license certified.
- B4: official Ammon English edition, Radio Ergo Somali/English publisher sections; current source counts cannot be treated as Arabic-native coverage. Do not infer native language from registry stream field or substitute machine translation without source-linked quality proof.
- Evidence: `docs/v2/B1_B4_INSTALLED_SOURCE_REVIEW_2026-10-23.md` and `config/v2/source_probe_review_2026-10-23.json`. B1–B7 remain PARTIAL; B8 BLOCKED. No CI dispatch, webhook, source promotion, deletion, DB provisioning, production/main edits or paid model calls.

## 23 October 2026 — B5 direct production-renderer NO-POST pass
- After `54dd93a` checkpoint, directly invoked `gazette_render.render_p1/render_p2` with wholly synthetic, stamped sample data: 2 actual English PNGs, 3840×2160 RGBA each; no `slide.py` entry point invoked, so no collect, analysis, model or Discord.
- Directly invoked `arabic_newsletter.render.render` with `sample.fixture(long=True)`: 3 actual Arabic PNGs, 3840×2160 RGB, renderer `clipped=0`, all in disposable `/tmp` with no Discord.
- Local system has no approved production Noto Sans Arabic; fallback DejaVu was used. Render completion and internal clipping counter are not visual legibility or genuine news-content QA; still B5 PARTIAL. Report `docs/v2/B5_ACTUAL_NOPOST_RENDER_2026-10-23.md`.

## 23 October 2026 — substantial B1/B2/B3/B5 continuation on isolated V2
- At start, `rebuild/aggregateit-v2` remained at `f6650c1`; main unchanged at `c7a53e9`; branch Actions runs zero. Disposable separate checkout + dependency-installed Python 3.12; no main or webhook activity.
- Reconciled the prior **14 identical main-and-V2 Arabic test failures** against current safety contracts **without changing the sender or production workflow**: eight editorial fixtures, three one-message/ambiguous-timeout expectations, source retry cap, scheduled branch assertion, 10-card layout. **Arabic app suite 55/55 PASS.** All editorial validation and ambiguous-network refusal gates remain strict.
- Actual Arabic `--sample --long`, without `--send`, completed `render/ok`, three 3840×2160 PNGs and zero shortened blocks; no model, live collector or Discord call.
- New local POSIX single-writer journal store with cooperative flock, fsynced journal and crash-atomic independently checksummed receipt, strict replay and fail-closed split-brain refusal. **9/9** new B3 lock/fault tests pass including separate process and injected receipt failure. No off-host attestation, publisher provenance, power-loss proof or automatic repair.
- B2 first-party Global Voices Arabic CC BY candidate (excluding third-party media unless independently licensed) verified via publisher policies and one robots-allowed capped RSS metadata sample; **not recent**, 96k partial feed, no promotion or rights blanket clearance.
- B5 visually inspected synthetic Arabic pages; UAE small headline color contrast **2.17:1 → 4.79:1**, three explicit contrast/sample-marking tests, no font policy decision. All sample pages now identify synthetic non-news in the footer. The second-page ten-item density at reduced/mobile viewing remains a QA concern.
- `python -B -m unittest discover -s tests -p 'test_*.py' -q`: **178/178 PASS** (after all continuation edits). Reports and run details in `docs/v2/B1_B2_B3_B5_CONTINUATION_2026-10-23.md`. B1–B7 PARTIAL, B8 BLOCKED; no live resources, production, main, CI dispatch, Discord, deletion or paid calls.
