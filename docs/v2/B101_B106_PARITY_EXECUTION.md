# B101-B106 — Processing parity execution and evidence gates (29 Oct 2026)

## Implemented
- B101: `v2_processing_parity_benchmark.py` gives five controlled Arabic examples and transparent English scoring output; `v2_b101_b106_parity_gates.py` compares supplied same-input V1/V2 results by date, product and dimension.
- B102: event clustering is non-destructive; reversal and unrelated event cases have regression coverage. Automatic source-independent event consolidation **not implemented**.
- B103: cross-language candidates are review-only, with source event/excerpt IDs; true bilingual semantic identity and automatic consolidation **not implemented**.
- B104: signed operator journal can establish bounded prior event versions. Seven-day event evolution on actual authenticated editions **not demonstrated**.
- B105: source/publisher fallback is tested separately. LLM translation/model failover parity **not demonstrated**; the new gate requires explicit exercised model fallback evidence.
- B106: seven-date English and Arabic evidence must contain 14 unique date/product records. Missing dates, missing processing evidence or mismatches hold. Visual review and provenance evidence are required. No live seven-date parity set was supplied.

## Current evidence status
Controlled regression suite and one-slot shadow components exist. Passing unit tests does not prove V1 production-equivalent selection, bilingual event identity, real model failover or seven consecutive calendar dates. The gate refuses release even with complete matched evidence, pending an owner decision.

## How to continue
1. Obtain source-byte-identical V1/V2 newsroom outputs for each English/Arabic date, with trustworthy input digests and provenance; do not manufacture or repeat one date as seven.
2. Convert outputs to dimension-specific event/story identity lists for Arabic filtering, English scoring, event clustering, multilingual consolidation, historical evolution, translation/fallback and visual/delivery.
3. Run `assess(rows, as_of=...)` with 14 date/product rows, investigate every mismatch and preserve evidence links.
4. Run actual primary/fallback LLM failures without live publication; record provider and translation outputs, visual review, authenticated prior journals and independent publisher/source checks.
5. Review full workflow artifacts, then separately decide whether to authorize release.

## Guardrails
Branch `rebuild/aggregateit-v2` only. No production or main modifications, no paid model calls, no Discord posts, no cutover. The parity gate always returns `can_release: false`.
