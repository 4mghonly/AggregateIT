# AggregateIT V2 Synthetic Golden Cases
All cases in golden_cases.json are **synthetic**. They contain invented test actors and example.com URLs and MUST NEVER be treated as actual news, published, used for factual claims or sent to production Discord.

Contract: aggregateit-golden-cases/1, non-executable specification for B1-B5. Tests must be implemented independently; checking that JSON parses does not prove editorial behavior.

Expected decisions:
- ACCEPT: grounded normalized event may appear after all other gates.
- REJECT: editorial or evidence mismatch prevents publication.
- DEGRADE: incomplete inputs/coverage must be explicitly labelled and metrics preserved.
- WITHHOLD: delivery should not proceed until required evidence or quality returns.
- UPDATE: stable event identity and real delta rather than duplicate slot.

When writing tests, assert observable result and traceable reason; never implement a shallow test that merely echoes fixture.expect. Include negative controls and cross-language/RTL layout snapshots. Branch-only, no production posts.
