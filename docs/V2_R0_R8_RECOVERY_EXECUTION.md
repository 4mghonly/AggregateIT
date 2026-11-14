# AggregateIT V2 coordinated recovery — R0–R8 execution register

Status: **IN PROGRESS; NOT RELEASE-READY**. Working branch: `audit/b119-evidence-reconciliation`. V1 `main` and protected `rebuild/aggregateit-v2` are read-only. No Telegram or production publishing authorized by this recovery approval.

## R0 initial source-to-output inspection (2026-11-14)

The inventory of the writable branch includes 623 entries and 397 Python files. This is a targeted **execution-path inspection**, not a claim of full line-by-line coverage of every file.

| Stage | V1 implementation | V2 implementation | Verified finding | Required action |
|---|---|---|---|---|
| Collection | `main.py:fetch_rss,full_text,score_item`; `slide.py:collect` | `v2_b46_live_editorial_runner.py:run`; `v2_b46_live_editorial.py:compile_captured_articles` | V2 limits capture to 64 and source bodies to validated publisher captures | Compare same-capture source admission, missingness and category mix |
| Relevance | `main.py:score_item,cluster_events` | `v2_editorial.py:plan_edition`; `v2_b46_live_editorial.py` | Fixed `max_items=6` previously imposed for both products | Configurable bounded limit implemented; inspect layout and selection quality before raising operational limit |
| Event identity | `main.py:cluster_events,resolve_prior_event` | `v2_b46_live_editorial.py:compile_captured_articles` | V2 assigns one explicit article event per captured article; cross-publisher similarity does not auto-merge | Introduce reviewable event clustering with source-family provenance |
| Intelligence | `main.py:analyze_event` calls structured LLM with evidence and prior event; Arabic `arabic_newsletter/editor.py` | `v2_product_compiler.py:compile_daily` | Compiled V2 stories have `assessment=None`; live output reports `model_called=False` | Implement evidence-grounded event analysis, typed provenance and abstention behavior |
| Markets | `market.py`; `slide.py:collect,analyze` | `v2_product_compiler.py:compile_daily` accepts validated observations | Real V2 sample reports English market unavailable | Restore read-only market observations with timestamps and clear stale/unavailable handling |
| Daily visual | `slide.py:render_p1,render_p2`; `arabic_newsletter/render.py` | `v2_native_evidence_render.py`; `v2_recovery_english_layout.py` | V2 pages show source excerpts without substantive event assessments | Design against actual analytical data, full-size human visual review |
| Weekly | V1 report and historical state | `v2_b47_four_product_held.py` | `rollup_week([plan],...)` uses a single plan | Connect seven real V2 daily plans; disclose missing dates |
| Publication | V1 `main.py:send_digest`; `slide.py:send` | Held no-send V2 workflow; separate controlled Telegram preview | Transport acceptance alone is not editorial acceptance | Require human approval and strict no-auto-publish |

### Sample evidence
- English V1 `intel-report.zip` from historical 2026-11-13 workflow: eight events; first observed event includes facts, assessment, what changed, confidence, corroboration and gaps.
- Arabic pre-existing `briefing.json` sample: thirteen events plus `situation_ar`, `implications_ar`, `developing_ar`, `watch_ar`.
- V2 real daily no-send artifact `v2-live-quality.json`: six English and six Arabic selected; English represented regions `['iran']`; `market_status='unavailable'`, `model_called=False`.
- Sample windows are not identical; compare source-matched runs before making numerical superiority claims.

## R1 first implemented change
- Added optional `editorial_max_items` to `compile_captured_articles`, strict integer range 1–16, default remains six to avoid silently overfilling existing image templates.
- Added `tests/test_v2_r1_editorial_capacity.py` with signature, default and invalid-value regressions.
- This **does not** close coverage parity or change the currently shipped visual limit. Raising the count is conditional on renderer and editorial acceptance.

## R2 design contract — required before enabling a model
1. Input: canonical event, all independent source-family excerpts, prior signed event state, verified market context and timestamps.
2. Output: source-backed factual claims; separate conditional assessment; significance and what changed; alternative interpretation; uncertainties; monitorable indicators; confidence calibrated to independent corroboration.
3. Reject unsupported claims, fabricated links, wrong language, empty analysis and citation IDs absent from the evidence ledger.
4. When inference fails or evidence is inadequate, mark analysis unavailable rather than silently publishing excerpts as an equivalent intelligence product.
5. Run local and hosted models behind a provider-agnostic adapter with explicit limits, no secret values in logs and no unapproved spend.
6. Keep publication authorization separate from successful model execution.

