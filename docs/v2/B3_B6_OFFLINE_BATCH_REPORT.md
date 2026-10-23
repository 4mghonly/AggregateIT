# AggregateIT V2 — B3c / B4 / B5a / B6a Offline Batch Evidence
Date: 23 October 2026 (UAE)
Branch: `rebuild/aggregateit-v2`
Status: **isolated prototypes only; no production integration, deployment, model, feed, database, cleanup or Discord actions**

## B3c — append-only replay and recovery prototype
- `v2_evidence_journal.py` appends canonical JSONL frames; SHA-256 hash chain, monotonic sequence, exact source-graph replay and external head receipt checking.
- Each command is validated against a copy of the current evidence graph before the stream write; I/O failures poison the journal instance pending recovery. The durable mode requires stream flush and `fsync`; tests use a deliberately nondurable in-memory stream.
- Explicit size limits: 1.2 MB/frame, 64 MB/log, 50,000 records; existing graph 20,000-observation maximum remains.
- Rejects changed/reordered frames, partial tail, unknown commands, unsupported references and old-revision tampering. Complete-tail loss is detected only if caller preserves the head receipt independently.
- **Not production durability**: no disk-based crash test, exclusive-writer lock, atomic off-host receipt, durable backend, live publisher verification or source rights certification.

## B4 — separate evidence-gated English/Arabic editorial admission
- `v2_editorial.py`: one in-memory source/evidence/event ledger, two independently scoped policies.
- English allows market/economy/geopolitics topics, 2-page budget; Arabic allows diplomacy/security/conflict topics, 3-slide budget, deliberate UAE-first admission (maximum four), then geographic diversity across 17 named region keys.
- Only source-native **verbatim spans** from already attached publisher-assertion claims are admitted. Excerpts must have source identity, exact revision, suitable timestamp, safe text length and matching product language.
- Persian/other-language content without independently verified target-language wording is withheld with an explicit reason. Translation is **not** fabricated. No semantic LLM output, claim rewriting, verified-language certification or full cross-lingual QA has been performed.
- Previous edition delta uses stable event version IDs and distinguishes unknown baseline, new, updated and unchanged. Every item explicitly says publisher independence is unverified and analysis abstained; all edition payloads have `delivery_authorized=false`.
- Geography annotations and severity/priority supplied by upstream are **not authenticated or validated as correct geopolitical facts**. Live source-family corroboration and headline semantic-fidelity review are open gates.

## B5a — fixed-page non-rendering layout admission
- `v2_layout.py` provides 3 Arabic command-brief page contracts (UAE/Gulf; near regional theatre; extended theatre) and 2 English Gazette contracts (security/geopolitics; markets/economy).
- Source quote, claim, event version and URL are checked against the actual graph before layout. Per-page cards and character caps produce explicit omission records instead of silently clipping.
- RTL/LTR, suggested palettes and font fallbacks are specifications only. No raster slides, screenshots, 3840×2160 visual QA, font-install test or Discord-resolution proof occurred; B5 stays PARTIAL.

## B6a — no-resource analytics guard prototype
- `v2_analytics_controls.py` rejects article bodies, prompts, URLs and secrets in telemetry; accepts only allowlisted operational metadata.
- Account metrics unknown => refuse optional analytics writes; warn at 250 MB, reject optional detail >=300 MB, stop writes >=350 MB, with 20,000 written rows/day and 250,000 read rows/day application budgets.
- Retention preview labels expired 30-day detail and 365-day aggregates. The proposed 04:30 UAE sweep remains **dry-run-only**; output requires verified export checksum, tested restore and explicit approval before deletion.
- Backup manifest provides a checksum for metadata only. There is **no Cloudflare D1, PocketBase, Drive upload, deployed cron, DB deletion or backup restore test**.

## Tests and acceptance limits
- 19 original B3-core + 15 B3-ledger + 14 new B3-journal + 15 B4-editorial + 8 B5-layout + 12 B6-budget = **83/83 passing**.
- Ran real Python `unittest` cases against actual fetched branch source plus proposed modules in an isolated Python 3.12 in-memory harness. No packages, writable clone, external services, or Actions used.
- This is **synthetic contract evidence only**, not live newsroom accuracy, multilingual translation coverage, layout screenshot approval, filesystem crash-recovery or integrated production behavior.
- B1/B2 remain PARTIAL. B3 remains PARTIAL until persisted integration, source provenance and replay-in-real-process pass. B4, B5 and B6 are newly PARTIAL. B7 shadow and B8 production cutover have not started. B8 requires the owner's explicit permission.

## Next bounded package
1. In isolated durable test fixture, prove write→fsync→restart→replay and power-loss simulation using independently stored head receipts; test concurrent-writer exclusion, large files, permissions, and SQLite/D1 feasibility without allocating paid resources.
2. Validate authenticated article captures and publisher rights/family identity in a small sample from B2; attach received-source provenance without mirroring unlicensed raw text into telemetry.
3. Connect B4 selectors to frozen bilingual publisher-grounded fixtures; add native-language semantic headline review and verified translation output tests. Do not silently treat unsupported scripts as translated.
4. B5 actual rendered PNG/SVG screenshot and 100% Discord-scale readability/clipping inspection; compare against existing page formats.
5. B6 D1 resource activation, retention and Drive backup are **separately gated**. B7 shadow comparisons may run only without delivery.
