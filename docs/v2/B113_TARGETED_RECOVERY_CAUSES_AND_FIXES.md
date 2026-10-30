# B113 — Targeted Arabic recovery: root causes, repairs and next acceptance

## Verified evidence
- B112 accepted CI run `40991845436`, artifact `12949272711`: 3 English stories, 0 Arabic in both separate live/shadow captures. The Arabic primary publisher served valid RSS and six article HTTP responses. Article-evidence rejection categories: `arabic_topic_without_explicit_trigger` (3), `article_body_container_missing` (1), `no_grounded_region` (1). One primary article passed body evidence but failed editor's `arabic_not_security_relevant` gate.
- B108 run `40953418909`: a different live capture did recover one Arabic story through BBC Arabic; therefore the Arabic path is not globally disabled.
- B112 history-conflict artifact groups restored receipts across three successful runs for 2026-10-28 and 2026-10-29. All 2026-10-28 receipts agree. For 2026-10-29, all show three English and one Arabic story, but three different evidence hashes. These are distinct snapshots, not evidence that any count is mathematically wrong. No seven-day full V1/V2 comparison exists.
- B112 artifact `b112_history_conflicts.json` and `b95_b97_history.json` contained extra literal slash-n text after their JSON objects because the YAML embedded Python used `+'\\n'` instead of an actual newline.

## Confirmed implementation defects
1. The B108 collector deferred countryless Arabic headlines, but `classify_geography()` refused all headlines without country text even when the article lead named a country.
2. `source_recovery` counted article-body eligibility as publisher success before the Arabic editorial relevance gate. One rejected primary article blocked automatic BBC Arabic fallback.
3. The history archive is indexed as **day**, even though multiple independent capture slots exist in one day. Choosing one digest would compromise provenance and still would not establish a full V1 baseline.

## B113 targeted repairs
- Permit an Arabic countryless headline only when the first two article paragraphs contain **one unique explicit supported country**, corroborated by article text; never guess ambiguous geography or remove the topic/security gates.
- Evaluate the *same* Arabic editorial relevance predicate before marking source recovery success, allowing the approved BBC Arabic fallback when the primary's sole eligible item fails relevance.
- Repair the CI embedded JSON serializer to emit valid JSON followed by an actual newline.
- Add offline regressions for single-country recovery, ambiguous-country hold, body corroboration, and editorial-aware fallback. Do not relax unrelated source/rights checks or change production.

## Proposed next fixes (not yet implemented)
1. **Arabic topic accuracy:** Evaluate the exact rejected articles against bounded, evidence-backed Arabic security/diplomacy cue variants, including prefixed/inflected terms and verified article-lead context. Add positive/negative regression examples *before* extending the lexicon. Do not indiscriminately weaken `arabic_filter`.
2. **One-pass edition capture:** Pass the **same in-memory RSS and article evidence snapshot** into live and shadow validation; retain only hashes/counts in CI artifacts. Compare V1 and V2 full processing on that same snapshot rather than treating two independently fetched runs as equivalent.
3. **Historical provenance:** Store immutable receipts keyed by `(capture_date, slot_id, run_id, product, input_digest)`; surface all same-day versions separately, reject incompatible claims for any supposedly identical slot, and require seven distinct dates × two products with genuine V1 execution evidence.
4. **Translation:** Run one bounded, no-post primary/fallback connectivity test only after provider credentials are explicitly available in the isolated job; classify 401/403 as access issues, not transient rate limits. No unnecessary retries or paid model calls.

## Release decision
**HOLD.** A passing unit-test/CI workflow is not real bilingual editorial equivalence. Acceptance requires robust English and Arabic story selection, authenticated same-source V1/V2 comparisons, seven-day evidence, model fallback proof, and independent native visual review. Main, production and Discord remain untouched.
