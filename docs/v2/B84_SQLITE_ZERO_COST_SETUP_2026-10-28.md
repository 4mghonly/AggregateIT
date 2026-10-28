# V2 SQLite zero-cost setup — 28 October 2026

Status: **isolated SQLite implementation and hosted smoke test**. This does not yet connect the newsletter pipelines to the DB or provide durable multi-run restore.

- Branch: `rebuild/aggregateit-v2`; no V1/main or production modifications.
- `v2_sqlite_store.py`: standard-library SQLite; articles, source health and edition evidence; EN/AR identities deduplicated; 64 KiB per JSON record; 20 MiB file ceiling; cleanup 14/30/30 days.
- `.github/workflows/v2-sqlite-acceptance.yml`: creates an **empty** local DB, tests operations, uploads a 7-day expiring artifact. No external database, paid service, webhook, model, or network write. GitHub Actions artifacts are temporary; **not a permanent DB**.
- Secrets, full publisher bodies and personal data should not be stored in the artifacts. Avoid putting untrusted publisher text into persisted evidence without additional review.
- A private backup repository and restore-on-run integration remain **unimplemented**. Creating a separate repository and storing production data requires explicit design of access control, serialization, collision prevention, privacy, size, restore integrity and GitHub quota. Do not imply a durable backup exists.
- No free-tier usage or cost can be guaranteed indefinitely: GitHub plan limits, storage and minutes must be monitored. This workflow has a five-minute job timeout and seven-day artifact retention.
- Next: implement transactional restore from a verified artifact or isolated private backup repo, then wire actual V2 capture/edition receipts, add automated cleaning and backup retention. Require demonstrated multi-run restoration before calling database persistence complete.
