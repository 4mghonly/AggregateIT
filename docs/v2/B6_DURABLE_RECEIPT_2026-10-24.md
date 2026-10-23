# AggregateIT V2 — B6 local durable receipt-failure rehearsal

**Date:** 24 October 2026 (UAE). **Branch:** `rebuild/aggregateit-v2`.
**Scope:** Offline, no-post experiment. No database, network, Discord, CI or live slot operations.

## Demonstrated issue

The existing `v2_delivery_gate.ReceiptGate` kept the state of an attempted send
only in memory. If a process terminated after marking an ambiguous outcome,
reinitialization lost that knowledge and could incorrectly consider the slot
new. No production sender used this prototype, so this is a **prototype
reliability gap**, not evidence that production duplicated a message.

## Implemented seam

`v2_delivery_receipt_store.DurableReceiptStore` keeps the existing B6 state
machine and destination policy but persists all slot transitions to an
operator-provided **existing local directory**. It uses a POSIX exclusive
lock, strictly validated/checksummed JSON snapshot, exclusive reservation,
write/fsync/rename/directory-fsync before returning a changed state, and
safe reopen. Both an English and an Arabic slot can coexist independently.

- `reserve` must complete before a candidate would initiate delivery.
- `mark_network_attempt` must persist **before the hypothetical first network
  byte**. Reopening an ambiguous slot forbids automatic retry.
- A caller-asserted message ID remains `confirmed_unverified`; it cannot
  masquerade as an authenticated Discord receipt.
- Checksum mismatch, missing state with existing lock marker, symlinks,
  invalid restored state, collision and second concurrent local writer refuse.
- A failed persistence call poisons the active object. Recovery requires
  closing and reopening; no automatic rollback, repair or deletion occurs.

This module **has no code to send**. Nothing in production has been switched
to it. There is no cross-host coordination, trusted off-host state anchor,
filesystem adversary-proofing, or Discord receipt reconciliation. Loss of
both local snapshot and marker, or coordinated rollback, remains an untested
external integrity threat. For production, sender ordering and crash recovery
need independent verification and approved deployment design.

## Additional B7 assertion hardening

The B7 offline scorecard refused implausible `items_rendered > items_cited`
in the preceding batch. This batch additionally rejects
`clipped_items > items_rendered`, omissions exceeding selected events, and
`delivery_status=confirmed_external` because its manifest has **no external
receipt proof field**. A verified delivery claim requires a separately
authenticated service path, not a caller-supplied string.

## Test evidence

- Focused B6 durable receipt suite: **10/10 PASS**; exercises actual abrupt
  process exit via `os._exit`, restart, persistence failure, tamper, bounded
  slots and two independent products.
- Focused B6/B7 offline scorecard suite: **16/16 PASS**, after two regression
  checks first failed on the prior code as expected.
- Final combined installed-dependency V2 suite: **220/220 PASS**. The preceding
  batch's 208/208 checkpoint was revalidated before this change.
- Independent Arabic application suite **55/55 PASS** (mocked Discord/model),
  and original English Gazette layout **6/6 PASS** (local synthetic output).
- No sends, model calls, database provisioning, deletions, workflow dispatch
  or production modifications.

## Remaining gate

B6 stays **PARTIAL**. Durable local state is a necessary rehearsal but not
operational exactly-once Discord delivery, verified external receipts,
scheduler operation, live alerting, analytics backing store, Cloudflare D1,
or approved retention. B7 remains **PARTIAL** without genuine synchronized
V1/V2 source windows. Do not publish or promote either on synthetic evidence.
