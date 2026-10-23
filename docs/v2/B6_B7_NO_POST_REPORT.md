# AggregateIT V2 — B6b / B7a No-Post Continuation
Date: 23 October 2026 (UAE)
Branch: `rebuild/aggregateit-v2`
Status: **experimental simulation contracts; no production delivery or live shadow job**

## B6b — Delivery receipt gate
- `v2_delivery_gate.py` is an in-memory, no-network product+slot reservation and acknowledgement model.
- Product endpoints are segregated: `english -> discord_webhook`, `arabic -> discord_webhook_arabic`. These are symbolic secret names, not actual URLs or credentials.
- Repeated reservation with identical digest is idempotent. Changing the content of a reserved slot is rejected.
- A recorded outbound-attempt ambiguity blocks retry by default; a claimed message receipt remains explicitly **unverified by Discord**. A wrong-channel receipt is rejected.
- **Still required:** transactional persistent reservation and message receipts, exact external reconciliation, duplicate-send fault injection, crash recovery, scheduler proof, and owner-approved controlled canary. The simulation never posts.

## B7a — Same-window V1/V2 metric comparison
- `v2_shadow_scorecard.py` validates explicitly supplied run manifests and refuses comparisons unless product and window match.
- Compares separately: usable sources, event selections, cited/rendered items, translation attempts/success, layout omissions and clipping; identifies lost/gained region keys.
- It will not collapse metrics into a spurious universal score. Publisher independence, source rights and factual accuracy remain **unverified/not measured**.
- Every scorecard says offline comparison only and `delivery_authorized=false`.
- **Still required:** genuine frozen same-window production V1 and isolated V2 captures, recorded evidence provenance, real scaled render and no-post shadow verification over repeated cycles.

## Synthetic proof
- 6 receipt gate plus 7 scorecard tests passed.
- Combined B3–B7 offline in-memory `unittest` run: **96/96 PASS** = 83 previous B3–B6 plus these 13.
- No installed-dependency full suite, filesystem crash recovery, Cloudflare D1, news feed checks, model inference, actual delivery, Actions or paid infrastructure.

## Boundaries / next permission gate
- B1/B2 live acceptance, B3 real collector/bytes, B4 verified translation and claim-fidelity, B5 screenshot legibility, B6 durable receiver/scheduler and D1 budget proof are outstanding.
- B7 is PARTIAL by design. Do not run or dispatch V1/production workflows, send test Discord posts or make any B8 cutover until explicitly approved.
