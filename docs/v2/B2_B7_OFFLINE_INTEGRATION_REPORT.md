# AggregateIT V2 — B2/B3–B7 integrated offline checkpoint

Date: 23 October 2026 (UAE)  
Branch: `rebuild/aggregateit-v2`  
Status: **isolated, synthetic, NO-POST. No production or live-source acceptance.**

## Scope completed in this package

**B3 → B7 single no-post rehearsal:** `v2_offline_rehearsal.py` accepts only an explicitly synthetic, bounded fixture with registered source IDs and reserved example hostnames. It reuses the real B3 article/excerpt/claim/event construction, appends and replays the hash-chain journal, checks the separate B4 English and Arabic evidence admissions, constructs B5 fixed-page layouts, checks B6 telemetry and unknown-budget fail-closed controls, and reserves B6 delivery slots for each product's symbolic destination secret without sending a request. B7 remains a separately tested offline scorecard; the rehearsal does **not** invent V1 captures or claim an end-to-end B7 production comparison.

The fixture ties an English excerpt and Arabic excerpt to one **explicit fixture-labelled** event, and includes a Persian-language event without verified translation. The two native-language excerpts survive replay and appear in their respective products, while unsupported content is withheld. The shared synthetic event key is not an inference or proof of multilingual entity resolution.

Rehearsal tests: **11/11 PASS**. Positive integration and negative paths cover event replay, product routing, no network/DB/LLM/Discord activity, exact quoted excerpts, unsupported language refusal, unregistered or non-synthetic inputs, real publisher URL refusal, conflicting event annotations and unverified publisher rights.

**B2 historical gap triage:** `v2_source_gate.py` audits the committed 222-source registry and the Arabic historical-audit summaries without fetching live publisher URLs. It rejects contradictory historical totals or duplicate source IDs, never turns a hostname into an independently verified publisher family, and caps suggested future probes at two per priority area. Source status, copyright/usage rights, publisher ownership and live freshness stay unverified. `tests/test_b2_source_gate.py` verifies the real versioned registry and negative cases: **10/10 PASS**.

## Bounded follow-up queue — proposals, not live successes

| Geography | Historical dated source(s) | At most two offline candidate IDs for a future **authorized** source check | Deficit |
| --- | --- | --- | --- |
| Somalia | `ar-s056` (Radio Ergo) | `ar-s056` only; independent second feed absent in historically compatible rows | Below two historically dated hosts |
| Yemen | `ar-s081` (Yemenat) | `ar-s081`, `ar-s082` (South24, compatible but 0 dated-recent) | One dated host |
| Egypt | `ar-s046` (Mada Masr) | `ar-s046`, `ar-s108` (Masrawy, compatible but 0 dated-recent) | One dated host |
| Jordan | `ar-s101` (Ammon News Jordan) | `ar-s101`, `ar-s070` (Petra, compatible but 0 dated-recent) | One dated host |
| UAE | `ar-s017` and Abu Dhabi Media Office IDs `ar-s116`/`ar-s118` | `ar-s017`, `ar-s118` (two distinct host candidates) | Two host candidates vs target three independent families |

The source IDs/URLs identify **historical registry candidates only**. They are not assertions of contemporary availability, source-language accuracy, source usage permission, geographic editorial relevance or independence. For Somalia, alternative configured publishers were historically disabled, missing a feed or 404; they are flagged for manual discovery, not counted as a second valid feed. The UAE Media Office entries share one host; three feed endpoints do not prove three independent publishers.

## Combined regression evidence

- Earlier B3–B7 synthetic checkpoint: **96/96**.
- This package: **11 integrated rehearsal + 10 source gate**.
- One combined real-source-module, in-memory Python 3.12 `unittest` run: **117/117 PASS**; no stubs for the B3–B7 module collaborations. B1 and earlier B2 reconciliation cases not rerun in this combined run.
- Not proven: dependency-installed application suite, file-backed fsync/crash restore, authenticated feed captures, publisher rights, translation fidelity, source identity/ownership, actual slide raster/Discord-scale typography, transactional D1 receipt or analytics store, live no-post shadow V1/V2 comparison, SLA or repeated six-hour operation.
- Tool/environment constraint: read-only execution workspace, with production feedparser/requests/Arabic typography dependencies unavailable. Test sources were executed in memory from the branch. No published Python package/full integration runtime was used.

## Remaining gates in priority order

1. **B1**: dependency-installed isolated full-route/no-post application test, including primary and fallback error paths and 6-hour schedule simulation.
2. **B2**: rights and publisher-family identification per candidate, bounded current adapter/72h freshness probes using an approved access path; eliminate geographic/language gaps. Stop after three materially different unsuccessful access approaches, return blocker to owner.
3. **B3**: durable exclusive-writer journal + independent stored head receipt + fail/restart/replay, authenticated source revision capture with rights review.
4. **B4**: verified source-native editorial correctness, translation coverage/fidelity and geographic subject annotation. Preserve per-product boundaries.
5. **B5**: actual 2-page English and 3-page Arabic raster rendering; 100% Discord-scale screenshot/RTL/contrast/clipping inspection.
6. **B6**: optional free D1 analytics limits, dry-run retention, verified export/restore; no deletion or Drive upload without explicit separate instruction. Durable idempotent delivery receipts and external acknowledgement are required before real send.
7. **B7**: same-window frozen V1 and V2 captures over repeated cycles, no-post until separately approved; compare quality and geographic loss with source denominators.
8. **B8**: explicitly approval-gated canary/cutover and rollback; **NOT AUTHORIZED**.

## Explicit negative assertions

No production/main or Arabic production branch modifications; no Actions dispatch, webhook/Discord send, publisher request, model inference, Cloudflare/D1/PocketBase creation, Drive connection, raw-data copy, cleanup deletion or paid action. No source was promoted from the historical registry; `source_gate_report` uses only old observations. The next batch should prioritize reproducible isolated runtime and source/fidelity acceptance rather than inflating synthetic test count.
