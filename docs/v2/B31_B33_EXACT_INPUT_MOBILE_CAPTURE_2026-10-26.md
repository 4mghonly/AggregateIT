# AggregateIT V2 — B31–B33 exact-input, private mobile and capture-import batch

**Date:** 26 October 2026  
**Working branch:** `rebuild/aggregateit-v2`  
**Parent checkpoint:** `2bf05de7e50dd6c3a8b66d5398e293726a45f2e3`

## B31 — actual V1 parser comparison, same feed bytes

The V1 reference was separately cloned at `cb10eb38c056755903434d1327de878b0d1d0b38` and **not modified**. The relevant production source files have identical Git blob hashes in V1 and V2:

- `main.py`: `6c7915ab5b46ee6220bc59657e28a2fb08d1ad86`
- `arabic_newsletter/collect.py`: `ddbcd27d959b0aea07e269b925539906c90ef340`

New `v2_b31_same_input_shadow.py` directly invokes unchanged V1 `main.fetch_rss` or `arabic_newsletter.collect.collect_source` with in-memory feed bytes and network/side-effects patched out, then runs V2 `v2_feed_items.extract_candidates` on **those identical bytes**. It binds the V1 module blobs, aligns the observation window and language-specific V1 item caps, records raw/eligible counts, hashed item identities, drift and exclusions, and refuses all publication. This is a **parser-stage comparison**, not a genuine same-slot V1/V2 edition quality or delivery comparison.

`tests/test_v2_b31_exact_input_shadow.py`: 9/9 focused PASS on synthetic English and Arabic RSS, stale inputs, V1 source drift and blocked network. Real publisher bytes remain absent.

## B32 — private responsive preview fixture and browser readiness

- `v2_b32_generate_mobile_fixtures.py` generates two source-safe synthetic private HTML previews with three cards per language. The original-language, RTL/LTR and CSS viewport structure passes `v2_b23_compact_mobile.audit_compact_markup`.
- `v2_b32_mobile_browser_qa.mjs` is an isolated Playwright/Chromium QA runner for 320, 390, 768 and 1320 px, with network routes aborted, clipping/overflow checks and emulated desktop/mobile screenshots. **Its browser-dependent acceptance did not run.**
- Browser installation attempted once in a disposable environment. Chromium download produced a truncated/non-ZIP artifact and failed; there is no installed browser binary. Do not claim visual screenshots or real-phone QA.
- `tests/test_v2_b32_mobile_fixtures.py`: 2/2 focused PASS. These verify fixture construction and static markup only.

## B33 — offline future authenticated-capture import bridge

`v2_b33_capture_comparison.py` consumes bytes and a matching SHA-256/size receipt, runs B26 independent parser comparison and B31 V1/V2 same-input comparison, returns only hashed/count metadata and stays non-sendable. Matching a supplied hash **does not independently authenticate publisher origin**. The importer therefore always reports `external_provenance_authenticated=False`. `tests/test_v2_b33_capture_comparison.py`: 5/5 focused PASS, synthetic fixtures only.

## Source access constraint — stop after three different attempts

1. Pinned public-IP HTTPS: registered BBC Middle East RSS URL failed at DNS resolution (`socket.gaierror`), before TCP.
2. Environment-configured verified HTTPS proxy: bounded HTTP request timed out during proxy tunnelling.
3. Public web reader: publisher RSS endpoint was rejected because the viewer does not handle XML media types. It did not provide raw source bytes.

No source body or RSS bytes were acquired by these attempts. No first-party original-byte SHA can be asserted from this batch. Further identical retries are not justified. The exact-byte B33 importer is ready when an authorized execution environment can fetch source bytes.

## Verification and remaining acceptance

Complete dependency-installed test results: **505/505** V2 `unittest` suite PASS, **153/153** legacy `tests.py` PASS and **55/55** Arabic `unittest` PASS. Static JavaScript syntax check for `v2_b32_mobile_browser_qa.mjs` also passed. Neither V1 `main` nor V2 production webhooks, schedules, Cloudflare, database, or live GitHub Actions were modified. No Discord message, paid API call, model inference or production migration occurred.

| Gate | State | Evidence |
| --- | --- | --- |
| B14–B30 reconstruction published | VERIFIED | Previous remote commit `2bf05de` |
| Full offline regression | VERIFIED | Dependency-installed `tests/`, legacy and Arabic suites |
| V1/V2 same-byte parser bridge | VERIFIED **on synthetic** | B31 focused tests and immutable V1 source blob check |
| Static private mobile fixtures | VERIFIED **on synthetic** | B32 static markup tests |
| Authenticated original RSS bytes | HOLD | Three access approaches unavailable |
| Browser/mobile visual QA | HOLD | Chromium binary unavailable; no real-phone screenshots |
| Genuine same-slot V1/V2 editorial+delivery comparison | HOLD | No identical real capture pair or V1/V2 run artifacts |
| Canary/rollback production acceptance | HOLD | Symbolic B28 tabletop only |

**Completion bar definition:** Four of the eight explicit evidence checkpoints above have locally verified results. This is **4/8 evidence checkpoints**, not a claim that the V2 product is 50% deployable. Operational release remains **HOLD**.
