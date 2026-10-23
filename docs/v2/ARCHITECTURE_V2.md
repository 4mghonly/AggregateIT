# V2 Architecture — Proposed Contracts, Not Yet Implemented

## System flow
Source registry -> adapter/probe -> immutable normalized article -> excerpt/evidence index -> claim/event cluster -> edition planning -> editorial validation/LLM -> deterministic template renderer -> publication gate -> Discord receipt ledger.

A market context snapshot can join the English editorial layer, but never becomes evidence of a reported geopolitical fact. The Arabic geopolitical/security product uses a separate selection policy and a strict three-page layout budget.

## Data objects and identities
| Object | Minimum fields | Invariant |
| --- | --- | --- |
| Source | source_id, origin_domain, operator_family_id, format/adapter, language, region, rights, verified_at, disabled_reason | Syndicated or mirrored copies cannot count as independent origin families |
| Fetch observation | observation_id, source_id, fetched_at, HTTP/adapter status, freshness, duration, content hash, error class | A successful HTTP response is not proof of fresh usable stories |
| Article | article_id, canonical URL, source_id, published_at, retrieved_at, original text/language/hash, immutable snippet IDs | Stable deterministic identity; original language and provenance preserved |
| Evidence | excerpt_id, article_id, literal span, offsets/hash, original language, normalized translation with provenance | Every factual claim points to literal source evidence |
| Claim | claim_id, normalized subject/predicate/object/temporal/geography, evidence IDs, contradiction/uncertainty | Facts distinguished from publisher claims and analyst inference |
| Event | event_id, claim IDs, first_seen, last_changed, lifecycle, geo, source-family corroboration | Event update survives process restart and does not use randomized Python hash |
| Edition | product_id, slot_id, version, registry revision, selected IDs, quality result, render ID | Same product/slot cannot silently publish duplicates |
| Delivery | edition_id, channel policy, digest, request state, Discord message receipt, attempted_at | Ambiguous send state must be reconciled before retry |

Proposed IDs: canonicalized domain/URL plus collision-resistant digest for articles, digest of normalized content and article/spans for excerpts, stable saved IDs for evolving events, product+UAE-time-slot for editions. Hash input/version must be recorded. Do not hash untranslated names alone.

## Source architecture
- Registry is append-only/revisioned at provenance boundary; English and Arabic consumers share source metadata but can have different editorial eligibility.
- Store separate last_probe_ok, last_fresh_item, last_usable_event, and rights/terms flags. Statuses: HEALTHY, STALE, BLOCKED, PARSE_ERROR, EMPTY, RATE_LIMITED, QUARANTINED, UNVERIFIED.
- Probe with respectful timeouts/backoff, per-host concurrency and reproducible adapter snapshots. Distinguish transient 403/429 from permanent 404 and changing HTML.
- Alternative origin families must genuinely differ; mirrors of identical wire content do not raise independence confidence.
- Region threshold failure MUST NOT globally block registry bookkeeping and source replacement work; publish truthful gaps separately.
- Publishability and regional coverage are editorial decisions based on freshness, subject and evidence, not publisher country alone.

## Model route strategy
- Parse/validate provider responses with structured error classes: AUTH_403, RATE_429, TIMEOUT, EMPTY, TRUNCATED, INVALID_SCHEMA, UNSAFE_CLAIM.
- Maintain independent route health and per-run invocation/time budgets. Open circuit on repeated nontransient authentication errors.
- Batch short translation candidates under token/latency cap where supported; preserve per-article alignment. Failures never result in fabricated Arabic facts; either use authentic Arabic evidence or abstain visibly.
- Do not ask models to place text, pick font sizes, draw layouts or invent visual motifs. Their allowed outputs are constrained fields, uncertainty, attributed analysis and optional translated strings.
- Output schema enforcement runs outside the model. Review source quotation alignment, numbers, geography, event duplication, language completeness and hallucinations.
- Isolate raw collection and model prompt input to reduce prompt-injection influence. Source text is data only.
- A deterministic but explicitly degraded edition may publish without analysis if all fact/evidence gates pass; never publish generic invented “analysis”.

## Design system direction
- Arabic: command briefing, UAE first when sourced, three pages, dark slate/ink with restrained regional accents, precise typographic hierarchy, flags only when grounded, no generated event imagery; RTL, robust shaping and glyph checks.
- English: two-page editorial Gazette retaining useful market pulse/changes tables. Avoid “AI-dashboard” decoration.
- Template engine owns every box. Page planner measures text, sets a minimum effective font at Discord preview scale, applies admission budgets and deterministic ellipses/reflow; if fit impossible, reject/omit lower-priority story with a log, never silently crop facts.
- Split editorial completeness and design beauty metrics. Screenshot comparison at original size AND likely Discord scaled size.
- Copy the current Arabic product's proven useful layout rules and retain approved format until user signs off on a new template.

## Storage / schedule architecture
- B0-B1: production cache and SQLite remain untouched; fixtures and state are local to isolated runs.
- B6: evaluate SQLite-on-persistent-worker, Cloudflare D1/R2/Durable Objects, managed Postgres or other minimal-cost durable backing against actual required reads/writes, regional latency, backup/restore and no-cost constraints. No silent purchase.
- Separate fixed slot identity from GitHub workflow run identity. Two schedulers can coordinate only through one durable slot-claim ledger; do not infer scheduler deployment from checked-in ops scripts.
- Persist publication intent, digest and receiver receipt. Claim before send, then reconcile unknown outcomes without blind retry.
- Quality alert thresholds: missing deadline, missing receipt, degraded content, source coverage gap, unusually low translation yield, low corroboration, stale market data.
- Audit trails must separate confirmed fact, publisher assertion, analyst inference, market observation and unresolved conflict.

## Safety, compatibility and rollout
- Event consumers get a versioned schema adapter. Existing English/Arabic source lists remain readable until migration verified.
- No direct new branch Discord posting; isolated renders and run receipts live only in fixtures/approved storage.
- B7 replay compares the same time window and a pinned source set; report both quality gain and added latency/cost.
- B8 explicit approval required for schedule/webhook/branch/config changes. Preserve rollback to known main revision and previous registry/snapshot with receipt reconciliation.
- Test domains: freshness, 403/429, malformed/undated feeds, cross-language name collisions, Arabic encoding, single-source rumors, provenance mismatch, timezone/DST invariants (UAE UTC+4), duplicate schedulers, Discord transient failure and text clipping.

## Open ADRs (defer choices until evidence)
1. Source representation: JSON registry now versus SQLite table later.
2. Persistent storage choice and costs.
3. Per-source rights/republication policy for excerpt retention.
4. Model fallback ordering, token budget and availability/cost policy.
5. Page density and exact font face/size after real preview-scale comparison.
6. Search/embedding options only if deterministic clustering misses measured cases.

## Telemetry sidecar (accepted plan amendment)
A separate noncritical operations sidecar receives bounded run/source/model/edition/receipt metrics. It does not own immutable article evidence and cannot block collection, rendering or delivery when storage is at quota. Provisional Cloudflare D1 Free backend and small authenticated Worker UI; no existing server is assumed. Internal budget limits, retention dry-runs, cleanup windows, Cloudflare account-wide free ceilings, and manual SQL/independent raw archive are detailed in ANALYTICS_STORAGE_POLICY.md. This does not resolve the B6 canonical event database choice.
