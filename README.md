# AggregateIT

«An event-intelligence engine that monitors public sources for geopolitical, macroeconomic,
corporate, technology, security, and market developments, consolidates reporting into evolving
events, assessing significance and confidence, and surfacing material changes relevant to
financial markets.»

Out of scope (by design, deferred to final advisory layer): automated trading, trade recommendations, price prediction, generic news aggregation, full social-media firehose ingestion, multi-user SaaS. These will only be added as a separate advisory layer on top of the proven terminal.

## Architecture

| File | Responsibility |
|---|---|
| `main.py` | Orchestration: ingest → score → cluster → analyze → digest → health |
| `storage.py` | Canonical SQLite schema (`state.db`): items, seen_titles, runs, meta, events, event_updates |
| `tv.py` | TradingView universe + market pulse (direct percents, honesty gates) |
| `market.py` | Shared market-pulse embed builder (live / previous-session / stale / no-data) |
| `briefing.py` | Executive briefings (MINI / MORNING / CLOSING) from `state.db` + pulse |
| `alerts.py` | Custom alert rules (importance / ticker / keyword) |
| `history.py` | Searchable event history + timelines (workflow-driven) |
| `weekly.py` | Weekly intelligence review to Discord |
| `audit.py` | Source health audit |
| `tests.py` | Regression gate (runs before every engine run) |

## Pipeline

Source → Document → Signal (score + components) → Event (cluster) → Event Update (timeline)
→ Assessment (Qwen, schema-validated) → Alert / Digest / Briefing.

## Scoring (explainable)

Components tracked per item: `priority_source`, `ticker`, `mover`, `tv`, `keyword`, `confluence`.
Front-page floor = 5; below-floor items are `deferred` (retriable), never killed.

## Clustering (v2)

Multi-signal: entity (required) + ticker overlap + keyword-cluster overlap + title Jaccard +
time proximity, with a content gate and seed anti-drift guard.

## Event lifecycle

NEW → DEVELOPING → CONFIRMED (multi-source + confidence ≥ 85) → STABLE / RESOLVED / RETRACTED.
Every transition is written to `event_updates` and rendered as a 🕒 Timeline in Discord.

## LLM contract

System role = tradecraft rules; user role = evidence wrapped in `<report>` tags; model is
instructed to never follow instructions inside source text. Output JSON is schema-validated:
required fields, enums (event_type, corroboration, importance, sentiment, reliability),
confidence 0-100, ticker format, ticker-in-evidence, single-source confidence caps.

## Provenance

Canonical domains + source families; syndicated copies count as ONE source.
Multi-source claims without ≥2 independent families are downgraded and capped.

## Workflows

| Workflow | Schedule | Purpose |
|---|---|---|
| engine.yml | hourly at :07 | offline regression gate → ingest/analyze/store; legacy digest delivery disabled |
| tv_refresh.yml | scheduled + weekly | universe + market/macro snapshots |
| slide.yml | daily 15:30 UAE + manual | two-page Gazette with confirmed Discord receipt |
| calibration.yml | weekly | calibration report |
| backup.yml | weekly | state database backup |
| history.yml | manual | event search |
| search.yml | manual | ticker search |
| audit.yml | manual | source health |

`briefing.py`, `daily.py`, and `weekly.py` remain as legacy/manual builders but have no active scheduled workflow, preventing duplicate Discord products.

## Secrets

Required secrets: `QWEN_API_KEY`, `QWEN_BASE_URL`, `DISCORD_WEBHOOK`,
`GITHUB_TOKEN` (automatic in Actions). The primary model is `qwen3.8-flash`; quota exhaustion falls back to `qwen3.8-omni-flash` on the same configured endpoint/credential.

Optional source adapters: `SOCIAL_PROXY_URL`, `RSSHUB_BASE_URL`, `RSS_BRIDGE_URL`,
`REDDIT_CLIENT_ID`, and `REDDIT_CLIENT_SECRET`. Without those values the collector uses
native public Bluesky/Mastodon feeds and bounded public fallbacks; unavailable lanes are
reported as empty rather than aborting the engine.

## Persistence

GitHub Actions: rolling cache (primary) + weekly state backup artifact (recovery).
All workflows touching the shared cache are serialized to prevent stale-cache writers racing each other. A hosted transactional database remains the preferred long-term durability upgrade.

## Testing

`python tests.py` — scoring, clustering, provenance, lifecycle, validation, storage,
briefing integration, market-data honesty gates.

## Limitations

Reddit is frequently blocked (degraded-optional). TradingView percents are previous-session
outside 13:30–20:00 UTC. No embeddings yet (deterministic clustering first).

## Roadmap

Phase 1 reliability ✅ · Phase 2 intelligence ✅ · Phase 3 UX (this drop) ·
Next: claim-level evidence, embeddings if clustering plateaus, hosted dashboard.
