# AggregateIT V2 — B1/B2/B3/B5 isolated continuation

**Date:** 23 October 2026 (UAE). **Working branch:** `rebuild/aggregateit-v2`.
**Start:** `f6650c1c34415e79292592aceeac03d31eb65d31`; protected `main` observed unchanged at `c7a53e9f6ffa8167c8538b236af6d2bfaddabdf9` before work.

## B1 — historical Arabic suite adjudicated, safety contract preserved

The previous 55-case Arabic application suite showed 11 failures and three errors **identically on main and V2**. Reconciled only the branch test fixtures/expectations against independently inspectable current behavior:

| Prior failures | Count | Resolution/contract |
| --- | ---: | --- |
| Editorial/review/geography/Arabic digits/social attribution | 8 | Synthetic Iraq headline and summary now both name Iraq; sourced Lebanon test now cites an actual Lebanon source even when the *publisher* country is IQ. No geographic or review-validation gate weakened. Expected two-pass editorial sequence is exercised again. |
| Delivery receipt and timeout | 3 | One Discord message for a three-slide deck returns the message ID as a **string**, not a JSON-encoded list. A network timeout is **uncertain**, never an automatic triple retry; repeated send refuses until reconciled. This is the safer existing runtime behavior. |
| Source-audit recovery | 1 | Fixture includes a real region and verifies bounded eight non-Arabic/four Arabic audit retries, not old unlimited 18/6 rotation. |
| Workflow scheduling | 1 | Main is selected by the workflow event branch and four individual 02/08/14/20 UTC cron expressions; explicit `ref: main` is not required. Workflow file unchanged. |
| News card layout | 1 | Existing deliberate ten-secondary-story limit replaces obsolete three-secondary expectation; unique lead, secondary and UAE event identities still checked. |

**Post-reconciliation:** `python -B -m unittest arabic_newsletter.test_arabic -q`: **55/55 pass** in disposable dependency-installed Python 3.12. This is not evidence of live production delivery or editorial truthfulness and cannot justify enabling V2. Existing sender, schedule and production code were not changed.

Actual Arabic no-send CLI was also executed with the built-in **long synthetic fixture**:

`ARABIC_STATE_DIR=<disposable> python -B -m arabic_newsletter.run --sample --long --output <disposable>`

Result: `run_status.json` reports `render/ok`; three 3840×2160 PNGs; `render_report.json` reports `visually_shortened_blocks=0`; a reference text and briefing JSON were written into `/tmp` only. No `--send`, model probe, source fetch, webhook or external publication. No English live-equivalence claim.

## B3 — exclusive writer and crash-atomic head receipt prototype

New **`v2_evidence_store.py`** owns one local POSIX journal inside an existing caller-selected directory:

1. Persistent advisory `flock(LOCK_EX|LOCK_NB)` serializes cooperating writers *before* reading or appending.
2. Every journal append validates, flushes and `fsync`s as before, then updates a separate receipt through a same-directory temp file, `fsync`, atomic `os.replace` and directory `fsync`.
3. Reopen demands that the persisted receipt checksum, replayed SHA-256 chain, sequence, byte length and ledger counters agree; partial tails and committed-tail loss fail closed.
4. Interruption **after journal fsync but before head receipt** poisons the writer and refuses reopen. There is deliberately **no auto-truncate, silent repair or deletion**. A known-invalid command rejected *before I/O* does not poison subsequent valid work.

`tests/test_b3_exclusive_store.py`: **9/9 pass**, including same-process and separate-process lock contention, injected receipt failure, head tamper, trailing-frame truncation, incomplete journal/receipt pair, Unicode byte-accounting and correct rejection recovery. Earlier file-backed B3 regressions remain green in the full suite.

**Limit:** local advisory lock only; cooperating single-host POSIX writers. Receipt checksums/hash-chain detect accidental drift, **not authenticated publisher identity** or malicious rollback of both journal and receipt. No forced power-loss rig, Windows adapter, off-host signed checkpoint, collector integration or production DB proof. B3 remains PARTIAL.

