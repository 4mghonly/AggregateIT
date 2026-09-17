# AggregateIT Project Definition

## 1. Mission

AggregateIT is a low-cost event-intelligence system for geopolitical, macroeconomic,
corporate, technology, security, and financial-market developments. It collects public
information, normalizes and scores it, clusters related reporting into evolving events,
checks source independence, adds structured analysis, and distributes concise intelligence
products through Discord and a two-page Gazette.

The product should answer five questions reliably:

1. What materially changed?
2. Is the report corroborated by independent source families?
3. What entities, markets, regions, and themes are affected?
4. How does public and specialist chatter compare with reported facts and price action?
5. What should be monitored next, without presenting automated trading advice?

## 2. Product Boundaries

### In scope

- Public RSS, Atom, approved APIs, public social feeds, specialist blogs, and selected
  public GitHub repositories.
- Event detection, deduplication, clustering, source-family provenance, confidence,
  lifecycle tracking, and claim storage.
- Market context across equities, indices, futures, commodities, FX, rates, volatility,
  sectors, and selected crypto assets.
- Separate fact, assessment, social-signal, and market-price layers.
- Hourly intelligence digests, daily briefings, weekly reviews, alerts, searchable history,
  source-health reporting, and the two-page Aggregate Gazette.
- Low-cost model routing through an OpenAI-compatible endpoint such as Qwen or OpenRouter.

### Out of scope for the current production layer

- Automated trading or order execution.
- Unqualified price predictions or personalized investment advice.
- Private, paywalled, authenticated, or terms-restricted collection without permission.
- Full-firehose social ingestion.
- Treating posts, rumors, or engagement volume as verified facts.
- Multi-user SaaS features until persistence, observability, and access control are mature.

## 3. Current Architecture

```text
Public sources
  -> source adapters (RSS, Reddit mirrors, RSSHub, StockTwits, blogs, GitHub)
  -> normalized items
  -> deterministic relevance and market scoring
  -> URL/title deduplication
  -> event clustering and source-family checks
  -> schema-validated LLM assessment
  -> SQLite event, claim, and timeline store
  -> Discord digests, briefings, alerts, history, and Gazette

TradingView scanner
  -> market and macro snapshots
  -> regime, breadth, movers, sectors, curve, and cross-asset context
  -> briefings and Gazette
```

| Component | Responsibility |
|---|---|
| `main.py` | Collection orchestration, scoring, clustering, analysis, event lifecycle, and digest delivery |
| `social.py` | Bounded social, community, and specialist-blog collection |
| `storage.py` | SQLite canonical event, claim, item-state, run, and timeline storage |
| `tv.py` / `market.py` | Market universe, live/previous-session snapshots, macro board, and regime signals |
| `slide.py` | Two-page Gazette collection, analysis, rendering, and Discord delivery |
| `briefing.py` | Daily and intraday executive intelligence products |
| `audit.py` | Source availability and health tracking |
| `tests.py` | Deterministic regression suite |
| `.github/workflows/` | Scheduled collection, market refresh, briefing, Gazette, audit, and history jobs |

## 4. Why Slide 2 Had Data Gaps

The gaps were caused by several independent faults rather than one missing feed.

### 4.1 Event fields were discarded before rendering

`briefing.load_events()` returned `importance` but omitted the canonical `event_id`,
`severity`, `status`, `confidence`, and `source_count` fields. `slide.py` expected those
canonical names, so it silently showed Low severity, blank confidence/status, and zero
verified claims even when the database contained the values.

**Fix:** preserve the briefing alias and expose all canonical fields to the Gazette.

### 4.2 The Gazette ran twice

`slide.yml` contained duplicated restore, render, upload, and delivery steps. A scheduled
run could therefore post the same two pages twice, consume extra model calls, and save a
later cache based on the same or stale inputs.

**Fix:** keep one render and one artifact upload.

### 4.3 Mutable state was being carried in immutable caches

Every workflow created a unique `data-<run>-<workflow>` cache and restored whichever
`data-` entry was newest. A slide or briefing run could restore an older database and then
publish a newer cache key, making later jobs regress to the older state. This explains why
gaps could appear intermittently even after a successful engine or market refresh.

**Immediate mitigation:** refresh market, macro, and social data inside the Gazette job and
fall back from a 24-hour event window to 72 hours with an explicit diagnostic.

**Required production fix:** move canonical state from Actions cache to Neon/Postgres or
another transactional store. Keep Actions cache only for disposable acceleration data.

### 4.4 Market and curve panels depended on previous snapshots

Risers/fallers require a prior comparable snapshot, and the trailing 2s10s chart requires
multiple saved sessions. A cache miss correctly produced no delta or history, but the page
did not clearly distinguish “baseline building” from adapter failure.

