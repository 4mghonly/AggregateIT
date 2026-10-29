# V1 → V2 editorial continuity audit (2026-10-29)

Read directly from preserved V1 configuration on the V2 branch; no production modification.

- `config/keywords.json`: 40 intelligence clusters, 159 tag entries, 191 phrase entries; configuration version 3. **Preserved as a file; not yet fully consumed by V2's narrow live editorial source pipeline.**
- `config/watchlist.json`: ticker watchlist and keyword radar preserved. The V1 market snapshot bridge is integrated, but watchlist parity remains unverified.
- `config/sources.json`: 104 configured V1 source entries preserved. The current V2 live source catalog includes only BBC/DW English and Al Jazeera/BBC Arabic; it is not source parity.
- `arabic_newsletter/PRODUCT_RULES.md`: V1 production contract preserved; V2-specific UAE-only emphasis overrides any implied special allocation for Jordan/Palestine/Israel (see `ARABIC_EDITORIAL_PRIORITY_V2.md`).
- Existing production workflows: English 2 pages, Arabic 3 4K slides, original schedules and webhook routes preserved and checked by `v2_replacement_contract.py`.

## Release blockers
1. Feed the preserved keyword clusters and watchlists into V2's actual ranking/collection process with tests for coverage and false positives.
2. Expand V2's publisher-specific article-body compatibility beyond the four currently cataloged sources, retaining provenance and fail-closed behavior.
3. Validate English and Arabic actual model primary/fallback, evidence-grounded summaries and final rendering.
4. Prove seven distinct dates, durable history/restore, delivery rehearsal and production rollback.

Do not label preserved files as implemented parity.
