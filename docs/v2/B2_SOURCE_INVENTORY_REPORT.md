# AggregateIT V2 — B2 Source Inventory, Phase A
Date: 23 October 2026 (UAE)  
State: **PARTIAL — offline registry and tests complete; live-source, rights and publisher-independence gates open**  
Branch: `rebuild/aggregateit-v2`; **main unchanged**

## Evidence baseline and counts
The snapshot is mechanically reconciled against `config/sources.json`, `arabic_newsletter/sources.json`, and `arabic_newsletter/SOURCE_AUDIT.json` (last checked **2026-10-22 06:07 UTC**). These are historical observations, not a new source probe.

| Measure | Historical evidence |
| --- | ---: |
| English configured entries | 104 |
| Arabic configured entries | 118 |
| Total stable V2 identities | 222 |
| English ↔ Arabic identical feed URLs | 8 pairs; count once as upstream evidence, not two independent publishers |
| Arabic source audit adapter-compatible | 58/118 |
| Arabic adapter-compatible **with at least one dated item within the old 72h window** | 48/118 |
| Arabic declared enabled | 61; **3 now failed the later audit** |
| English GitHub repository discovery entries | 5 — must not be fetched as RSS |
| English unverified status | 13; one explicitly disabled source preserved |
| Arabic regions with published coverage rows | 18 |
| Ownership-independence confirmations | **0 — not assessed** |
| Source content/redistribution rights reviewed | **0 — not assessed** |

The three declared-enabled but later audit-incompatible Arabic sources are **Goobjoog (s058, Somalia, HTTP 404)**, **Shabait (s062, Horn, HTTP 202)** and **Khaama Press (s091, Afghanistan, HTTP 202)**. This is a V2 diagnostic, **not** an instruction to disable production sources.

## Measured regional gaps from the last audit

| Scope | Adapter-compatible | Dated recent | Distinct website-host candidates among dated recent | Target family count | Meaning |
| --- | ---: | ---: | ---: | ---: | --- |
| Somalia | 1 | 1 | 1 | 2 | Confirmed historical shortage |
| Yemen | 2 | 1 | 1 | 2 | HTML-only second source has no dated freshness evidence |
| Egypt | 2 | 1 | 1 | 2 | Second source had zero recent dated entries |
| Afghanistan | 2 | 1 | 1 | 2 | Second source had zero recent dated entries |
| Jordan | 3 | 1 | 1 | 2 | Two HTML adapters cannot demonstrate dated freshness |
| GCC region | 10 | 6 | 5 | 3 | Host-candidate count meets provisional number, but not certified independence |
| UAE-country subset | 7 | 3 | 2 | 3 | Three dated feeds resolve to only two publisher-site host candidates |

The other 13 Arabic region buckets have at least two different website-host candidates among historically dated sources. **Host distinctions are not legal/operational publisher-independence evidence**, and old audit observations are not proof of today's freshness. All 18 regions remain unverified against the strict independent-publisher acceptance gate.

## Immediate triage queue (no automated retry loop)
1. **Somalia:** retain Radio Ergo as a historical positive. Check SONNA (zero-entries audit), Goobjoog (latest 404 despite old registry "active"), and Hiiraan Online (no RSS). Find one new first-party alternative only if these cannot be validated without scraping or violating publisher terms.
2. **UAE:** validate dated current RSS from The National and Abu Dhabi Media Office, then one *independent* UAE publisher (Gulf News, Khaleej Times, or Emirates 24|7 currently HTML-only). Distinguish three Abu Dhabi Media Office feeds as one publisher.
3. **Yemen/Jordan:** verify legally permitted date extraction for South24, Petra and Al Ghad HTML adapters. An HTTP 200 and headline text alone cannot count toward the fresh-source floor.
4. **Egypt/Afghanistan:** examine dated entries and timestamps on Masrawy/Bakhtar; do not reactivate other candidates solely because URLs respond.
5. **English:** audit per-source adapter compatibility, freshness, language, geographic relevance and publisher family. The current English list has no per-feed language/region fields; V2 does not infer them.

No production registry was changed and no automatic source promotion, article harvesting, Discord posting, database creation, or paid API call was made.

## Implementation
- `config/v2/source_registry.json`: offline joint snapshot; stable `en-NNN`/`ar-sNNN` identities, legacy states, language/region where actually declared, adapter hints, historic source audits, duplicate upstream URLs and conservative geographic diagnostics.
- `v2_sources.py`: stdlib-only validator and read-only CLI. Catches source-of-record drift, forged audit freshness, invalid source states, duplicate IDs, altered duplicate links and unsupported geographic coverage claims.
- `tests/test_b2_source_registry.py`: 14 deterministic, network-free regression cases.
- Historical quality metrics can feed the later D1 dashboard **only after they are clearly dated and labelled as imported historical evidence**; they are never counted as current-live observations.

## Verification and exit
14/14 tests passed using the actual three original JSON inputs and generated snapshot in an isolated in-memory Python harness (Python 3.12, standard library), including mutation tests. The GitHub-branch files themselves have not yet been exercised in an installed checkout: remote exact-byte verification follows publication.

Remaining B2 acceptance: independent-owner corroboration, per-source rights clearance, live adapter and dated freshness probes with bounded timeouts, quarantine/replacement test, and regional floors. No claim of B2 completion until these are evidenced. B1 remains partial pending full installed-dependency/e2e rehearsal.
