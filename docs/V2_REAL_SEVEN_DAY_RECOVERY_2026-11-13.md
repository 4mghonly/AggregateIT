# AggregateIT V2 recovery — real historical evidence and acceptance

Date: 2026-11-13. Development branch: `audit/b119-evidence-reconciliation`.

## Proven historical data, not synthetic fixtures

The 2026-11-07 through 2026-11-13 daily English baseline was recovered from existing GitHub Actions `intel-report` artifacts. The corresponding Arabic V2 editorial briefings were recovered from `arabic-v2-*` artifacts. Each source artifact is an existing GitHub Actions output, not a generated historical observation.

Arabic artifact IDs (Nov 7–13): `13577291060,13588224969,13631864661,13706348417,13799600814,13951542206,14044418018`.

English V1 artifact IDs (Nov 7–13): `13595225142,13639150027,13719316995,13812311307,13899263741,13993547194,14056072113`.

Offline import results: **Arabic V2 91 observations, 7 distinct days, 91 source-URL-based events**; **English V1 48 observations, 7 distinct days, 47 V1 event IDs**. Both generated weekly HTML and a shared SQLite history. The English archive is a V1 comparison baseline, **not proof of V2 English parity**. Source-URL identity is intentionally conservative and may split one real-world event across multiple sources.

Reproduction: GitHub Actions workflow `.github/workflows/v2-seven-day-real-recovery.yml` on the development branch downloads the existing artifacts with read-only Actions permissions, runs recovery tests, imports both histories, generates bilingual weekly HTML, and retains the SQLite database and previews as a run artifact. No Telegram or Discord send is invoked.

## Technical changes

- `v2_recovery_arabic_archive.py`: reads real `arabic-brief-v3` JSON from ZIP or file, validates real source links, collapses same-day observations, rejects synthetic briefs.
- `v2_recovery_english_archive.py`: reads V1 `run.json` event observations as historical comparison baseline.
- `v2_recovery_pipeline.py` and B46 runner: optional bilingual editorial history persistence and weekly preview.
- `v2_product_recovery.py` and `v2_recovery_publication.py`: seven-day observation/change tracking, source links, evidence-bounded assessments, compact HTML.
- `arabic_layout/render_pages.py`: page-three category panels are content-adaptive, excluding empty militant, maritime, or conflict categories rather than manufacturing filler.
- Focused regression tests and an isolated, no-send GitHub Actions workflow.

## Editorial caveats and outstanding release gates

1. V1 and V2 editorial comparison on matched input evidence, including relevance and completeness, is not yet a demonstrated PASS.
2. Seven days of observations are now available, but seven days of **substantive** model-backed analysis and forward-indicator review have not been independently accepted.
3. The weekly recovery HTML is an inspectable preview, not the existing English/Arabic Telegram daily or weekly publishing product.
4. The Arabic real-image render is exercised separately, but English daily image layout and full Telegram end-to-end delivery remain unaccepted.
5. V2's source attribution and translated claims are not independently verified factual assertions. Publisher-rights status is tracked but is not treated as the sole technical release gate.
6. Do not alter V1 production or the protected `rebuild/aggregateit-v2` release branch until the candidate is demonstrated superior.

**Release state: HOLD pending editorial, rendering and delivery acceptance.** Historical evidence availability itself is no longer the blocker.


## Verified live GitHub Actions acceptance (isolated development branch)

- GitHub Actions run [43464917253](https://github.com/4mghonly/AggregateIT/actions/runs/43464917253): successful real-artifact downloads, 18 regression tests, seven nonempty dates for each language, actual Arabic three-page image rendering, **zero clipped text boxes**, and retained SQLite/HTML/PNG output.
- GitHub Actions run [43465150854](https://github.com/4mghonly/AggregateIT/actions/runs/43465150854): successful after preservation of historical model-generated English assessments with explicit unverified provenance.
- The original Arabic render had two clipped secondary summary cards. Dynamic summary length corrected both; subsequent real-data render reported zero clipping.
- Arabic page 3 now omits categories with no matching factual content; page 1 reclaims unused space when zero or one UAE event is present.
- These are **historical and layout acceptance passes**, not proof of V2 editorial parity or Telegram delivery.
