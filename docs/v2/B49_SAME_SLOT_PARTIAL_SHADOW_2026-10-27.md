# B49 — Same-slot V1/V2 acceptance, exact RSS evidence

Date: 27 October 2026, branch `rebuild/aggregateit-v2`.

A single immutable in-memory BBC World RSS capture and a single Al Jazeera Arabic RSS capture are shared between **the actual V1 and V2 parser comparison, source-only headline preview identity check, and the full held V2 source-to-article-to-native four-product laboratory**. Hashes are checked end-to-end, and only sanitized counts/digests enter the workflow artifact. V2 article pages are fetched independently after feed capture; this does **not** recreate the full V1 article evidence, model selection, translations, renderer and external Discord receipt from that same slot.

B49's full-system acceptance MUST remain **HOLD** until authentic V1 final editorial/model/graphic and delivery receipts exist, the B45 live translation gate is complete, and a like-for-like verified full-product quality/latency comparison can be made. No metrics are invented and no same-input quality score is manufactured from RSS parser parity.

No main writes, Discord sends, paid inference, source raw XML storage, database provisioning, deployment or canary. Single-run GitHub Actions path trigger; no recurring CI.

Hosted **partial same-source shadow PASS**; true end-to-end B7 **HOLD**.

## Hosted B49 exact-source findings and blockers

- [Run 40478257774](https://github.com/4mghonly/AggregateIT/actions/runs/40478257774) **SUCCESS**, **646/646 V2**, **153/153 EN**, **55/55 AR**: identical genuine BBC World and Al Jazeera Arabic RSS bytes used by pinned V1/V2 parser and headline preview; both parser and headline identities matched, and the same source snapshot was joined to V2 source-backed held four-product previews. **No V1 full original newsroom/model/render/delivery same-slot proof**; status `HOLD_NO_FULL_V1_EDITORIAL_BASELINE`, `can_release=false`.
- [Final combined run 40479327797](https://github.com/4mghonly/AggregateIT/actions/runs/40479327797) **SUCCESS**, **653/653 V2**, **153/153 EN**, **55/55 AR**, artifact `12722076127` metadata only (3 days): `parser_parity=true`, `headline_parity=true`, `four_v2_products=true`, `joined_b47_b48_b49=true`, **8 B48 operational alerts**, `v1_v2_full_editorial_compared=false`, `can_release=false`.

**B49 status: exact-RSS-byte partial parser/source comparison PASS; full B7 same-window product-quality/cost/delivery acceptance HOLD.** Absent evidence includes authentic V1 full editorial/LLM/translation/graphic and delivery receipts, independent model quality/latency/cost evidence, rights/factual checks, complete seven-day source history and real client/rollback. Do not infer a product-quality percentage or authorization from parser agreement. Production `main` stays unchanged at `ea52e14bc7fd2973058fd659f0ff2e8d617111dc` (including its previously authorized source-audit automation).

