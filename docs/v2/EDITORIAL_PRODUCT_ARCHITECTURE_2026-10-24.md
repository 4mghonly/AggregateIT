# AggregateIT V2 — Editorial Product Architecture: Dual Daily + Weekly
Date: 24 October 2026 (UAE) · Product-only scope · Replaces previous rigid assumptions where noted.

## Binding product distinction
**English Gazette = combined geopolitics, security, markets, macroeconomics and finance.**
**Arabic Intelligence Brief = geopolitical/security/military/diplomatic developments only**, UAE first. No finance, stocks, crypto, investor/market material unless an exceptional economic **policy decision** is itself a material geopolitical/security development; even then describe the geopolitics, not market trades.

The common substrate remains source -> normalized observation -> grounded claim/event -> edition planner -> analytical review -> deterministic renderer -> delivery ledger. Shared evidence is not shared editorial selection.

## TradingView: explicit preservation and expansion
The previous English V2 registry and 509-row catalogue had **zero TradingView entries**. This is a confirmed gap, not proof that a legacy tradingview collector still works.
- Re-added **TradingView News** https://www.tradingview.com/news/ to the V2 candidate master and B2 priority shortlist; market/economic headlines, news providers, symbol-specific reports. Editorial discovery and attribution; never count reprinted Reuters/Dow Jones reports on TradingView as independent of the original.
- Add **TradingView Economic Calendar** https://www.tradingview.com/economic-calendar/ for significant future/actual/consensus/prior events, as editorial reference.
- Add **TradingView News Feed widget** https://www.tradingview.com/widget-docs/widgets/news/news-feed/ and **Markets overview** https://www.tradingview.com/markets/ for the interactive browser companion. These are **display** capabilities, not a backend historical-price API.
- Official TradingView documentation explicitly states the standard widgets contain their own data, but does **not provide a general-purpose data extraction API**; do not implement the briefing's reproducible arithmetic by screen-scraping the widget. Use primary series and market data sources for market charts, calculations and dated comparisons.
- Complement sources: CME FedWatch, Cboe VIX, ECB Data Portal, Bank of England monetary policy, U.S. Treasury yields; combine with existing DFM, ADX, Saudi Exchange, FRED, EIA, OPEC, IMF and World Bank.
- Data provenance must include as-of timestamp, time zone, units, symbol/feed mapping, value vs estimate, stale/closed market, and return-calculation window. Null remains null; no fabricated percentages.
- Rank market signal usefulness by new event, source family, regional relevance and financial materiality; crypto and individual equity stories are optional unless materially consequential.

## Daily products: editorial briefs, not weekly analysis squeezed into slides
English:
1. Situation at a glance: top 3–5 verified developments; UAE/GCC flagged where material.
2. Developing stories (what, change, significance, sources, next checkpoint).
3. Cross-asset market pulse (index/energy/FX/yield observations and relevant TradingView news links; current values only if real and dated).
4. Geopolitical–financial transmission (measured relationship where warranted, clearly labelled analyst hypothesis otherwise).
5. Economic events ahead; source quality and coverage gaps.
6. Compact daily Naysayer (one testable counterinterpretation, evidence and a disconfirming indicator).

Arabic:
1. UAE-first security/geopolitical situation and changes since previous edition.
2. Regional chapters: GCC; Iran/Iraq/Turkey; Yemen/Red Sea; Levant/Palestine/Israel/Jordan; Sudan/Horn; Sahel/North Africa; Pakistan/Afghanistan.
3. Dated incidents/diplomatic moves, developing stories, contradiction and verification status.
4. Compact Arabic Naysayer, then forward indicators.
5. No trading, returns, commodity prices, indexes or financial market tables.

The current 2-page EN / 3-slide AR products remain compatibility targets **only**. Do not truncate the evidence or omit a priority country to preserve those page counts. New output: concise Discord image covers + linked mobile-responsive HTML edition or paginated annex.

## Weekly products: new and separate
English 6–10 editorial pages equivalent (content-dependent, never mandatory padding):
- Executive synthesis with material changes from last week.
- Chronological event evolution and corrections by region.
- Weekly *measured* asset performance (market holidays/exchanges/time-zone alignment), macro/central-bank surprises and energy/shipping trends.
- Research/report analysis (think tanks, government papers, central banks, open data) alongside breaking stories.
- 3–5 Naysayer thesis tests, contrasting strongest explanation, counterevidence and indicators.
- Scenarios, uncertainties, upcoming-week calendar and accountability against prior forecasts.

