# AggregateIT V2 — Free-Plan Analytics & Backup Policy
Decision: accepted as a planning amendment on 23 October 2026 (UAE). No Cloudflare resource or scheduled cleanup has been created.
Applies to a proposed small analytics/telemetry database ONLY. It does not authorize deletion of the existing production SQLite state, source records, cached artifacts or news/evidence data.

## Architectural boundary
- Recommended provisional backend: Cloudflare D1 Free + an authenticated ingestion Worker + a small read-only operator dashboard.
- PocketBase remains an option only if an approved persistent host and backup volume already exist. Its built-in admin UI is not a substitute for editorial metrics.
- D1 is for operational *metadata* (source probes, editions, translation/model outcomes, render QA, receipts, daily totals), not for full article text, images, prompts, model credentials, raw HTTP bodies or unlicensed archives.
- Canonical article/evidence durability remains an independent B3/B6 decision; never silently migrate or destroy existing state.

## Verified platform ceilings (as at 23 October 2026)
| Cloudflare D1 Workers Free | Provider ceiling | Application policy |
| --- | --- | --- |
| Single database size | 500 MB | Warn at 250 MB; stop optional detail at 300 MB; stop all D1 writes at 350 MB |
| All D1 database storage | 5 GB total/account | Refuse creation if shared account headroom cannot be verified; reserve for other databases |
| Rows written (including deletes/index overhead) | 100,000/day, account shared | Budget at most 20,000 rows/day across analytics write and cleanup jobs |
| Rows read/scanned | 5,000,000/day, account shared | Target no more than 250,000 rows/day; pagination, indexes, aggregated reads |
| Databases | 10/account | Create one separate analytics database only after approval |
| Database recovery history | 7 days | Never treat Time Travel as a long-term backup |
| Queries per Worker invocation | 50 (Free) | Each maintenance batch well below this boundary |

The free plan stops servicing over-quota operations; there is no automatic fallback to paid service. Do not enable billing upgrades or paid Workers to overcome exhaustion. Guardrails must consider all D1 usage in the same account, not just this Worker. Verify limits again before deployment.

## Ingestion and budget enforcement
- Proposed initial cap: 3,000 detailed telemetry records/day; 300 records/source-probe cycle and 600/model-or-edition cycle unless real measured needs justify revising these ceilings. Above cap, aggregate counts or drop *optional analytics only*, never interrupt news delivery.
- Every insertion has an idempotency key (run_id + event class + source/article key). Reject duplicates before writing.
- One collector/gateway batches and samples data. The worker records per-query rows_read, rows_written and size_after where returned by D1, plus reconciles account-wide usage via Cloudflare metrics if accessible.
- If metric verification is unavailable, avoid high-volume ingestion and raise an operational warning; preserve independent log artifacts for later reconciliation.
- At 250 MB: warning/forecast; at 300 MB: disable per-article/per-model detail first; at 350 MB: hard stop all analytics writes pending export/cleanup. Always retain main briefing delivery and show “telemetry unavailable” externally.
- Query cost is based on rows scanned, not returned. Index by timestamp, source_id, product, run_id, status, and aggregate by day. Never run recurring unbounded full-table scans.
- A rate-limited authenticated append-only endpoint is required. Do not expose superuser credentials or database administration publicly.

## Retention and scheduled maintenance (future B6 deployment)
| Data class | Retention target | Disposal policy |
| --- | --- | --- |
| Fine-grained source probes, model outcomes and per-run telemetry | 30 days | Roll up first; delete only eligible detail, in bounded batches |
| Daily source/product/model health aggregates | 365 days | Monthly summarization/export, then bounded expiry |
| Edition identifiers, verified delivery receipts and change/audit decisions | 365 days minimum | Retain separately from expendable logs; archive before any eventual purge |
| Full article texts, source evidence, existing production state | NOT stored in D1 | Never automatically delete or move without independent user authorization and verified backup |

