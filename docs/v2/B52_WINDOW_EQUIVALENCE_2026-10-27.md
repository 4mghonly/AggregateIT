# B52 — V1/V2 shadow window timezone reconciliation (27 October 2026)

## Issue and isolated correction
`v2_shadow_scorecard.compare_runs` and `v2_a9_shadow_readiness.classify_shadow_pair` compared offset-aware ISO8601 strings literally. The same real window written at 06:00–12:00 UTC+04 and 02:00–08:00 UTC was wrongly labelled `different_product_or_window`.

Both gates now normalize the already validated offset-aware timestamps to UTC instants through the same `_window_identity` helper. This permits equivalent timestamps only; different instants, products and invalid timestamps still reject. Source labels and original time strings in scorecards are preserved.

Four regression cases cover equivalent instants, different instants and the unchanged requirement for distinct revisions and caller attestation. Local isolated timestamp reproduction: original behavior failed for equivalent instants, normalized comparison passed the positive and negative controls. The repository's full Python regression suite has **not** been run in this execution environment (remote clone/network unavailable); hosted verification remains open and must be recorded before treating this patch as fully tested.

## Unchanged safeguards and open gates
No genuine V1/V2 matching originals were created. `delivery_authorized` remains false. Attestation stays caller-asserted, not independently authenticated; live B45 translation/fallback, publisher-rights clearance, 7-day source completeness, B49/B7 real full-edition shadow and B50/B8 cutover remain **HOLD**. No publisher request, paid model, secret, database, CI dispatch, Discord, schedule, or production-main operation was performed.

Production Source Health Audit #40480137867 failed because `main` workflow installs `aiohttp feedparser` but omits `requests`; the V2 isolated branch's `.github/workflows/audit.yml` already installs `requests`. The correction to production would require separately authorized main change, which was not made.

### Verification record
- Branch before patch: `ff4d4d9617470e34fcabeaf76a48f657415244ae`
- Changed source: scorecard and readiness gate
- Changed tests: `tests/test_b6_b7_shadow.py`, `tests/test_v2_a9_shadow_readiness.py`
- Source tests scheduled for normal future no-post verification only; no workflow was dispatched.
- Planning 60% and formal 6/8 gates unchanged.


## B52 verified in combined CI

B7 18/18 and A9 9/9, complete V2 677/677 PASS in Actions 40551560501. UTC-equivalent comparison correction verified; actual run source attestation and canary remain HOLD.
