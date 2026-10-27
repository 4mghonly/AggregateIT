# AggregateIT V2 — B44/B45 isolated staging and translation gate

Date: 27 October 2026, branch `rebuild/aggregateit-v2`.

**B44:** All four B43-qualified Somalia candidates are staged in `config/v2/source_registry.json` under `staged_sources`, separate from the original 222 source-of-record rows, and must remain disabled for collection, publishing and activation. Repeat actual production-validator and collector checks from the same single live feed capture on isolated GitHub runner, re-evaluate Somalia and 17 region floors against read-only current production SOURCE_AUDIT.json. A hypothetical source count does not close the production audit or verify publisher independence.

**B45:** Use up to two real collected foreign-language articles per candidate to record actual untranslated demand (original article bytes/headlines stay only in memory). A source-bound translation QA function invokes the existing production output normalizer, requires source-digest binding, numerical multiset integrity including repeated quantities and substantial Arabic script. Even passing structural translation stays **not publishable** without live model connectivity and semantic/source-equivalence review. No model/provider budget, credentials or paid calls are inferred from permission to begin the batch. B43 existing mocked failover tests still guard control-flow behavior.

**Safety:** No `main` / webhook / schedule / production registry / database changes. GitHub Actions workflow limited to one path-scoped push and no post. Artifacts retain counts/hashes only for 3 days.

Hosted acceptance: **B44 source staging and B45 structural QA PASS; real translation quality still HOLD**.

## Hosted B44–B45 results — 27 October 2026

[GitHub Actions #40468118638](https://github.com/4mghonly/AggregateIT/actions/runs/40468118638) **SUCCESS** on `368bd3fd057b7788a9fdad5f9d4e5c21ad9b98d8`: new focused tests **11/11**, entire V2 suite **589/589**, English legacy **153/153**, Arabic legacy **55/55**. Runner read current `main` audit from a separate checkout. Sanitized metadata artifact ID `12717417143` (3-day retention).

All four disabled Somalia candidates again passed the live technical checks and produced dated items within 72 hours: Shabelle **10**, Puntland Post **10**, Somali Dispatch **4**, Goobjoog English **10**. **Four provisional publisher-family labels** qualified technically; independent operator ownership and editorial accuracy were **not audited**. Eight source-linked foreign-language article excerpts (up to two per publisher) were prepared **in memory only** for eventual translation review. No provider endpoint was called and no translation was invented. Without model output, the B45 review correctly produced `HOLD_LIVE_TRANSLATION`.

Across the 17 target regions, the current production source-compatibility audit's only region below the minimum technical count of two was **Somalia (1)**. The additional four disabled V2 candidates yield a **hypothetical** compatible count of five (1 + 4), not a passed production audit, not confirmed independence, and not Arabic editorial eligibility. GCC's 3-source target is tracked separately in the B44 calculator. The historic coverage snapshot in the registry is unchanged.

### Exit assessment

| Workstream | Status | Remaining acceptance |
| --- | --- | --- |
| B44: four sources in unified V2 registry, disabled | **PASS** | Production activation/re-audit only after authorization and language/publisher QA |
| B44: 17-region technical source-floor report | **PASS as a read-only report** | Somalia 1/2 production floor still OPEN; independently operated source verification incomplete |
| B45: source-bound translation review contract | **PASS (structural tests only)** | Actual English→Arabic and Somali→Arabic source-faithful translations and provider/fallback connectivity |
| B45: eight live article samples routed for review | **PASS (pending inputs)** | No live translations; cannot grade semantic fidelity or market actual model yield |
| B7/B8 full-system/production canary | **HOLD** | B46–B51 per approved program |

No source was enabled, no production record altered, no model/Discord sends, no paid calls or database provisioning. The user's previous planning estimate **60% production readiness** and formal **6/8 verification gates** remain unchanged. Next work: run a strictly budgeted, authorized model translation evaluation and independent publisher family checks; continue integration in B46, then full-system shadow and canary.

