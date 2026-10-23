# B0 Quality Baseline — 23 October 2026
Snapshot is based on GitHub files and action logs; it is not a complete live-service or external-source uptime certification.

## Reproducibility anchors
- Repository main snapshot: 6deea127bbbd645cc5a4969a5397e745839a95ce, 22 Oct 2026 06:07 UTC.
- Arabic compatibility audit: arabic_newsletter/SOURCE_AUDIT.json at this commit; checked 22 Oct 2026 06:07 UTC.
- English sources: config/sources.json (104 records); Arabic candidate sources: arabic_newsletter/SOURCE_AUDIT.json (118 records); active Arabic production registry: arabic_newsletter/sources.json (61 enabled/active).
- Arabic production: https://github.com/4mghonly/AggregateIT/actions/runs/39887640847
- Gazette production: https://github.com/4mghonly/AggregateIT/actions/runs/39771702661
- Arabic source audit failure: https://github.com/4mghonly/AggregateIT/actions/runs/39731964658
- Engine check: https://github.com/4mghonly/AggregateIT/actions/runs/39893560396

## Directly observed production examples
| Layer | Observation | Interpretation |
| --- | --- | --- |
| Arabic source audit | 118 configured; 58 marked compatible (49.2%); Somalia 1/3; every other listed target region >=2 compatible | The all-region floor fails. “Compatible” means the existing adapter audit, NOT freshness or factual independence |
| Arabic registry | 61 enabled/active (different from 58 latest compatible) | Registry can be stale when audit validation fails; workflow writes audit file before source floor, then skips rebuild |
| English registry | 104 source rows | Inventory count only; not 104 healthy feeds |
| Arabic run 23 Oct 06:05–06:12 UAE | 110 collected, 17 selected, UAE selected=1, translated=3; primary translation: empty/truncated/invalid schema; fallback repeated HTTP 403; quality warning about translation and UAE coverage | Three-page deck delivered with degraded content; run conclusion success does not imply edition quality |
| Arabic Discord delivery | One message with 3 PNGs, receipt logged | Transport delivery confirmed for that run |
| Gazette 22 Oct 15:35–15:39 UAE | Primary and fallback analysis exhausted/rejected by schema; deterministic fallback, workflow success; two-page Discord receipt logged | Delivery confirmed; analytical layer degraded |
| News Intelligence Engine 23 Oct 07:10 UAE | Workflow success | Execution success only; no complete downstream quality proof |
| Arabic audit 22 Oct | Floor assert failed: Somalia=1; production source rebuild skipped | Required source registry update blocked |

## Geographic coverage in most recent Arabic audit
| Region | Compatible |
| --- | ---: |
| Global (cross-cutting) | 10 |
| GCC | 10 |
| Oman | 2 |
| Iran | 3 |
| Turkey | 3 |
| Iraq | 2 |
| Yemen | 2 |
| Sudan | 2 |
| Sahel | 6 |
| North Africa | 2 |
| Egypt | 2 |
| Pakistan | 2 |
| Afghanistan | 2 |
| Somalia | **1** |
| Horn of Africa | 2 |
| Palestine/Israel | 2 |
| Levant | 2 |
| Jordan | 3 |

These numbers are audit-adapter responses. There is no proof here of fresh political/security events in every region, independent ownership or publisher licensing.

## Confirmed mechanisms and exposure
1. The Arabic translation selection path requests individual model translations with a finite stage budget; failed translations can remove foreign-language events from the final deck. The latest fallback returned HTTP 403 repeatedly; no observed effective permanent-open-circuit for that route.
2. Arabic source compatibility audit checks nonempty extraction more readily than dated, relevant, fresh evidence; source coverage can appear healthier than event coverage.
3. Arabic live event fields do not enforce article-level exact excerpt provenance called for in arabic_newsletter/PRODUCT_RULES.md. Publisher source ID is not an immutable article ID.
4. Arabic brief generation does not persist and pass previous comparable events to the change-delta path consistently. “Changes since last briefing” is not proven operational.
5. The Arabic renderer uses fixed 3840x2160 zones with some small source/secondary labels; an image which looks acceptable enlarged may become unreadable in the Discord preview. This is a design hypothesis requiring fresh scaled-image QA, not a measured pixel-legibility claim.
6. The English source-audit workflow installs aiohttp and feedparser, whereas audit imports social requiring requests; prior run failed with ModuleNotFoundError. Dependency parity is a B1 target.
7. Current state uses rolling GitHub Actions cache plus weekly artifact backup. Cache restore is not a transactional database.
8. The scheduler implementation is present in ops/, but ops/README.md explicitly states it is NOT deployed/active. Do not assume independent scheduler is live. Repeated workflow_dispatch runs are visible, but their trigger mechanism is not established by this audit.
9. Existing cadence watchdog looks at workflow execution recency; it does not establish claim accuracy, translation yield, page usability or Discord receipt health.

## Supplemental one-shot English feed probe (not production evidence)
An earlier isolated probe of all 104 registered URLs in a non-production network returned HTTP 200 for 71; 66 yielded nonempty parsed feeds; 57 had dates parsed as within 72 hours. It was a simplified urllib/XML/date parser, subject to concurrency and network bias. HTTP 402/403/404 and transient network errors occurred. These figures are preliminary diagnosis and MUST NOT be treated as per-source permanent dead/healthy classifications. Re-run under B2 with the production adapter and separate response, freshness and editorial usability metrics.

## Measurement contract for V2
For each run/edition capture: slot_id, code revision, source registry revision, sample window, source attempted/fetched/parsed/fresh counts, geographies, selected events, article and publisher-family corroboration, translation attempts/success and discarded selections, validation rejections, LLM route/time/cost, render dimensions/text overflow and visual QA, expected Discord channel, receipt ID, published/degraded/withheld status, and failure code. Separate operational availability from editorial truthfulness.

## Evidence gaps / limitations
- No authenticated credentials, live feed access, fresh all-source replay, or production environment mutation performed in B0.
- No statistically reliable publication SLO computed from a sufficiently long period of receipt events.
- Latest workflow logs demonstrate selected failures, not all failures or median/p95 timing distributions.
- No independent visual screenshot audit or source-ownership/legal-rights classification in this batch.
- Existing test results are not fresh branch-local test executions.

## B1 triage order
1. Route error classification, failover and model-output schema repair (primary invalid JSON vs fallback HTTP 403).
2. Audit dependency parity; differentiate audit status from registry update status.
3. Translation stage budget, bounded selection attrition and degraded-mode attribution.
4. Source-family and edition-level health report as non-publishing JSON.
