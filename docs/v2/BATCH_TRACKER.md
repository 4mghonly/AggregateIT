# AggregateIT V2 — Batch Tracker
Working branch: rebuild/aggregateit-v2  
No production integration before owner-approved B8.

| Batch | State as of 24 Oct 2026 | Evidence and exit gate |
| --- | --- | --- |
| B0 Foundation | COMPLETE — seven planning/fixture files committed and verified | MASTER_PLAN_V2, QUALITY_BASELINE, ARCHITECTURE_V2, fixtures, HANDOFF, branch/base comparison |
| B1 Reliability | PARTIAL — expanded 231/231 installed V2 tests PASS, Arabic app 55/55 and English layout 6/6 fresh PASS; both native English 2-page and native Arabic 3-page evidence-to-real-renderer synthetic no-post bridges now exist | No live collector/model/source/Discord; genuine content and service E2E still pending |
| B2 Source inventory | PARTIAL — 222-record ledger unchanged; three distinct rights-qualified alternative approaches screened and bounded search STOP reached; 0 registry/family promotions | Global Voices Arabic feed not current; OCHA CC BY humanitarian reports are not verified six-hour Arabic news; Wikinews closed May 2026. B1_B2_B3_B5_CONTINUATION_2026-10-23.md |
| B3 Evidence core | PARTIAL — POSIX locked journal, atomic head receipt and offline HMAC linked external-anchor contract exercised; no genuine external storage/key custody | v2_evidence_store.py, v2_evidence_anchor.py; local rollback detection needs independently held newer anchor; no publisher attestation |
| B4 Editorial engines | PARTIAL — native-language admissions plus obvious English/Arabic script-label mismatch refusal PASS; not full language identification | v2_editorial.py and v2_script_guard.py; Arabic-script Persian may pass, translation fidelity/source-family proof unavailable |
| B5 Layout | PARTIAL — actual V2-evidence-driven Arabic 3-page plus English 2-page synthetic renders; English missing values fixed; Arabic unknown severity neutral, unrelated events no longer filled into militant/conflict/maritime panels | Genuine source copy, Arabic mobile density and release-font legibility not signed off; see B1_B5_ARABIC_BRIDGE_2026-10-24.md |
| B6 Operations | PARTIAL — telemetry/SQLite-in-memory lab plus local atomic file-backed receipt-state rehearsal, 10 focused durable-state tests PASS | v2_delivery_receipt_store.py; ambiguity survives crash but no operational sender, D1, schedule, authenticated receipt or deletion |
| B7 Shadow | PARTIAL — deterministic same-window scorecard rejects uncited rendered items, unsupported verified delivery and impossible clipping; live captures unavailable | v2_shadow_scorecard.py; no real V1/V2 shadow execution or Discord publishing |
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
- New local POSIX single-writer journal store with cooperative flock, fsynced journal and crash-atomic independently checksummed receipt, strict replay and fail-closed split-brain refusal. **9/9** initial B3 lock/fault tests pass including separate process and injected receipt failure; next follow-on gate strengthened path handling and raised this to **12/12**. No off-host attestation, publisher provenance, power-loss proof or automatic repair.
- B2 first-party Global Voices Arabic CC BY candidate (excluding third-party media unless independently licensed) verified via publisher policies and one robots-allowed capped RSS metadata sample; **not recent**, 96k partial feed, no promotion or rights blanket clearance.
- B5 visually inspected synthetic Arabic pages; UAE small headline color contrast **2.17:1 → 4.79:1**, three explicit contrast/sample-marking tests, no font policy decision. All sample pages now identify synthetic non-news in the footer. The second-page ten-item density at reduced/mobile viewing remains a QA concern.
- `python -B -m unittest discover -s tests -p 'test_*.py' -q`: **181/181 PASS** (after both continuation gates). Reports and run details in `docs/v2/B1_B2_B3_B5_CONTINUATION_2026-10-23.md`. B1–B7 PARTIAL, B8 BLOCKED; no live resources, production, main, CI dispatch, Discord, deletion or paid calls.

