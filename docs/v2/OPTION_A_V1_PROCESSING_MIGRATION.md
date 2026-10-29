# Option A — V1 Processing Migration (2026-10-29)

## Delivered in this increment
- `v2_v1_processing_bridge.py`: side-effect-free V1-inspired Arabic selection (UAE emphasis, relevance ranking, soft publisher diversity, no geographic quotas) and conservative title dedup decision.
- `v2_editorial.py`: actual Arabic edition planner now uses migrated selection logic.
- `tests/test_v2_v1_processing_bridge.py`: UAE-only emphasis, neutral other regions, publisher diversity, exact duplicate, fuzzy review, reversed actors.
- `.github/workflows/v2-b80-b83-live-acceptance.yml`: executes migration regression tests in isolated no-post CI.
- Prior increment: `v2_keyword_priority.py` integrates V1 keyword clusters into English V2 headline priority; V1 full scoring remains richer.

## Explicit boundaries
- The dedup decision helper is **not yet connected** to live V2 event admission. Fuzzy similarities are not auto-merged; publisher-independent evidence must remain separate for corroboration.
- V1 English `main.py` has weighted source/ticker/mover scoring, clustering, prior-event resolution, corroboration policy and model analysis. These have not all been migrated.
- V1 Arabic `arabic_live_v2.py` has source collection, security filtering, date checks, fuzzy dedup, impact ranking, publisher diversity, translation and LLM failover. Only selection primitives have been migrated in this increment.
- No hosted test pass is asserted until GitHub Actions completion is inspected.
- Production V1/main unchanged; no Discord post or cutover.

## Next bounded implementation batch
1. Port V1 English score components (keywords, ticker, movers, priority source) as a pure testable adapter, compare fixture results with V1.
2. Port Arabic deterministic filtering, impact scoring and dedup into the actual V2 source-admission pipeline, retaining provenance and source-date gates.
3. Add non-destructive cross-language candidate matching and event evolution receipts, not automatic event merging.
4. Test no-post end-to-end on identical V1/V2 fixtures and review live visual artifacts before release.
