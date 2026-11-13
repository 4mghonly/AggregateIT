# B127 — source-identity matched editorial disagreement acceptance

Date: 2026-11-13 UTC. Repository: `4mghonly/AggregateIT`. Development branch: `audit/b119-evidence-reconciliation`. Immutable candidate: `b67a9e4115f4f88049716d608e54a6d06ef5f15f`.

## Implementation and evidence
- `v2_b127_identity_review.py` matches each B124 V1/V2 disagreement against exact source URL SHA256, the V2 source roster and B126 seven-day aggregate counts. Missing/duplicate/contradictory identities fail closed. It preserves rejection reasons, not publisher text.
- `v2_b127_offline_audit.py` is a bounded, offline reproducible CLI. Inputs: ordered arrays of the seven `b124_editorial_review_queue.json` artifacts and seven `b120_daily_source_roster.json` artifacts, plus `b126_weekly_editorial_audit.json`; candidate SHA required.
- `v2_b119_release_readiness.py` now surfaces a separate `b127_identity_matched_disagreements` gate. No editorial adjudication, rights, visual/model/delivery or release gate is automatically promoted.
- The 73-row review artifact is committed at `docs/evidence/B127_IDENTITY_REVIEW_2026-11-06_TO_12.json`. No article bodies or headlines included. `analyst_reviewed=false`, `materiality=UNASSESSED`, `publisher_rights=UNVERIFIED` for every row.

## Authenticated historical reconciliation
Seven GitHub Actions acceptance artifacts for UTC 2026-11-06 through 2026-11-12 were reused (same run IDs and candidate SHA as B125). No new workflow dispatch. B127 CLI returned exit code 0, `evidence_reconciled=true`, `disagreement_count=73`, `issues=[]`, `review_status=PENDING_INDEPENDENT_REVIEW`, `release=HOLD`.

| Selection disagreement | English | Arabic | Total |
|---|---:|---:|---:|
| V1 only | 3 | 37 | 40 |
| V2 only | 14 | 19 | 33 |
| Total | 17 | 56 | 73 |

73 selection instances represent 65 distinct source URLs across the seven dates. The same source may recur on different dates; each date/product/identity is independently reviewable.

### Recorded V2 rejection reasons for V1-only selections
| Reason | English | Arabic |
|---|---:|---:|
| no_grounded_region | 0 | 12 |
| article_body_container_missing | 0 | 9 |
| arabic_topic_without_explicit_trigger | 0 | 7 |
| rank_diversity_or_page_budget | 3 | 6 |
| arabic_not_security_relevant | 0 | 2 |
| ambiguous_geography | 0 | 1 |

These are **system-recorded reasons**, not independently validated reasons or correctness judgments. Distinguish extraction failures (`article_body_container_missing`), grounding failures (`no_grounded_region`), topical relevance decisions and budget/ranking decisions before proposing changes. Arabic has 56 of 73 differences, warranting prioritized review but not automatic assumption of a defective model.

## Testing and acceptance boundaries
Observed RED tests before implementation, followed by 9/9 B127 tests passing. B119 integration was tested RED then GREEN. The final B119/B125/B126/B127 focused regression ran 32 tests: all passed. The complete repository-wide test suite was not executed. Real seven-day B127 audit: passed.

**B127 development and evidence reconciliation: COMPLETE.** **Independent editorial adjudication: NOT COMPLETE.** Full V1/V2 model parity, Arabic translation fallback, four-product weekly reporting, same-slot visual equivalence, authenticated delivery/rollback and publisher rights/factuality remain HOLD. No protected branch, database, publisher service, or production system was changed.

Next batch should be B128: independently adjudicate the 73 source-identity disagreements using a defined rubric and document individual dispositions, then test full weekly analytical-product parity without production posting. Do not promote gates from aggregate statistics or unverifiable reviewer flags.