## 23 October 2026 — B3 subsequent path-safety gate
- Reopen with a verified regular file now seeks to its byte-end before wrapping the append sink. An initial hardening regression was detected in the focused run, fixed, then all **12/12** exclusive-store tests passed; no production involvement.
- `v2_evidence_store.py` refuses symlinked root/receipt paths, opens leaf handles with `O_NOFOLLOW | O_NONBLOCK` and demands `stat.S_ISREG`; tests additionally assert FIFO refusal without blocking. No claim of defense against uncooperative malicious path substitutions or rollback of both artifacts.
- V2 focused full suite **181/181 PASS** at follow-on closure; separate legacy Arabic suite remains **55/55 PASS** from the first checkpoint. B3 remains PARTIAL pending independent off-host receipt/authentic publisher and integration evidence. Decisions and B6/B8 deployment/resource gates still deferred.

## 23 October 2026 — B2 three-route bounded research closure
- Official Global Voices Arabic RSS: CC BY eligible original Global Voices work, but a capped 23 Oct metadata sample showed no entry newer than 11 Oct; no third-party media rights granted by that license.
- UN OCHA official Humanitarian Action/country reporting pages carry CC BY 4.0 unless otherwise noted; useful as attributed humanitarian context, **not** yet proven current/native-Arabic six-hour news or publisher-family corroboration.
- Wikimedia Wikinews official portal confirms the project closed 4 May 2026; despite historical reusable licensing, it cannot fill 23 Oct current news slots. UN News search was blocked by robots, not retried or circumvented.
- **STOP bounded source discovery after 3 materially different non-admitted approaches.** No article-body scrape, feed promotion, new publisher identity, source registry modification or rights inference from robots. B2 remains PARTIAL; other offline work was completed independently. Next publisher clearance requires new dated/readable primary evidence or explicit permission.

## 24 October 2026 — B1/B3/B4/B5/B7 installed offline product rehearsal
- Starting V2 branch HEAD `5022fee801fe90ddd4d7a969eb6a945045f0f36a`; main observed unchanged at `c7a53e9f6ffa8167c8538b236af6d2bfaddabdf9` before this batch. No user-owned production resources, source registry, workflows or secrets modified.
- **B1:** Real English `gazette_render` 2-page 3840×2160 PNG no-post rehearsal now consumes actual B3/B4-gated synthetic English excerpts through `v2_english_application_rehearsal.py`. Three source IDs admitted, Persian-only event held, unavailable market/social data left absent, egress blocked. Explicit non-synthetic and existing-file overwrite rejection tests.
- **B3:** `v2_evidence_anchor.py` adds caller-keyed HMAC operator checkpoint and authenticated predecessor-chain verification. Simulated external newer anchor detects coherent local journal+head rollback; MAC tamper, wrong key, missing parent, reverse sequence and same-sequence fork refused. No off-host storage, signing-key management or publisher authenticity proof.
- **B4:** `v2_script_guard.py` detects obvious mismatched Latin/Arabic script against declared `en`/`ar` source snippets before B4 admission. **Not** language identification; Arabic-script Persian/Urdu/Pashto cannot be distinguished by script alone.
- **B5:** Actual V2 English page-2 visual QA revealed default 0–1 axes on missing market data and page-1 0% severity for all-unrated events. Isolated `gazette_render.py` now displays `No verified snapshot` without artificial ticks and `-` for unknown severity; 0% remains for measured zero among classified/rated events only.
- **B7:** Scorecard now rejects `items_rendered > items_cited`, preventing uncited rendered content from being reported as a coverage improvement.
- **Executed tests:** installed dependency Python 3.12 V2 `unittest discover -s tests` **208/208 PASS**; legacy Arabic application **55/55 PASS**; original English layout **6/6 PASS**. Real English two-page offline PNG generated and visually inspected in a disposable directory. The Arabic send/LLM test prints are mocks only; no real traffic.
- Evidence: `docs/v2/B1_B3_B4_B5_B7_NOPOST_2026-10-24.md`. **All B1–B7 remain PARTIAL, B8 BLOCKED.** No licensed/timely real feeds, live full-pipeline operation, actual off-host anchor, auth-backed D1 or paired real shadow evidence claimed. B2 search STOP and all deferred decisions remain unchanged.