## Work queue
- **R0:** Continue line-by-line inventory and line-specific defect ledger for remaining critical execution paths; collect controlled matched-capture comparison.
- **R1:** Add selection diversity and significance tests; explain each significant V1 omission; integrate safe adaptive page capacity.
- **R2:** Implement and test analysis adapter, claim-to-excerpt checks, Arabic synthesis and abstention; execute against real captured inputs.
- **R3:** Event resolution, corroboration and historical continuity.
- **R4:** English financial and macro feeds with freshness gates.
- **R5:** Independent English/Arabic editorial contracts and quality tests.
- **R6:** Adaptive native layout, full-resolution image checks.
- **R7:** Genuine seven-day native weekly assembly.
- **R8:** Controlled end-to-end acceptance; no Telegram send before human editorial approval.

## Exit criteria
A green test suite is necessary but insufficient. Each batch needs reproducible test evidence and source-matched editorial acceptance. R0–R2 remain open until real analytical output has been inspected, not merely because configuration tests pass.

## R2 resumed implementation checkpoint (2026-11-14)
- Added optional `analysis_candidates` to `v2_product_compiler.compile_daily` with strict event ID, excerpt ID, confidence, nonempty statement and duplicate controls.
- Accepted analytical text is explicitly labeled `evidence_referenced_unverified` and `content_truth_verified=False`, `delivery_authorized=False` remain invariant. This is **not** independent corroboration or verification of the model's factual content.
- No candidate means `analysis_status=abstained`, rather than generating unsupported filler.
- Added five R2 contract tests and dedicated CI. The model inference adapter, cross-excerpt validation, real model calls and genuine rendered analysis are still outstanding. Do not characterize this contract as complete R2.

## Continuous recovery checkpoint (2026-11-14, second pass)
- R1: The live runner now accepts `editorial_max_items` (1–16, default six), propagates it to the compiler, and raises its per-language capture ceiling when the requested story budget exceeds ten. CLI `--editorial-max-items` is supported. This does not guarantee the available publisher roster supplies enough distinct eligible stories.
- Added regression test `tests/test_v2_r1_runner_capacity.py` and included it in `v2-r0-r2-recovery.yml`.
- R2: evidence-bound candidate compiler remains deliberately non-publishing; actual model generation, claim verification and renderer integration remain open.
- R3–R8: **NOT COMPLETE**. No user-facing Telegram samples or production sends were authorized or triggered by this batch.


### R7 source-bound history input checkpoint (2026-11-14)

`compose_held_products` now accepts optional `weekly_history={'english': [...], 'arabic': [...]}`. Each list contains previously captured daily editorial plans, not generated or fabricated snapshots. The weekly rollup validates plan schema, source excerpt references, language, date window, and counts distinct observation dates. When history is missing, the original single-day incomplete-week status remains. This is an input contract, **not** proof that seven genuine days have been captured. All daily/weekly packets remain held and unsendable. R0–R8 final acceptance remains open.

## R2 live publisher acceptance checkpoint (2026-11-14)
- Live publisher capture yielded three English and three Arabic stories; primary and fallback configured routes both reached the inference endpoint. Structural response outcomes varied across repeated runs; an explicit empty-items abstention is permitted by the adapter contract and must not be misclassified as a transport failure.
- Earlier real-publisher run 43606785375: primary English/Arabic pass, fallback Arabic pass, fallback English ValueError. Run 43607533628: primary English ValueError, fallback English pass, both Arabic pass. Run 43607816630: three structural passes and fallback Arabic abstention; strict non-abstention gate failed. These runs do NOT demonstrate reproducible semantic quality.
- The held runner uses only one selected item per language per model; passing this limited probe cannot establish comprehensive article coverage, contradiction handling, or editorial equivalence. Analysis candidates remain evidence-referenced but unverified.
- R2 connectivity and provider integration are implemented; full R2 semantic/editorial acceptance remains OPEN pending independent assessment of genuine model prose against source excerpts, Arabic language quality, and rendered edition verification. Do not equate green workflow status with this sign-off.
- No production delivery authorized. Protected branches unchanged.
