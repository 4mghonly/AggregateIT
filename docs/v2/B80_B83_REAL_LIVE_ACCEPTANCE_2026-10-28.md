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
