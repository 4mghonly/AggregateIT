# AggregateIT V2 — B14–B30 reconstruction evidence (26 October 2026)

## Recovery provenance

The owner chose **Option 2** after the unpublished execution workspace and its temporary Git bundle could not be located. This is a fresh, source-level reconstruction from the verified GitHub branch `rebuild/aggregateit-v2` at `109166a73092e3c5a8d2463fa393d3324980bbc7`, **not recovery of the twelve original commit objects**. The original local HEAD `701231256a3967ecb7dccae4980a9f78e264f009` and its historical hashes cannot be recreated. Any new commit is a successor to the published branch, with new hashes.

The reconstructed modules are functional replacements based on recorded requirements; their contracts **are not asserted byte-for-byte equivalent** to the lost code. No prior live/browser screenshots, source captures, external journal entries or publisher-byte proofs are fabricated or re-certified.

## Rebuilt engineering scope

| Lost batch | Reconstructed artifact | Verified capability | Open gate |
| --- | --- | --- | --- |
| B14 | `v2_b14_admission.py` | Match candidate URL, source feed, title, excerpt ID, native language, evidence timing; hold incomplete rows | Genuine authenticated article capture |
| B15 | `v2_b15_source_watch.py` | Stable source-health summary; unknown/unprobed separated, no auto-promotion | Live per-source freshness and publisher independence |
| B16 | `v2_b16_replay_contract.py` | Byte-derived SHA-256 manifest and offline re-verification | Retained original-byte package and independently held receipts |
| B17 | `v2_b17_release_gate.py` | Technical checklist: tests, parser parity, two products, routes, rollback, live same-window proof | Live proof and cutover approval |
| B18 | `v2_b18_private_digest.py` | Native English/Arabic source-linked private summaries, topic isolation, unique IDs | Model-backed analysis and real-content editorial QA |
| B19–B20 | `v2_b20_private_mobile.py` | RTL/LTR responsive private HTML, escaping, no outbound requests | Browser/phone visual QA on genuine content |
| B21 | `v2_b21_private_snapshots.py` | Immutable digest/size receipts for HTML, PNG and PDF, caller-owned bytes | Real browser/native captures and durable storage |
| B22 | `v2_b22_private_packets.py` | Separate EN/AR destination-key manifests, single message per channel, no-send | Actual attachment/output inspection |
| B23 | `v2_b23_compact_mobile.py` | Static markup audit for language, direction, viewport, responsive CSS, card counts | Real device width and screenshot verification |
| B24 | `v2_b24_editorial_diversity.py` | Honest missing-region and source concentration diagnostics | Complete target-region source data |
| B25 | `v2_b25_recovery.py` | Bounded manual recovery; stale preview marked, ambiguous states not replayed | Operational fault injection |
| B26 | `v2_b26_parser_shadow.py` | Two parsers run on the same source bytes, SHA-256 and drift reporting | Authenticated broad actual-source capture and parser parity |
| B27 | `v2_b27_private_acceptance.py` | Composition gate returns `PARTIAL_OFFLINE` or `HOLD` | Genuine V1/V2 comparison and mobile QA |
| B28 | `v2_b28_canary_rehearsal.py` | Symbolic rollback with frozen candidate and no repeat of ambiguous receipts | Live canary and authenticated receipt evidence |
| B29–B30 | `v2_secure_transport.py`; existing fetch wrappers changed | Validated public DNS IP is the TCP target, original TLS SNI/hostname/Host retained, same-origin redirects, bounded payloads, no HTTP/TLS retry | Egress firewall and actual pinned-feed transport runtime |

`v2_feed_probe.py`, `v2_large_feed_adapter.py` and `v2_a8_single_run.py` now use pinned HTTPS transport. Older URL/DNS helpers remain for backward compatibility; no URL-target connection relies on preflight-only DNS.

The existing B13 rights-held preview remains historical code. At the owner's direction, legal/rights qualification is excluded from the **new V2 B17 engineering acceptance**. This neither asserts redistribution permission nor changes production.

## Reproducibility and limitations

- B14–B28 tests use constructed fixtures. Live data, real-device QA, model calls, webhook delivery, new source promotions and actual rollback are **not measured**.
- B26 parser comparison requires the declared `feedparser` dependency; it is not a second human source validation.
- B18 private mobile HTML is a rebuilt review surface. It does **not** recreate lost Chromium screenshots or prove visual equivalence to the original work.
- All source-stage exceptions and recovery metadata remain no-send. Production scheduler and main branch are untouched.
- No paid calls, new database, D1/PocketBase, retention deletion, Cloudflare migration, Discord message, production workflow or schedule execution was initiated by reconstruction.
- Technical regression completion does not close B7 genuine same-window shadow or B8 cutover.

## Verification

Tests: `tests/test_v2_rebuild_b14_b28.py`, `tests/test_v2_b29_pinned_https.py`, full `tests/` and legacy `tests.py` (see final run record in tracker). Dependencies were installed into isolated `/tmp/aggregateit-v2-deps`; repository requirements and production environment were not modified.

## Residual decision

Reconstruction may be published to `rebuild/aggregateit-v2` with new commit IDs. Treat it as **partial source-level reconstruction**, not complete operational acceptance or restoration of missing original hashes. Live source, real-device and production-linked gates remain OPEN. Preserve no-post state until separately authorized.
