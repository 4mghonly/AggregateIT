# October 14 production health repair

## Changes

- Arabic translation requests contain one story instead of three, with a 4096-token output allowance. Partial or invalid translations remain excluded. Numeric fidelity checks remain strict.
- English tries each configured route before spending budget on repair. A truncated/empty response gets one larger bounded repair (maximum 8192 tokens). Runtime options cannot overwrite the evidence, model or output allowance. Validation failures emit allowlisted diagnostic codes, never provider bodies or credentials.
- Arabic analysis uses 4096 tokens and a single schema repair up to 8192; a separate stage deadline still bounds the attempt sequence.
- Arabic collection can retain up to three UAE items from the previous 24 hours only when the current window has none. Original publication timestamps are preserved and the summaries explicitly label them as prior context. This cannot guarantee news where no dated source evidence exists.
- Pin Arabic and English delivery channels to their verified channel IDs, while retaining explicit configured overrides. Distinct webhook secrets remain in use.
- Persist host cooldowns after HTTP 429; avoid repeated requests during the cooldown. Reddit audit now checks the same OAuth/archive paths production uses instead of unauthenticated RSS. Missing access remains a visible failure.
- The Independent endpoint changed to its working world RSS feed. IntelNews uses its working canonical trailing-slash URL. Yahoo's 404 feed is disabled with a recorded reason; existing Bloomberg/CNBC/MarketWatch feeds retain market coverage.
- Independent Cloudflare scheduler and production slot gates are implemented. Tests cover accepted dispatch receipts, native-run races, slot boundaries and duplicate suppression. **External scheduling is not active:** the existing AggregateIT Worker has no GitHub dispatch credential. See ops/README.md.

## Verification

- Core: 153 passed, zero failed.
- Focused Python recovery/layout/cadence checks: 30 passed.
- Scheduler Node tests: 3 passed.
- Workflow YAML/config JSON parsing and diff checks passed.
- First independent live probe: both English Gazette routes, both English event routes, both single-story Arabic translation routes and fallback Arabic analysis passed. Primary Arabic analysis failed its first schema check. Follow-up independently passed both Arabic analysis routes through the production repair path.
- GitHub core/Arabic/Gazette CI passed on the first repair commit; the follow-up probe passed primary and fallback Arabic analysis (11.4s and 11.0s).
- Source checks from this environment: Independent world RSS HTTP 200/71 entries; IntelNews canonical feed HTTP 200/30 entries. Reddit fallback had an obsolete hostname/path and unsupported sort syntax. Updated against the upstream API documentation; the corrected endpoint returned HTTP 200 and three fresh r/stocks items.

## Remaining access and production verification

- A persistent fine-grained GitHub Actions dispatch credential is required to activate Cloudflare cadence; the connected GitHub app cannot export one. No secret was requested in chat or copied from an unrelated project.
- Reddit OAuth remains unconfigured. The repaired public archive fallback returned fresh posts, but its uptime and comment-search coverage cannot be guaranteed. Official authenticated access remains preferable.
- No Discord messages or full production editions were manually triggered. A successful live probe demonstrates structured API output, not end-to-end production delivery. Confirm the next scheduled editions and output artifacts after rollout.