- Run a single authenticated Cloudflare Worker Cron maintenance task once daily at 00:30 UTC (04:30 UAE); no extra GitHub Actions schedule. Its initial mode is DRY_RUN, with count-only reporting.
- On each live cycle: verify budget -> compute idempotent daily rollups -> verify totals -> purge records older than their approved class cutoff in batches of no more than 250 rows per query (up to 5,000 rows per day subject to write budget) -> record count/reasons/elapsed time.
- Never delete records with unknown timestamps or unclassified retention category; quarantine them for explicit review.
- A failed rollup prevents that table's deletion. A missing operator-confirmed Google Drive export covering the records also prevents deletion; stop optional detailed ingestion at the cap rather than erase unarchived rows. A failed cleanup marks health degraded and retries the next day; no unbounded catch-up loop.
- Cleanups and any destructive retention enablement require a separate preview of exact table/cutoff/count and operator approval at B6. This document alone does NOT activate deletion.

## Manual Google Drive backup — two different meanings of “raw”
1. **Analytics SQL export** (D1 rows/schema): supported by Wrangler. From a trusted personal machine, after D1 is deployed:
   `npx wrangler d1 export aggregateit-analytics --remote --output=./aggregateit-analytics-YYYY-MM-DD.sql`
   Replace YYYY-MM-DD with the actual date and use the real D1 database name. Verify that the export finished successfully.
2. **Original article/evidence raw archive**: NOT part of the analytics D1. Export/copy from the separately defined source-of-truth archive (existing SQLite and future article/evidence storage) when implemented, preserving URL, timestamps, hashes and source-rights metadata. Do not assume a D1 export contains raw articles.

For both exports:
- Calculate SHA-256 locally, for example on Windows PowerShell:
  `Get-FileHash aggregateit-analytics-YYYY-MM-DD.sql -Algorithm SHA256`
- Upload the file manually via Google Drive to a restricted AggregateIT/backups/YYYY-MM folder. Record the filename, SHA-256, export range, byte count, date, archive type and **your confirmation** of successful upload in a separate backup manifest; never store Google passwords/tokens in GitHub.
- Download a backup to an isolated test environment quarterly and test schema/data restore. Hash confirmation alone is not proof of restorable data.
- Suggested cadence: analytics export every two weeks (before the 30-day detailed telemetry window expires); raw article/evidence archive at least monthly once archival storage exists. Adjust only after actual volume/rights/restore checks.
- D1 Free Time Travel allows 7-day recovery, but is not a substitute for your Google Drive archive.

## Telemetry schema proposal
- source_probe: source_id, region, checked_at, probe_status, freshness_window, latest_published_at, item_count, adapter_version, latency_ms.
- engine_run: product, slot_id, run_id, revision, start/end, result, error, duration, counts.
- model_attempt: route_hash/provider label, task, status, error_category, latency, token_usage_estimate, optional cost_estimate; NO API key or prompt body.
- edition_quality: edition_id, field_count, evidence_count, rejected_count, translation_attempted/completed, geography_gaps, page_validation_result.
- delivery_receipt: edition_id, expected channel reference, status, message_id, retry_resolution; NO webhook URLs.
- day_rollup: date, product/region/source, counts, degraded_reason and denominators.
- backup_register: artifact type, export time, content hash, size, operator-verified Drive upload and restore test result.

## Acceptance gates and stop conditions
1. Policy and telemetry data contract approved, with budget tests for 0, 250, 300, 350 and 500 MB and simulated near-quota rows.
2. Synthetic fill/cleanup tests prove bounded deletion, idempotent rollups and all protected data types untouched.
3. No use of D1 beyond free-account budget; verify account sharing and quota consumption at deployment.
4. Backup export + SHA-256 + independent restore trial completed before first live deletion; later cleanup requires operator-confirmed export coverage of every row being purged.
5. No production migration, payment, Discord posting, OAuth token storage or auto-sync to Google Drive without separate authorization.

Official references:
- D1 pricing: https://developers.cloudflare.com/d1/platform/pricing/
- D1 limits: https://developers.cloudflare.com/d1/platform/limits/
- D1 import/export: https://developers.cloudflare.com/d1/best-practices/import-export-data/
- D1 Time Travel: https://developers.cloudflare.com/d1/reference/time-travel/
- Workers Cron: https://developers.cloudflare.com/workers/configuration/cron-triggers/
