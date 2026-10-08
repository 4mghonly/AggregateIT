# Aggregator health repair — 8 October 2026

## Scope and evidence

Production main baseline: `b82027c5585dfd4e4336b662a6980be06d75db84`.
Arabic development branch remains separate; main owns the current V3 production path.

- Arabic run 37750036552: primary translation rejected, fallback read timeout;
  primary analysis schema rejected, fallback read timeout; degraded deck delivered.
- Arabic run 37833964360: analysis recovered on primary but translation still failed,
  zero translations and zero UAE selections; deck delivered with green workflow status.
- English run 37763484901: four malformed-output failures; 495 fetched articles;
  all logged social lanes empty.
- Observed GitHub schedules run late and fewer times than configured. Shared Actions
  concurrency has one pending slot, so competing workflows can replace pending jobs.
  This is a preventable contributor, not proof of the cause of every scheduling gap.

## Repairs

- Validate usable, complete JSON and the consumer schema before accepting an English
  response or caching it. Malformed HTTP 200 responses now trigger bounded repair and
  independent failover. The ten-call engine budget counts physical requests.
- Arabic translation uses batches of three, retries missing/invalid rows on fallback,
  preserves numeric facts, and marks partial coverage as degraded. One read timeout
  switches routes immediately. Translation/analysis have bounded stage budgets.
- Arabic analysis retries schema failures as well as malformed JSON, validates Arabic
  text, and restores the independent `probe_llms` function used by existing workflows.
- Arabic health evidence and the single Discord deck caption flag translation,
  analysis, empty-event and UAE coverage issues even when delivery succeeds.
  Gazette health is written separately from its delivery confirmation.
- Only the engine writes the canonical `engine-state-` database cache. Gazette and
  readers restore without saving it; market JSON and Gazette reports use separate
  namespaces and concurrency groups. Legacy prefixes are read for migration.
- Read-only overdue-run watchdog and a daily English source audit expose missed jobs.
  GitHub schedule delays remain possible; this is not an exact-time delivery guarantee.
- Three official Arabic Abu Dhabi Media Office feeds and one English feed were verified
  with HTTP 200 and 24 parsed entries each before inclusion. Government feed newest
  entry: 7 October; security: 2 October; crown-prince: 5 October. Quiet feeds are not
  fabricated into fresh news.
- CSIS feed returned items dated 2016, Oryx latest item dated 2024, and CISA feeds returned
  HTTP 403 in this environment. Pause these specialist lanes pending re-audit; add
  verified Cloudflare Security and Bellingcat feeds (HTTP 200, dated entries).
  Social source telemetry distinguishes disabled, transport failure and quiet/stale.
- Undated/future RSS and social records are not assigned fabricated current timestamps.

## Verification and remaining limitations

- Core regression: 153 passed, zero failed.
- Recovery plus Gazette layout: 21 tests passed, zero failed.
- Production Arabic V3 CI assertions and three-page sample render passed locally.
- Python compilation, workflow YAML parsing and whitespace checks passed.
- Legacy V1 Arabic suite: 55 tests, 11 failures and 3 errors, reproduced unchanged
  on baseline main. These tests assert retired synthesis/delivery/layout contracts;
  they are not silently treated as a passing production V3 gate.
- Live credentials are available only in GitHub Actions. Local mocked failover proves
  control flow; actual provider latency, current credential/quota health and production
  delivery with this branch require a post-merge read-only route probe and scheduled run.
- HTML extractors now read publisher publication metadata with at most four article
  date probes per source. Undated articles are excluded and reported as unverified.
  Publishers without supported date metadata can therefore show reduced coverage;
  they are not represented as freshly published articles.
- Discord expected-channel settings were empty in inspected runs. Receipts confirmed
  distinct existing channels, but pinning them requires deployment configuration.
- No production editions were posted during this repair. No credentials were changed.

## Rollout

Review and merge the fix branch. Existing production schedules then use the repairs.
Run the existing Arabic route probe to test both configured engines independently;
inspect the next Arabic and English health artifacts and Discord receipts. Provider
failures or remaining external scheduling delays must remain visible as degraded health.
