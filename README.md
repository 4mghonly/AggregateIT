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
→ Assessment (runtime-configured LLM, schema-validated) → Alert / Digest / Briefing.

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
| calibration.yml | weekly | current event/market association diagnostic (not predictive backtesting) |
| backup.yml | weekly | state database backup |
| history.yml | manual | event search |
| search.yml | manual | ticker search |
| audit.yml | manual | source health |

`briefing.py`, `daily.py`, and `weekly.py` remain as legacy/manual builders but have no active scheduled workflow, preventing duplicate Discord products.

## LLM configuration

LLM provider and model selection are runtime-configured; no provider or model is fixed in code.
GitHub Actions reads all six essential LLM routing values from repository Secrets.

Primary route Secrets:
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`

Fallback route Secrets:
- `LLM_FALLBACK_API_KEY`
- `LLM_FALLBACK_BASE_URL`
- `LLM_FALLBACK_MODEL`

Optional provider-compatibility variables: `LLM_AUTH_HEADER`, `LLM_AUTH_SCHEME`, `LLM_CHAT_PATH`,
`LLM_REQUEST_OPTIONS_JSON`, `LLM_EXTRA_HEADERS_JSON`, plus their `LLM_FALLBACK_*` equivalents.

The Arabic briefing inherits these generic Secrets by default, or can use its own `ARABIC_LLM_*` overrides.
`ARABIC_LLM_FALLBACK_MODELS` is also supplied as a Variable; no model list is embedded in source code.

Other integration credentials remain in GitHub Settings → Secrets and variables → Actions.

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