## 24 October 2026 — B6 crash-aware local state and B7 assertion continuation
- The in-memory `ReceiptGate` could not retain an ambiguous delivery state after process restart; **new isolated `DurableReceiptStore`** serializes its existing state machine and checkpoints each mutation with a locked, checksummed and atomic/fsynced local snapshot. No sender or network calls exist in the new module.
- Abrupt process exit, two independent English/Arabic slots, conflicting reservations, checksum corruption, forged state, symlink, missing persisted state, concurrent local writer and injected write failure exercised; **10/10 focused tests PASS**.
- B7 offline scorecard now additionally rejects `confirmed_external` caller assertions (manifest lacks receipt proof) and impossible clipped/omitted counts; two new failing-first tests and **16/16 focused tests PASS**.
- Expanded installed-dependency V2 regression suite **220/220 PASS**; Arabic application **55/55 PASS** and original English layout **6/6 PASS** with mocked/no-post outputs. Reference `docs/v2/B6_DURABLE_RECEIPT_2026-10-24.md`. **B6/B7 PARTIAL**, B8 still BLOCKED. Production receipt reconciliation, cross-host state and live paired comparison require separate approval/evidence.

## 24 October 2026 — B1/B5 actual Arabic renderer no-post continuation
- `v2_arabic_application_rehearsal.py` consumes original-Arabic B3/B4 admissions and renders the genuine `arabic_layout.render_pages` three-slide 3840×2160 deck offline, with three synthetic source IDs and three non-Arabic events withheld. Result reports **0 clipped items**; no collection, model, translation, database or posting.
- `arabic_layout/render_engine.py` no longer defaults missing/unknown severity to Low: displays neutral **غير مصنف**. A failing-first test proved the prior bug; focused **7/7 bridge tests PASS**.
- `arabic_layout/render_pages.py` now requires factual title/summary support for page-3 militant, conflict and maritime-tension buckets. No filler of irrelevant security, generic regional or safe port-drill stories. Three failing-first tests exposed the old behavior; **4/4 category tests PASS**.
- Final synthetic three-page preview visually inspected with explicit sample labels and no category invention. Evidence `docs/v2/B1_B5_ARABIC_BRIDGE_2026-10-24.md`.
- Combined installed-dependency V2 **231/231 PASS**, original Arabic **55/55 PASS**, original English layout **6/6 PASS** in fresh post-change tests.
- **B1/B4/B5 remain PARTIAL**; lexical categories cannot certify factual truth, rights, translation, source families or mobile-scale legibility; B2 remains STOP and B8 BLOCKED.

## 24 October 2026 — B2/B4/B5 bilingual Naysayer and source-review kickoff (docs/fixtures only)
- Owner requested a comprehensive fresh source landscape review and a consistently present **Naysayer**/adversarial analyst, smaller in each daily English/Arabic edition and expanded in distinct weekly English/Arabic supplements.
- New `docs/v2/B4_B5_NAYSAYER_DAILY_WEEKLY_CONTRACT.md` defines evidence-gated challenge/abstention, source-family independence, native-language/verified-translation rules, provisional daily/weekly word/page budgets, visual slots and safety/factual quality gates. Weekly cadence and format are **proposals only**; no schedules or live products changed.
- New `fixtures/v2/naysayer_cases.json` has **10 synthetic, non-publishable expected-decision cases** spanning both products and both cadences. JSON structure and uniqueness checked during authoring; **no Python/runtime tests executed** for this documentation-only batch.
- A separate deep-source research request is being commissioned. No candidate source has been approved or promoted; existing B2 source-discovery stop remains in force until new evidence is evaluated. Copyright/robots/terms remain binding despite the desire for broader coverage.
- B4/B5 implementation, test-first behavior verification, genuine source-linked editorial comparison and actual daily/weekly rendered QA remain **OPEN**. B1–B7 PARTIAL; B8 BLOCKED.
- Production/main, Discord, CI, Cloudflare/D1, secrets, scheduled cleanup and paid resources were not modified.