Arabic 5–8 editorial pages equivalent:
- Weekly strategic assessment, UAE/GCC first.
- Region-by-region geopolitical/security trend analysis, policy/diplomatic developments and conflict changes.
- Evidence-backed incident frequency changes if coverage/denominators justify counts.
- 3–5 Naysayer challenges and explicit unresolved issues.
- Scenarios, early-warning signals, revisions from previous assessment.
- Explicitly exclude financial metrics/trading/investor narrative.

Daily and weekly are distinct editorial plans and layout templates; a weekly report is **NOT** a concatenation of daily slides. Weekly uses week-long stored evidence to avoid re-collecting everything, with report literature added.

## Design system V3: professional, distinctive, non-generic
Standalone interactive proof: `aggregateit_editorial_prototype.html` delivered as downloadable local artifact. Four independent views: English Daily, English Weekly, Arabic Daily, Arabic Weekly. This prototype is **not yet committed as a runnable site** and is not a production template.
English: editorial financial broadsheet, warm ivory/ink/copper, restrained serif headlines, fine rules, source gutters, measured charts, explicit “unknown”.
Arabic: command-review editorial, dark midnight/slate/bronze, high contrast, right-to-left structure, readable Arabic font stack, country-region table. No loud colored country cards, fuzzy flags, AI-created illustrations or finance panels.
Responsive HTML first; deterministic PNG/PDF/Discord covers are generated from same **admitted** data model. Not from LLM-provided coordinates. Link to complete annex to preserve geographic scope.

## Approach to offline / online work
**Do not make the entire project offline.** Offline is a *test mode*, not the product architecture or an arbitrary development prohibition.
- **Offline deterministic:** schemas, dedup, evidence integrity, citation validation, analytics, naysayer proof contract, source scoring, time-zone and price math, template rendering, backup/recovery, fixtures, failure injection. Cheap/repeatable and safe.
- **Read-only live networking:** real publisher RSS/HTML/API adapters, TradingView news visibility, correct native-language checks, market-data freshness, feed independence and run-time latency. Keep bounded limits/concurrency for quality/reliability, not an artificial blanket ban.
- **Isolated integrated shadow:** collect same windows as V1 with independent output destination to local files/preview; route configured live LLM(s) only when budget/provider credentials are explicitly configured; count cost and quality.
- **Production:** preserve deployment isolation until genuine same-window B7 shows acceptable results; minimize disruptive cutovers, retain delivery deduplication. User may authorize changing production schedule and cost separately.
- No local GPU required, no model hosting requirement; use hosted APIs if operationally available, with configured controls rather than fixed model names. Cached analysis and deterministic summaries reduce inference cost.

## Acceptance checks
- Daily English contains sourced geopolitical and market segments; Arabic contains no market/trading section.
- TradingView editorial links present when fresh/relevant, or explicit provider unavailable reason; TradingView widgets shown only in browser companion. Primary macro and exchange data used for objective numbers.
- Weekly shows event change vs week baseline, actual source/report synthesis, credible geographic completeness, no daily concatenation.
- Critical daily once; weekly 3–5 evidenced challenges; no fabricated “opposition” where evidence cannot support it.
- User-facing full-width 390px preview, 1320px desktop and print/PDF preview; real RTL shaping, zero overlap/overflow, readable font, no clipping. Avoid replacing factual qualifiers with ellipses.
- Every rendered claim evidence-linked; source quality and freshness recorded; missing/unknown shown honestly.
- Comparative acceptance B7 on actual source windows, including cost, coverage, relevance, latency and mobile legibility.

## Batch execution
- **B2+:** TradingView and market supplements added as candidates, then priority authentic collector checks and scoring. Do not label candidates as active until observed.
- **B4+:** Separate daily/weekly editorial contracts and automatic critic candidate generation/validation, English market/geopolitics vs Arabic-only geopolitics; measure with held-out evidence.
- **B5+:** Replace bland previews with a responsive four-view design system, then wire into real V2 renderers with mobile screenshots; extend weekly report output.
- **B6+:** Add material-change tracking, weekly event memory and price-series analytics; keep free-tier storage caps and retention safeguards.
- **B7:** Shadow run across dates and compare outputs; require evidence before B8 cutover.

User's current instruction **supersedes rigid “offline-only” workflow preferences**: offline work is kept only where it actually adds verification value. Existing user-owned production/main constraints and charges are not silently reinterpreted as permission to disrupt production.
