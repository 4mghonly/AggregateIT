# B126 — bilingual weekly roster and V1/V2 editorial-selection divergence

Date: 2026-11-13 UTC. Branch: `audit/b119-evidence-reconciliation`. Candidate SHA (immutable): `b67a9e4115f4f88049716d608e54a6d06ef5f15f`.

## Implementation
- `v2_b126_weekly_editorial_audit.py`: fail-closed 7-day window, candidate SHA, B125 authenticated-evidence result, bilingual positive selections, selection arithmetic, and duplicate/missing date validation.
- `v2_b126_offline_audit.py`: no-network CLI with explicitly supplied B115 paired receipts and B125 independently reconciled report.
- `v2_b119_release_readiness.py`: distinct `b126_attributed_weekly_bilingual_source_roster` gate. Does not change `v2_weekly_both_languages_seven_real_days` or full-model-parity HOLD.
- Tests: 22 B119/B125/B126 focused tests passed; RED tests were observed before implementations. No repository-wide test claim.

## Authenticated historical evidence
The B125 authenticated GitHub artifacts for 2026-11-06 through 2026-11-12 were reused without any new workflow dispatch. B126 live offline CLI returned exit 0, `source_roster_seven_days=true`, `selection_disagreements_observed=true`, `issues=[]`, `release=HOLD`.

| Language | V1 selected | V2 selected | Both | V1 only | V2 only |
|---|---:|---:|---:|---:|---:|
| English | 31 | 42 | 28 | 3 | 14 |
| Arabic | 60 | 42 | 23 | 37 | 19 |

These are seven-day *aggregate selection counts*, not per-story matched editorial judgments. They do not prove model or translation quality, parity, or which selection is better.

## Remaining acceptance
The original B119 `v2_weekly_both_languages_seven_real_days` gate refers to a full weekly four-product reporting requirement. B126 proves only the source-linked bilingual roster and must not override that gate. Full model/editorial parity, Arabic translation fallback, same-slot visual equivalence, authenticated delivery and rollback, independent adjudication, publisher rights/factuality remain HOLD.

Next: produce a source-identity matched per-story V1/V2 disagreement review queue, inspect independent editorial decisions and test the full weekly analytical product without production delivery. No model calls or publisher rights inferred. No protected branch or database modifications.
