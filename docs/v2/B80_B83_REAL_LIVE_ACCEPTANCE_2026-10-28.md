# B80–B83 live publisher acceptance — 28 October 2026

## First actual hosted attempt: #40733805528

Live original-source capture completed for **BBC World English** and **Al Jazeera Arabic**:
- English: RSS accessible, 3 article attempts, 3 HTTP successes, 3 eligible article/body captures, 3 source-backed editorial stories.
- Arabic: RSS accessible, 4 article attempts, 4 HTTP successes, 1 eligible article/body capture and 3 rejected by `arabic_topic_without_explicit_trigger`.
- Total admitted real article captures: **4**. No raw publisher bytes persisted.
- Native renderer returned `HELD_VALID_NATIVE_PAGES`, **five 4K pages** (2 EN + 3 AR), but these were generated in a temporary directory and not independently visually reviewed.
- Four-product daily/weekly integration returned `HOLD_FOUR_PRODUCT_INTEGRATION` (error class must be diagnosed separately).
- B83 V1/V2 source-byte comparison crashed with `KeyError: 'arabic'`. Root: a captured RSS packet was added before parser/preview admission, leaving incomplete `parser` mapping when an exception occurred.

## Fix and retest

B49 now admits source packets only after successful parser and preview validation and returns a fail-closed `HOLD_SHARED_FEED_CONTRACT_MISMATCH` when source contracts differ. This prevents a missing parser row from crashing the comparison or being treated as success. Hosted rerun #40733983884 started.

## Acceptance interpretation

B80 genuine article-body capture: **observed** for 4 stories, not broad publisher quality acceptance.
B81 live English-to-Arabic translation: **not run**, no model credentials supplied; no semantic fidelity acceptance.
B82 native page generation: **5 genuine source-backed held pages rendered**, but visual/pixel review and known defect closure are not evidenced; four-product integration held.
B83 same-byte parser comparison: **not yet accepted**, initial run crashed and fix under hosted retest. Full V1 editorial/model/render/delivery parity remains missing.

Production release remains HOLD. V1, Discord, production secrets and database unchanged.

## Second hosted run #40733983884 — workflow SUCCESS, acceptance HOLD

B80 article-backed counts reproduced (3 English, 1 Arabic) and five held 4K pages generated. B83 now safely returned `HOLD_SOURCE_CAPTURE_FAILED` rather than crashing. Failure evidence identified `ModuleNotFoundError` in legacy Arabic parser. Investigation of `arabic_newsletter/collect.py` shows a direct `bs4.BeautifulSoup` import absent from the hosted install command. Added `beautifulsoup4` to isolated workflow dependencies; third live run #40734126557 initiated. No parser semantics weakened to bypass this requirement.

## Third hosted run #40734126557 — exact-source-byte parser/headline parity PASS

After adding `beautifulsoup4` (required by legacy Arabic collector), B83 completed without exception. Actual V1/V2 same-input rows: English parser parity true, headline identity parity true, V1-only 0, V2-only 0, 3 V2 editorial stories; Arabic parser parity true, headline identity parity true, V1-only 0, V2-only 0, 1 V2 editorial story. Both source hashes joined correctly. Full comparison status explicitly `HOLD_MISSING_V1_FULL_SYSTEM_EVIDENCE`, as no full legacy editorial/render/model/delivery replay was performed. B80 source captures and B82 five held pages reproduced. Four-product integration still `HOLD_FOUR_PRODUCT_INTEGRATION`; Arabic translation not run. This is a **partial real acceptance result**, not a production pass.

## Fourth hosted run #40734320042 — diagnostic

Real article counts, five native pages, and exact-input bilingual parser/headline parity all reproduced successfully. Four-product integration still held with `ModuleNotFoundError`. Inspection of `v2_b47_weekly_pdf_preview.py` identified imports `arabic_reshaper` and `bidi.algorithm` not in the isolated workflow installation. Added `arabic-reshaper` and `python-bidi` to that workflow only; fifth run #40734476003 started. No changes to production or translation semantics.

## Fifth hosted run #40734476003 — B80/B82/B83 technical integration PASS

Workflow **SUCCESS**. Source-backed original articles: 3 English, 1 Arabic. Five native 4K held pages generated. Full B47 four-product held package now successfully returned schema `aggregateit-v2-b47-four-product-held/1` after installing `arabic-reshaper` and `python-bidi` in isolated workflow. English weekly real daily snapshot days: 1; Arabic weekly: 1; neither represents seven-day coverage. B83 source-byte-joined English and Arabic parser parity true and headline identity parity true, with zero V1-only/V2-only items. No model translations, full V1 render parity or independent Discord receipt. This closes **technical live pipeline execution** for B80/B82 and parser-level B83, not editorial/visual/translation production acceptance. No main changes, production calls or posts.
