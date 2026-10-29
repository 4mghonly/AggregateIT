# B108 — Arabic zero-story investigation and bounded recovery (2026-10-30)

## Evidence inspected
GitHub Actions artifact 12932335267, run 40951618959:
- Same-source V1/V2 RSS parser and headline identity: MATCH for both English and Arabic.
- V2 English story count 3, Arabic story count 0. The artifact did not include stage-specific article rejection counts.
- Archived V1 Arabic: 3 of 8 requested translations completed; 5 fallback HTTP 403 occurrences. This is a production V1 historical artifact, not a current credential diagnosis.
- Seven-date comparator: 0/14 full processing receipts; full editorial/model/render equivalence not established.

## Root-cause assessment
Arabic zero selection occurs downstream of RSS parsing. In `v2_b46_live_editorial_runner.py`, only headlines with exactly one supported country were eligible for article retrieval, before article text could establish geography. Other potential rejection stages include article-body evidence, topic relevance, publication age, editorial selection and limited publisher fallback. No individual stage can be identified as the sole cause from the previous sanitized artifact.

## Changes
- Added `arabic_zero_story_diagnosis` with sanitized collection counts, publisher attempts, article-admission and editorial holds.
- Added a bounded recovery path: at most three Arabic headlines without recognized country are admitted to article-body verification, within the existing six-attempt per-publisher cap. Headlines with multiple ambiguous countries are not newly admitted. The body/evidence and relevance gates remain unchanged; this is not blind story admission.
- Added isolated diagnostic regression and no-post CI coverage.

## Remaining blockers
- Verify real Arabic publisher response and post-change selected-story counts from a fresh shadow artifact.
- Investigate fallback 403 against current provider/account settings without exposing secrets; do not infer that historical failures still persist.
- Capture actual same-input full V1/V2 processing outputs, authenticated history across seven dates, real model fallback, native visual review and source-backed bilingual event identities.
- Maintain production/main isolation and release hold.