### Follow-on B3 path-safety gate (same-day second batch)

After publishing the first checkpoint, a separate bounded hardening pass required an existing **non-symlink directory** and regular journal, receipt and lock files. File descriptors use `O_NOFOLLOW` (where POSIX supported) and `O_NONBLOCK` plus `fstat(S_ISREG)`, so symlink/FIFO file-substitution probes refuse instead of following arbitrary paths or hanging. The append descriptor now explicitly seeks to the verified journal byte-end before a text writer is constructed; the first post-hardening test run exposed this offset regression and it was fixed before closure. Added **three** targeted tests: symlinked root, symlinked receipt and FIFO journal. All **12/12** B3 exclusive-store cases subsequently pass.

This remains a cooperative-writer prototype, not a secure directory service: a malicious actor who can rename parent paths, bypass advisory locks or roll back both files is still outside its defended threat model. The operator must use a trusted isolated directory and independent off-host receipts in any later deployment design.

## B2 — single new permissive-source candidate; no admission

First-party [Global Voices RSS directory](https://globalvoices.org/feeds/) lists [Arabic RSS feeds](https://ar.globalvoices.org/feeds/). Its [republishing guidelines](https://globalvoices.org/about/global-voices-attribution-policy/) say Global Voices-authored material is CC BY 3.0 unless otherwise stated, including commercial adaptation if correctly attributed and changes disclosed. **Embedded third-party photographs/video/audio are expressly excluded unless their own permission permits reuse.** Treat this as a *candidate* for content-specific verification, not blanket feed/asset clearance.

One bounded, read-only metadata probe on `2026-10-23`: `https://ar.globalvoices.org/robots.txt` HTTP 200 and allowed the feed; `https://ar.globalvoices.org/feed/` HTTP 200, RSS mime type, **96,000-byte cap**, five partially parsed entries, parser `bozo=True` because the captured feed was truncated. The sampled top dates were **6–11 October 2026**, not a recent 72h source for 23 October. No bodies saved, no source registry addition, promotion, regional-floor or independent-family credit. The Arabic attribution-page link returned 404, but the official English policy was reachable; record this caveat if ever admitted. No repeated probes or scraping of restricted publishers.

## B5 — observed contrast defect corrected only on V2

An actual rendered Arabic sample image showed UAE story headlines drawn in the map decoration shade `#8B343B` over paper panel `#101D25`: computed relative luminance contrast **2.17:1**, too dim for paragraph/headline reading when downscaled. `arabic_layout/render_pages.py` now uses `UAE_HEADLINE_COLOR = ALERT` (`#D5646B`), with contrast **4.79:1** over the same panel. Dedicated tests compare the published renderer constant to the background and reject reuse of the low-contrast map shade. All other region colors and the three-page layout remain unchanged.

Synthetic `sample=True` pages now also print **«بيانات اختبار — ليست أخباراً حقيقية»** in the footer, avoiding confusion if an offline screenshot is copied. The sample-only marker never appears on a non-sample briefing. This is a **measured contrast repair and synthetic preview check**, not proof of final client visual acceptance. Noto Sans Arabic release font absent, Siraj Noir choice deferred, full mobile-scale typography/genuine text and source rights still pending.

## Run and authorization limits

- V2-focused installed suite (after the continuation edits): see completion receipt in the batch tracker; no live network, LLM or Discord calls.
- Legacy Arabic suite: **55/55 PASS** after contract fixture corrections; tests never hit Discord because POST is mocked.
- No main/production/workflow/secrets/CI changes, no Discord posts, no live model billing, no D1 or other DB provisioning, no deployment, no deletion.
- **Remaining:** B1/4 genuine source→translation→editor end-to-end; B2 lawful recent rights-qualified sources by region; B3 off-host attestation/power-loss stress; B5 release font/mobile text; B6 D1 authorization; B7 paired authentic no-post shadow; B8 separately approved canary/cutover.

**Decision:** B1–B7 stay PARTIAL; B8 BLOCKED. Source and typography policy decisions intentionally deferred under owner instruction.
