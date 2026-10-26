# AggregateIT V2 — B34 GitHub-hosted acceptance closeout

**Date:** 26 October 2026
**Branch:** `rebuild/aggregateit-v2`
**GitHub Actions run:** https://github.com/4mghonly/AggregateIT/actions/runs/40388155216
**Trigger commit:** `58d5adc4df1b9c4694e23947ab0aefd400670941`
**Production/main:** `cb10eb38c056755903434d1327de878b0d1d0b38` (unchanged after execution)

## Result and scope

The isolated `push`-only V2 workflow ran once and completed **SUCCESS**
(2026-10-26 19:35:51–19:36:56 UTC). Both jobs succeeded.
GitHub-hosted public runner, no production key access, no Discord post,
no LLM invocation, no DB write, no source-registry write, no deployment.

- Focused B34 safety tests: **5/5 PASS**.
- Full V2 Python suite: **510/510 PASS** (includes those five).
- Legacy English suite: **153/153 PASS**.
- Legacy Arabic suite: **55/55 PASS**.
- Chromium: **8/8 PASS** at EN and AR × 320/390/768/1320 px. No
  horizontal overflow or JS page errors, correct `lang`/`dir`, all
  three synthetic cards present and horizontally bounded. Four synthetic
  PNG screenshots and a JSON QA receipt uploaded. This was emulated
  Chromium, **not** real-phone or actual live-news editorial QA.

## Four authenticated-transport captures (metadata only)

All four publisher RSS endpoints returned HTTPS 200 using public-IP-pinned
TLS with hostname verification; each byte buffer was fed unchanged to V1,
V2 and independent feedparser comparisons. Source body bytes were **not
retained** in the repo, artifact or logs. The recorded SHA-256 values bind
the observations to what the runner fetched, but no publisher signature,
per-article license clearance or third-party attestation was obtained.

| Publisher/feed | Bytes | SHA-256 | V1 eligible | V2 eligible | Aligned |
| --- | ---: | --- | ---: | ---: | --- |
| BBC World | 21,738 | `be8248157cf080a0d4468d244339ae99d2efccf09f71d27265e66c0105796f63` | 5 | 5 | Yes |
| BBC Middle East | 18,451 | `0e6c9058c8c2469fcbc631418e29a5781bc9647b407e7f1475137e626f723a5e` | 5 | 5 | Yes |
| Al Jazeera Arabic | 26,974 | `9bdcc0715b42b5f68682590ab42bfd0d53348a7715eeb4b737b68e0ae50b8afb` | 25 | 25 | Yes |
| France 24 Arabic | 41,930 | `83463985e4829305dfa5c73dca5c01f49f4af912f219bd9d91ef69282c2ebc57` | 24 | 23 | **No — one V1-only item** |

Independent parser comparison also agreed exactly for BBC World (28/28),
BBC Middle East (11/11) and Al Jazeera (25/25). For France 24,
feedparser yielded 24 candidates versus 23 in V2's stdlib parser.
**The reason for this one-item exclusion is not established** by the
sanitized artifact; there is no saved body to inspect. Do not silently
discard the mismatch, call parser parity complete, or refetch without a
separately bounded diagnostic plan.

## Artifacts and integrity

- Source metadata-only ZIP, artifact **12680124255**, SHA-256 of
  artifact ZIP `ca8b937df542edc22496f2907ca4c0b89579c49d8e204cee6afe9b56479fe860`.
- Synthetic Chromium QA ZIP, artifact **12682111952**, SHA-256 of
  artifact ZIP `43d9f764222ad4451727b473f529b99841fbf0c275ac6bc99cada9dbfb062cdb`.
- Both have three-day retention, scheduled to expire **29 October 2026**
  around 19:36 UTC; repository and artifacts are public, so no raw
  publisher RSS or private information was uploaded.
- Run/job logs demonstrate installed-browser binary, network capture,
  all regression counts and no-post checks.
- Original RSS content is not available for an independent same-byte
  replay after the runner ends; the receipts provide hashes and counts only.

## Checkpoint disposition

| Objective evidence checkpoint | Status after B34 |
| --- | --- |
| Reconstructed V2 code published | CONFIRMED |
| Full installed offline regression | CONFIRMED |
| Synthetic same-byte actual V1/V2 parsing | CONFIRMED |
| Static private mobile markup | CONFIRMED |
| Bounded original RSS source capture on authenticated TLS | CONFIRMED (receipt only, 1/4 feeds with parser drift) |
| Chromium responsive layout, emulated mobile | CONFIRMED (8/8 synthetic; physical-device QA unmeasured) |
| Genuine same-slot full V1/V2 editorial, model, graphics and delivery comparison | HOLD |
| Canary and rollback operational acceptance | HOLD |

**Evidence bar: 6/8. Production-readiness percentage is not established.**
The green workflow means its scoped execution steps passed; it does **not**
mean RSS parser parity, genuine editorial quality, real phone UX, publication
rights or release approval.

## Next bounded question

Investigate why France 24 Arabic returns one V1-only item. A future
runner-side aggregate rejection-breakdown diagnostic can expose only
hashed/membership and reject-class counts, with one bounded source fetch,
if separately approved. No repeated B34 Actions run is scheduled: only
changes to the workflow file on the V2 branch satisfy its push filter.
