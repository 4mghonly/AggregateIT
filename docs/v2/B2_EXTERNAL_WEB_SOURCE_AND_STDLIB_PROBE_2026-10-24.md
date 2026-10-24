# AggregateIT V2 — External read-only source observations and isolated fixes
Date: 24 October 2026 (UAE); code branch: `rebuild/aggregateit-v2`.

## Decision and isolation
The owner authorized use of an **alternative source-testing environment**, asked to apply repairs, and instructed that configured-model execution be **DEFERRED until needed**. OpenHands, protected `main`, current production delivery, cloud DB, model secrets and GitHub Actions are out of scope. No paid or live LLM call was made.

## What the independent public web environment actually proved
These are **public web client observations**, not a Python RSS adapter test or an endorsement of publisher claims.

| Publisher / entrypoint | Observation | Unverified |
|---|---|---|
| Reuters Middle East — https://www.reuters.com/world/middle-east/ | HTML newsroom page accessible | individual article body/fresh RSS/rights |
| Al Jazeera Arabic — https://www.aljazeera.net/ | Arabic news and regional categories accessible | article/collection adapter |
| Sky News Arabia — https://www.skynewsarabia.com/ | Arabic news site accessible | RSS and extraction |
| Sudan Tribune — https://sudantribune.com/ | website with dated regional headlines visible | RSS parsing and freshness SLA |
| Garowe Online — https://www.garoweonline.com/en | website with dated Somalia/Horn stories visible | article parser and RSS |
| Dawn — https://www.dawn.com/ | readable newsroom, contemporary issue/navigation | feed endpoint + extraction |
| Afghanistan International — https://www.afintl.com/en | site accessible, Arabic/Pashto/Persian navigation | individual language feed tests |
| TradingView News — https://www.tradingview.com/news/ | newsroom market updates and external syndicated provider identifiers visible | scanner API, timestamps/value series, independent corroboration |
| UN OCHA oPt — https://www.ochaopt.org/ | official dated periodic humanitarian reports visible | six-hour live feed suitability |
| Abu Dhabi Media Office index — https://www.mediaoffice.abudhabi/en/rss-news-feeds-abu-dhabi-media-office/ | first-party RSS directory accessible | source payload parsing |
| Abu Dhabi Media Office RSS — https://www.mediaoffice.abudhabi/en/security/rss/ | web viewer reports unsupported application/rss+xml | not evidence that publisher feed is broken |
| BBC World RSS — https://feeds.bbci.co.uk/news/world/rss.xml | web viewer reports unsupported text/xml | not evidence that feed is broken |
| Al Jazeera English RSS — https://www.aljazeera.com/xml/rss/all.xml | web viewer reports unsupported application/rss+xml | not evidence that feed is broken |
| Argaam — https://www.argaam.com/ | one latest web-client request produced an unexpected response, while a prior check viewed homepage | inconclusive, not a general source outage |

The public web check confirmed **access to several news sites**; the XML/RSS responses were **not parsed** by that web client. `config/v2/source_shortlist_triage_2026-10-24.csv` now contains **30/105** entries with scoped public-web metadata observations (previously 28). **No new publisher was admitted to production**, and 30 is NOT a count of validated working collector feeds.

## Fixes applied on isolated V2 branch
- `v2_source_lab.py`: stdlib-only RSS/Atom probe lab independent of `feedparser`, `trafilatura` and `ddgs` for this **diagnostic**, not their full production replacement. One bounded GET per unique candidate, 12 max sources, 200 KB response cap via shared probe, 8-second default timeout; no credentials, LLM, article-body persistence, database write, Discord send, or source promotion. Explicit `--live` opt-in; default CLI produces a dry-run manifest.
- `v2_feed_probe.py`: reject private and mixed-public/private resolved DNS answers before each direct request and redirect; `_SafeRedirect` blocks unsafe URLs. This is a **defense-in-depth preflight**, not a DNS-rebinding-proof HTTP transport: a managed network egress boundary is required before untrusted arbitrary URLs may be fetched.
- `v2_feed_probe.py` + `v2_feed_items.py`: reject XML `DOCTYPE` and `ENTITY` payloads before ElementTree parsing, preventing dangerous entity-expansion input from being treated as ordinary RSS.
- `v2_source_lab.py` reports `live_http_attempted` separately from `live_http_performed`. A DNS failure or blocked target must never be called a completed HTTP check; `network_error`, `http_403`, `not_a_feed`, and `usable_dated_feed` remain distinct.
- Focused tests: `tests/test_v2_source_lab.py` (8), `tests/test_v2_feed_egress_security.py` (7). Failing-first regressions confirmed before fixes. Combined complete local V2 `tests/` suite: **349/349 PASS** with no placeholder package modules. Native live collector compatibility **not** thereby certified.

## Environment and operational limitations
The isolated ChatGPT container still cannot resolve public internet hosts by DNS and does not have `feedparser`, `trafilatura` or `ddgs` installed. Those packages are **already declared** in the repository requirements and production workflows may install them. The new source lab allows independent RSS metadata checks without those packages **once executed in a genuinely network-capable environment**. A local explicit two-source live check attempted BBC and Al Jazeera and correctly returned `network_error`, `live_http_attempted=True`, `live_http_performed=False`: do not count them as live parsed sources.

Safe example, no traffic:
```sh
python -B -m v2_source_lab --source bbc=https://feeds.bbci.co.uk/news/world/rss.xml
```

Read-only one-shot external environment, *only when egress controls and connectivity are available*:
```sh
python -B -m v2_source_lab --live --source bbc=https://feeds.bbci.co.uk/news/world/rss.xml --source aj=https://www.aljazeera.com/xml/rss/all.xml
```

## Explicitly deferred
- Configured primary/fallback model access, secret handling, paid LLM calls, real multilingual translation and generated analysis: **DEFER until source-grounded intake and zero-post publication pipeline require them**. Do not request or copy keys.
- Cloud deployments, production scheduler, protected branches, external databases and any actual Discord publication remain outside this batch.
- Live actual RSS parser acceptance, full article ingestion, market scanner HTTP POST and 105-source regional independence verification remain pending genuine runtime evidence.

## Next acceptance criteria
To close source Batch A, run the read-only source lab with a verifiably completed HTTP response on a network-enabled but isolated environment, record parsed article dates/URLs, independently establish publisher families, and test the existing TradingView scanner without allowing data writes. Continue B once grounded source excerpts are available; only then decide on live model-credential access. No automatic cutover.
