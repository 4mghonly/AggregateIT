# AggregateIT V2 — B40 full-system shadow acceptance investigation

Date: 27 October 2026  
Branch: `rebuild/aggregateit-v2`  
Starting SHA: `8a3075ce2f3e3e4368d00667cbb52e32c1900141`

## Scope and verification objective

B40 begins from genuine BBC World and Al Jazeera Arabic identical-buffer parser evidence (B38), then separately exercises the existing B3 evidence journal, B4 editors, real native 4K English two-page and Arabic three-page renderers, and actual Discord message/attachment *packaging* in NO-POST mode.

**Strict evidence boundary:** Live RSS parser input and the independently rendered five-page synthetic evidence fixture are different input corpora. Their outputs must **not** be compared as if they were a genuine shared-input, same-window newsroom benchmark. Without verified article-body evidence, executed legacy editorial/model/translation on identical snapshots, and authenticated delivery, B40 cannot close the final full-system comparison gate. No semantic or performance deltas are computed across the mismatched tracks.

## Deliverables

- `v2_b40_stage_acceptance.py`: stage-by-stage evidentiary HOLD and strict page/hash/destination validation. Can never release based on synthetic pages or caller-only flags.
- `v2_b40_private_chain.py`: read-only live-parser collection from B38; separately invoke real B3/B4/renderer/packaging against fixed synthetic fixture, verify 3840x2160 PNG dimensions, SHA-256 and one-message-per-product destination.
- `tests/test_v2_b40_stage_acceptance.py`: eight focused negative/positive assertions. Missing module import reproduced RED locally; the pure stage checks passed after implementation.
- Isolated branch-only push-path GitHub workflow, 20-minute limit, no secrets or Discord or model calls. Only redacted metadata is uploaded with 2-day retention.

## Acceptance state

B40 stage-specific results and hosted regression: **PENDING isolated GitHub Actions run**.

Genuine final V1/V2 editorial + translation + native page comparison: **HOLD**, not verified by this stage-specific rehearsal. Real Discord-client delivery/rollback: **HOLD** for B41. France 24 B34 24-vs-23 discrepancy still unresolved and not reprobed. User-approved legal-rights exclusion remains AggregateIT-only.

Progress bar: **6 of 8 checkpoints (75%) unchanged**; this is an evidence-gate fraction, not a production-readiness claim.

No production/main branch modifications, schedules, secrets, databases, paid model usage, or Discord posts.