**Fix:** refresh the pulse and macro board before each Gazette and display input age/status.
The production persistence change must retain snapshot history independently of runners.

### 4.5 Social collection was oversized and unfairly capped

More than 300 X handles were fetched sequentially. On a degraded RSSHub day the time budget
could expire before later categories or other platforms were reached. The final global cap
was applied to `Reddit + X + RSSHub + StockTwits` in that order, so Reddit could consume the
entire allowance and make the other lanes appear empty.

**Fix:** rotate a bounded sample per category, reject stale/undated feed entries, apply
per-platform quotas, merge remaining capacity by recency, and publish per-platform coverage.

### 4.6 The social proxy secret was never passed to scheduled jobs

`social.py` supports `SOCIAL_PROXY_URL`, but `engine.yml` and `slide.yml` did not expose the
secret. Scheduled jobs therefore always attempted direct data-center access, where Reddit,
X/RSSHub, and StockTwits are frequently blocked.

**Fix:** pass the optional secret to the engine and Gazette refresh. Direct mode
remains the fallback when no proxy is configured.

### 4.8 Audit execution and model retries consumed the hourly budget

Importing `audit.py` executed a complete live audit, so every engine and test run made more
than 100 unrelated network requests before collection began. The workflow then ran the engine
twice, allowing up to 80 model calls per hour. A depleted model quota stopped the complete run.

**Fix:** make the audit CLI-only, run one bounded engine pass, cap it at ten model calls, trim
evidence payloads, and persist conservative Low/Medium fallback assessments when the model is
unavailable. Fallback assessments cannot trigger digests or alerts.

### 4.7 Invalid YouTube identifiers created permanent empty lanes

The three configured channel IDs were tested: two returned 404 and the third belonged to an
unrelated programming channel. They were removed rather than represented as active OSINT
sources. YouTube should be reintroduced only with verified channel IDs and feed-health tests.

## 5. Gazette Information Design

### Page 1: Executive intelligence

- Lead assessment linking geopolitical events and market transmission channels.
- Event ledger with real severity, status, confidence, source count, and claim count.
- World/geopolitical and markets/economy columns.
- Social narrative clearly labeled as chatter, not corroboration.
- Change since the previous edition, outlook, and key risk.

### Page 2: Markets, evidence, and diagnostics

- Mega-cap, sector, relative-volume, commodities, rates, FX, and yield-curve views.
- Cash indices and index futures shown separately.
- Market, macro, social, and event-window freshness on the page.
- Headlines and social/OSINT wires with source labels and timestamps.
- Explicit `missing`, `stale`, or `baseline building` states instead of blank areas.
- A future compact data-quality box: successful/attempted sources, stale-source count,
  latest engine run, LLM mode, and snapshot age.

## 6. Social and Specialist Chatter Scope

The social layer is a lead-generation and narrative-detection layer. It must never increase
factual corroboration unless an item links to an independently attributable primary source.

### Current collection lanes

- Reddit submissions and comments through the official OAuth API when configured, with public
  archives and optional RSS-Bridge as bounded fallbacks.
- X accounts through a configured RSSHub instance, with optional RSS-Bridge fallback.
- Bluesky through the public AT Protocol API and Mastodon through native RSS.
- Telegram through RSSHub, with optional RSS-Bridge fallback.
- StockTwits trending symbols and symbol streams.
- Verified specialist/institutional feeds: Oryx, Atlantic Council, CSIS, CISA, BIS,
  Financial Stability Board, CEPR/VoxEU, and RAND commentary.

### Expansion rules

Each new source must have:

- A documented public endpoint and collection method.
- A category, source family, reliability tier, region, language, and expected cadence.
- A health status based on live fetch results, not a static `Active` label.
- A timeout, item cap, retry policy, and backoff behavior.
- A statement of whether it is primary reporting, institutional publication, expert
  analysis, community discussion, or unverified chatter.

### Next source families to validate

- Official UAE and GCC institutions, exchanges, central banks, and energy bodies.
- Maritime, aviation, sanctions, trade-route, and supply-chain sources.
- Verified defense analysts and conflict-monitoring organizations.
- Corporate investor-relations and regulator filings for the watchlist.
- Regional Arabic-language public feeds with language-aware normalization.
- Additional public forums only where collection is permitted and stable.

## 7. Reliability and Data Model Amendments

### Priority 0 — required before calling the system production-ready

1. Move canonical state and snapshot history to Neon/Postgres.
2. Add idempotency keys for collection runs, event updates, and outbound messages.
3. Store every adapter attempt with source, started/finished time, status, item count,
   latency, HTTP/error class, and last successful item timestamp.
