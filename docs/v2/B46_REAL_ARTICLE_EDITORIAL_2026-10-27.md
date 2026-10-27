# AggregateIT V2 — B46 phase 1 real publisher article-to-editorial chain

Date: 27 October 2026
Working branch: rebuild/aggregateit-v2

## Implementation

B46 stage 1 connects genuine **publisher HTML article body** to the existing V2 B3 immutable text/revision/excerpt/claim/event ledger, the B4 independent English+Arabic policy planners, Naysayer abstention and the no-post daily compiler. It exercises the established \`v2_article_body_gate\` and existing B3/B4 modules, rather than creating a second untracked editorial engine.

Two pinned origins only: BBC World English and Al Jazeera Arabic. RSS is fetched once per feed; at most six article URL fetch attempts per language, cap 3 collected pages per language; one HTTPS request per eligible article and no fallback to mismatched host. Captured publisher text/HTML is only held in memory; runner writes source/article hash, aggregate counts, withheld reasons and coverage gaps. Every admitted publisher quotation must be a literal span of an actual article-body container from the matched source, never a naked RSS headline or unverified semantic rewrite. The event key is derived from article identity, *not* from headline similarity or an inferred cross-language entity match.

Source attribution means **the publisher printed the quotation**, not that the reported event has been independently verified. Topic and geography are bounded by the existing deterministic headline+article-body country classifier; any ambiguity withholds admission. English market data remains explicitly unavailable; Arabic financial section is forbidden. Both products always retain Naysayer insufficient-evidence notices until sourced independent reports exist.

## Carried-forward B45 open gate

Eight previous English/Somali source-linked samples existed in memory in B44/B45. No actual model translation or provider fallback connectivity was run. This remains a separately measured B45 gate, including model budget, multilingual translation of names/numbers/locations, Arabic semantics and deduplication. B46 does not silently promote untranslated Somali/English source claims into the Arabic edition.

## Verification

TDD cases cover successful bilingual real-article-container integration, source host swap rejection, excerpt integrity, repeated article IDs, stale admissions, exact product-topic separation, conservative delta when previous baseline is missing and no persisted publisher body. Focused test run and full hosted regression **PENDING**.

## Exit and bounds

This stage is a real article-to-graph-to-held-edition integration, but **not** full cross-language resolution, model analysis, Naysayer generation, verified TradingView prices, authenticated commercial rights, complete regional coverage, render/Discord receipt or genuine V1/V2 full shadow. All outputs remain non-sendable and production unmodified. AggregateIT estimated production readiness and formal B7/B8 evidence gates are unchanged.
