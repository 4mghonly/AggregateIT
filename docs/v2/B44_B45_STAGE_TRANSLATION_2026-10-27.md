# AggregateIT V2 — B44/B45 isolated staging and translation gate

Date: 27 October 2026, branch `rebuild/aggregateit-v2`.

**B44:** All four B43-qualified Somalia candidates are staged in `config/v2/source_registry.json` under `staged_sources`, separate from the original 222 source-of-record rows, and must remain disabled for collection, publishing and activation. Repeat actual production-validator and collector checks from the same single live feed capture on isolated GitHub runner, re-evaluate Somalia and 17 region floors against read-only current production SOURCE_AUDIT.json. A hypothetical source count does not close the production audit or verify publisher independence.

**B45:** Use up to two real collected foreign-language articles per candidate to record actual untranslated demand (original article bytes/headlines stay only in memory). A source-bound translation QA function invokes the existing production output normalizer, requires source-digest binding, numerical multiset integrity including repeated quantities and substantial Arabic script. Even passing structural translation stays **not publishable** without live model connectivity and semantic/source-equivalence review. No model/provider budget, credentials or paid calls are inferred from permission to begin the batch. B43 existing mocked failover tests still guard control-flow behavior.

**Safety:** No `main` / webhook / schedule / production registry / database changes. GitHub Actions workflow limited to one path-scoped push and no post. Artifacts retain counts/hashes only for 3 days.

Initial hosted acceptance: **PENDING**.
