# AggregateIT V2 — B36 offline evidence acceptance hardening

Date: 27 October 2026  
Branch: `rebuild/aggregateit-v2`  
Starting head: `ace636b7120a44790a154f5b5032487054f325f4`

## Scope and demonstrated defect

The existing B27 private evaluator took caller-supplied `live_parser_parity_proven` and two `real_device_verified` booleans as proof of independently measured live QA. A regression test showed all three self-declared values could elevate an otherwise offline rehearsal to `PRIVATE_ACCEPTANCE_MEASURED`.

B36 changes the evaluator to cap these unchecked inputs at `PARTIAL_OFFLINE`. It reports live claims separately as self-reported, without certifying external evidence or authorizing delivery.

The new `v2_b36_same_snapshot_scorecard.py` requires identical source rosters, revisions, source byte digests, product and observation windows, and distinct code revisions before producing an **offline diagnostic** scorecard. Run metrics are supplied by the caller and therefore remain unauthenticated. Different inputs yield HOLD with no deltas. No raw publisher bytes are included in result dictionaries.

## Verification

- Test-driven RED: forged live-claim test reproduced the prior measured-status defect.
- Test-driven GREEN: 4 B27 evidence-integrity tests passed locally.
- B36 snapshot scorecard: 7 additional focused tests passed locally using copies of its direct helper contracts.
- GitHub hosted full installed regression: **pending at first commit**; use the isolated `v2-b36-offline-evidence.yml` workflow run for authoritative results.

## Outstanding gates

Historical B34 France 24 Arabic parser 24 vs 23 discrepancy remains unresolved. B35 single new request returned HTTP 403; no request is repeated in B36.

Operational evidence checkpoints stay **6/8 (75%)**. Neither the genuine same-slot full V1/V2 editorial/model/render/delivery comparison nor the live canary/rollback acceptance is completed by this batch. The new B36 scorecard is a replay contract, not real execution evidence.

No changes to V1/main, production, schedules, webhooks, databases, cloud deployment or model routes; zero Discord messages and no publisher requests in B36.