4. Add a `snapshot_id` to every Gazette and retain the exact event/market/social inputs.
5. Use one delivery record per product so retries cannot create duplicate Discord posts.
6. Fail scheduled jobs when delivery is required but not confirmed.

### Priority 1 — data quality

1. Replace static verification labels with measured source health.
2. Canonicalize URLs and syndicated source families before deduplication.
3. Add language detection and Arabic/English entity aliases.
4. Separate observed facts, source claims, model assessments, and social narratives.
5. Track claim-level support and contradiction, not only event-level confidence.
6. Add event merge/split review and cluster-drift metrics.
7. Record market-data session, exchange timezone, and comparison baseline for every move.

### Priority 2 — intelligence depth

1. Expand ontology to people, organizations, governments, locations, infrastructure,
   vessels, aircraft, commodities, securities, sanctions, cyber actors, and relationships.
2. Add entity resolution, aliases, co-mentions, and event-to-market linkage.
3. Measure social velocity, source diversity, novelty, and coordinated reposting.
4. Build watchlist-specific dossiers and timelines.
5. Add feedback labels for useful/noisy events and use them to calibrate deterministic
   thresholds before spending more LLM tokens.

## 8. Cost and Token Controls

- Fetch and filter deterministically before any model call.
- Cluster first; analyze one event rather than every article.
- Route low-impact summaries to the lowest-cost adequate model.
- Reserve larger models for high-severity, contradictory, or multi-domain events.
- Cache structured assessments by evidence hash.
- Send only normalized evidence and changed fields to the model.
- Enforce per-run call, token, time, and spend ceilings.
- Record input/output tokens, model, latency, fallback, and estimated cost per product.
- Current hourly ceiling: one engine pass, at most eight analyzed events and ten model calls;
  prompts contain at most four sources with 800 characters of evidence each.

## 9. Security and Compliance

- Collect only public or explicitly authorized data.
- Respect site terms, robots directives where applicable, API limits, and UAE law.
- Never bypass authentication, paywalls, CAPTCHAs, or technical access controls.
- Treat all collected content as untrusted input and preserve prompt-injection defenses.
- Keep secrets in GitHub Secrets or the deployment secret manager, never in code or logs.
- Strip tokens, credentials, personal data, and unsafe HTML from reports and artifacts.

## 10. Acceptance Criteria

A release is acceptable when:

- `python -m py_compile *.py` passes.
- `python tests.py` passes with no regression failures.
- JSON configuration files parse and contain no duplicate IDs or URLs.
- A dry run produces non-overlapping, readable Gazette pages.
- Missing inputs render explicit diagnostics instead of fabricated zeroes.
- Scheduled Gazette execution renders and delivers exactly once.
- Every Gazette shows the age of market, macro, social, and event inputs.
- Social output contains balanced lanes when those lanes return data.
- No social post is counted as independent factual corroboration by default.
- Source health and delivery failures are visible in the run report.

## 11. Delivery Plan

### Stage 1 — immediate stabilization

- Correct Gazette event-field mapping.
- Remove duplicate slide execution.
- Refresh page-two inputs in the Gazette job.
- Pass the optional social proxy configuration.
- Bound and balance social collection.
- Add verified specialist feeds and quarantine invalid sources.
- Add freshness and diagnostic labels to Page 2.

### Stage 2 — persistent production state

- Introduce Neon/Postgres schema and migrations.
- Dual-write SQLite/Postgres for validation, then make Postgres canonical.
- Persist immutable snapshots, run telemetry, and delivery idempotency.
- Remove cross-workflow mutable-state dependence on Actions cache.

### Stage 3 — evidence and analytics

- Claim graph, contradiction tracking, improved entity resolution, and cluster quality.
- Social velocity/baseline analysis and cross-platform narrative comparison.
- Source-health dashboard and per-product data-quality score.

### Stage 4 — user experience

- Searchable hosted dashboard, event timelines, saved filters, source drill-down,
  watchlist views, and controlled alert preferences.
- Keep advisory or trading features isolated from the core evidence engine.

## 12. Definition of Done for the Current Repair

- Repository behavior and documentation agree.
- Slide 2 receives canonical event fields and shows input freshness.
- Cash indices, index futures, commodities, FX, and rates are represented explicitly.
- Scheduled Gazette generation runs once and refreshes market/social inputs first.
- Social collection cannot be monopolized by a single platform.
- Invalid YouTube sources are removed and ten live specialist feeds are configured.
- The remaining cache-race limitation is documented as a production blocker rather than
  hidden behind a successful workflow status.
