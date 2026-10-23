# AggregateIT V2 — B6c SQLite Analytics and Local Backup Rehearsal

Date: 23 October 2026 (UAE)  
Branch: `rebuild/aggregateit-v2`  
State: **fully disposable SQLite `:memory:` experiment, zero external storage usage**

## Delivered

- `v2_analytics_sqlite_lab.py`: parameterized SQLite tables for approved operational metadata only; primary-key idempotency, independent English/Arabic product counts and grouped source/edition statuses. A runtime connection uses **`:memory:`** and vanishes at process exit.
- All ingest paths validate the existing `v2_analytics_controls.py` allowlist. Raw text, full article URL, prompts, provider output, keys and other unapproved fields cannot enter the lab.
- Optional writes fail closed when any current account-level usage figure is **unknown**. When supplied as mock values for rehearsal, the existing policy imposes application headroom: warning at 250 MB, details throttled at 300 MB, optional writes stopped at 350 MB, daily 20k writes and 250k reads. The lab conservatively adds locally accepted writes and estimated bytes to a possibly stale account snapshot, preventing sequential local writes from evading the limit. **These figures are conservative proposed app controls, not proof of Cloudflare's current free-plan limits or account-wide usage.**
- Valid telemetry produced by the synthetic bilingual B3–B7 no-post rehearsal was inserted as two separate, approved metadata records in local SQLite, grouped, exported, SHA-256 checked and restored into a **second disposable SQLite database**. Source articles and real Discord/Cloudflare systems were not touched.
- `retention_dry_run` computes only candidate IDs for detail older than 30 days, with the planned 04:30 UAE schedule explicitly **not deployed**; no SQL DELETE method exists in the lab.
- `export_bytes` generates in-memory JSON and SHA-256 digest. `verify_restore` rejects changed bytes, false Drive/production-backup flags and restored-row discrepancies. It certifies **local simulated restore only**; there is no Drive upload, real database backup or service-to-service restoration.

## Verification

- 13 B6 SQLite tests (including bilingual integrated telemetry round-trip) PASSED.
- Combined B2 source gate + B3–B7 integration + B5 raster + B6 SQLite + previous B3–B7 unit coverage: **138/138 synthetic offline Python tests PASS** in one in-memory Python 3.12 run.
- No real D1 SQL/transaction parity, connection serialization, Cloudflare account budgets, remote export download, Google Drive authorization, durable writer/race/concurrency, or scheduled retention operation were tested.

## Still required before activation

1. Explicit choice and approval of a free-plan deployment (Cloudflare D1 proposed; PocketBase would need its own host/storage/backup). Verify **current** provider quota, storage, account-level writes/reads, and Cloudflare Worker compatibility before provisioning.
2. Provision isolated non-production D1 only with user approval; use actual account usage and apply the budget gate before optional telemetry writes. A denial must not block either newsletter.
3. Implement authenticated read-only admin dashboard with low-cost aggregated queries, role restrictions and export download; do not expose the analytics write path to readers.
4. Prove actual export integrity, restore in a disposable independent instance, capacity limits and no-loss fallback before proposing retention deletion.
5. Connect manual Google Drive archive **only on explicit request**. Raw-news storage and redistribution require separate source-specific rights decisions; this lab exports metadata only.
6. Enabling any scheduled cleanup or destructive deletion is **not authorized** by this experiment; keep the production-data cleanup gate held pending explicit approval.

No production branch, Cloudflare deployment, D1 resource, GitHub Action, Discord, API key, Drive file, existing SQLite/PocketBase database or paid resource was changed.
