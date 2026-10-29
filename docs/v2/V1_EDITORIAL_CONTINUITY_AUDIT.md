# V1 → V2 editorial continuity audit (2026-10-29)

Read directly from preserved V1 configuration on the V2 branch; no production modification.

- `config/keywords.json`: 40 intelligence clusters, 159 tag entries, 191 phrase entries; configuration version 3. **Now connected to V2 English headline priority through `v2_keyword_priority.py` and `v2_b46_live_editorial.py`.** This is keyword relevance only, not full V1 engine parity.
- `config/watchlist.json`: ticker watchlist and keyword radar preserved. The V1 market snapshot bridge is integrated, but watchlist parity remains unverified.
- `config/sources.json`: 104 configured V1 source entries preserved. The current V2 live source catalog includes only BBC/DW English and Al Jazeera/BBC Arabic; it is not source parity.
- `arabic_newsletter/PRODUCT_RULES.md`: V1 production contract preserved; V2-specific UAE-only emphasis overrides any implied special allocation for Jordan/Palestine/Israel (see `ARABIC_EDITORIAL_PRIORITY_V2.md`).
- Existing production workflows: English 2 pages, Arabic 3 4K slides, original schedules and webhook routes preserved and checked by `v2_replacement_contract.py`.

## Release blockers
1. Keyword clusters now feed English V2 ranking; watchlist integration, full article-body relevance, and multilingual keyword coverage remain outstanding.
2. Expand V2's publisher-specific article-body compatibility beyond the four currently cataloged sources, retaining provenance and fail-closed behavior.
3. Validate English and Arabic actual model primary/fallback, evidence-grounded summaries and final rendering.
4. Prove seven distinct dates, durable history/restore, delivery rehearsal and production rollback.

Do not label preserved files as implemented parity.
