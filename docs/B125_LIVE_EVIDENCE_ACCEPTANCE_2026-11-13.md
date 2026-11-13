# B125 — authenticated live-evidence acceptance (2026-11-13 UTC)

Candidate: `b67a9e4115f4f88049716d608e54a6d06ef5f15f` on `rebuild/aggregateit-v2`.

Independent procedure: downloaded **both** GitHub Actions artifacts for each of the seven runs, parsed `b115_paired_run.json` and `b120_daily_source_roster.json`, retrieved authenticated GitHub workflow run metadata, then ran `v2_b125_offline_audit.py` from development commit `77a455729f2cbae2b6dd838ff524c806b77489db` with `--pairs`, `--rosters`, `--github-runs` and `--candidate-sha`. No workflows dispatched. No production actions.

| UTC date | GitHub run ID | Actual EN selected | Actual AR selected | EN roster stories | AR roster stories | Capture hash match |
|---|---:|---:|---:|---:|---:|---|
| 2026-11-06 | 42178164780 | 6 | 6 | 6 | 6 | Yes |
| 2026-11-07 | 42350027604 | 6 | 6 | 6 | 6 | Yes |
| 2026-11-08 | 42457140720 | 6 | 6 | 6 | 6 | Yes |
| 2026-11-09 | 42578138140 | 6 | 6 | 6 | 6 | Yes |
| 2026-11-10 | 42773499997 | 6 | 6 | 6 | 6 | Yes |
| 2026-11-11 | 42976665261 | 6 | 6 | 6 | 6 | Yes |
| 2026-11-12 | 43173201641 | 6 | 6 | 6 | 6 | Yes |

All GitHub runs: workflow `.github/workflows/v2-b80-b83-live-acceptance.yml`, branch `rebuild/aggregateit-v2`, pinned head SHA, `completed/success`. Each B115/B120 pair shares UTC date, observation timestamp and capture manifest digest; all observations are within the bounded GitHub run-start window.

**Observed CLI result:** exit code 0, `seven_verified: true`, `issues: []`, seven unique consecutive dates, `release: HOLD`.

**B119/B95 interpretation:** The 12 November `b95_b97_history.json` reports seven English and seven Arabic days and `seven_day_evidence_met: true`. The latest B119 still reports `v2_weekly_both_languages_seven_real_days: false`; this is a *different* four-product reporting gate and must not be auto-promoted by B125. The remaining B119 failures also include full V1/V2 editorial/model parity, Arabic fallback parity, same-slot visual equivalence, authenticated delivery/rollback, independent editorial adjudication and publisher rights/factuality.

**Boundary:** This report authenticates a seven-day same-capture roster history, not the accuracy or legal rights of the source articles, the V1 model, visual equivalence, or delivery. The existing immutable acceptance candidate and production remain untouched. No synthetic backfills. Release **HOLD**.
