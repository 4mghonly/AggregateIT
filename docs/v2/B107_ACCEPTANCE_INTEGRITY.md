# B107 acceptance integrity closeout — 29 October 2026

## Delivered
- Added explicit B107 event review regression tests to the isolated acceptance workflow.
- Added parity evidence integrity tests for repeated event identities, blank identifiers and invalid SHA-256 values.
- Corrected the B101–B106 comparison engine to compare event identifier **multiplicities** (Counter) rather than sets; previously a lost duplicate could be reported as a match.
- All code remains no-post and cannot authorize production cutover.

## Outstanding real evidence (not replaced by passing CI)
- B101: identical actual V1/V2 article corpus and full newsroom outputs.
- B102: real clustering/duplicate decisions with source provenance.
- B103: bilingual semantic identity beyond geographic co-occurrence.
- B104: seven-date authenticated prior-edition history.
- B105: primary and fallback model failure/recovery output comparison.
- B106: 14 actual date/product shadow receipts, independent visual review, verified provenance.

## Completion policy
B107 regression and evidence-integrity implementation can close only after the latest hosted workflow is green. B101–B106 cannot be marked completed until the real-world evidence above exists and is reviewed. Passing synthetic fixture tests never counts as seven-day production parity. No release, production posting or main modification is authorized.
