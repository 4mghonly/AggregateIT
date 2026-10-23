# AggregateIT V2 — Editorial Design and Source QA (24 October 2026)

## Actual deliverable
One self-contained (no required third-party assets) interactive HTML document with **four separate selectable editorial views**: EN daily, EN weekly, AR daily and AR weekly. Source is provided as a downloadable conversation artifact, NOT installed in production and NOT yet wired into the repo's native PNG renderers. No real news or price figures used; every view explicitly marked illustrative.

## Layout character
- English: warm ivory paper, dark ink, restrained copper, serif broadsheet masthead, cross-asset explainer chart, geopolitical story list, market intelligence, adjacent what-changed/watch-next, compact Naysayer. Weekly is a separate research-heavy page with geo/market/macro synthesis and weekly stress test.
- Arabic: midnight/navy + sand/gold, real RTL document flow and Arabic font fallback, UAE-first situational header, complete geographic watch table, developing political/security topics, compact daily critical desk. Weekly is a separate strategic analysis report with regional chapters, week-on-week indicators and deeper scenario testing. No finance or trading table appears in Arabic.
- Illustration-only SVG chart in English. No LLM chooses geometry; text slots and styles are deterministic. Missing metrics display em dash instead of invented zero.
- Long content goes into adaptive responsive report / annex rather than silently clipping a rigid Discord screenshot.

## Reproducible static browser QA (Python Playwright + system Chromium)
- Chromium viewport **1320 x 900**: four views switch successfully, full-page screenshots created.
- Chromium viewport **390 x 844**: same four views checked for horizontal overflow; **0 failures**.
- **0 JavaScript uncaught exceptions**, all four toggle combinations select exactly one active edition.
- Image sizes/preview remain **illustrative**, not production-ready visual acceptance.
- Local artifacts: `aggregateit_editorial_prototype.html`, 8 `{en,ar}_{daily,weekly}_{desktop,mobile}.png` snapshots, ZIP bundle. Not served over Internet; no deployment, external model, Discord or real source data in this QA.

## TradingView source verification update
- Official [market-news page](https://www.tradingview.com/news/) directly observed; has category/symbol-based reporting and syndicated provider names. News is a discovery channel; deduplicate by original publisher.
- Official [widgets page](https://www.tradingview.com/widget/) and [news-feed documentation](https://www.tradingview.com/widget-docs/widgets/news/news-feed/) confirm browser display features. No general backend historical market API is claimed.
- [CME FedWatch](https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html): verified page, reflects Fed Funds futures-implied probabilities; not a raw price series API.
- [Cboe VIX](https://www.cboe.com/tradable-products/vix): observed official page and redirect from old underscore path.
- [Bank of England monetary policy](https://www.bankofengland.co.uk/monetary-policy): corrected original mistaken nonexistent generic /monetary-policy-summary-and-minutes URL; stable landing page is readable.
- [US Treasury yield tables](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?field_tdr_date_value=2026&type=daily_treasury_yield_curve): corrected original generic path that returned 404; year and type explicitly scoped.
- [ECB Data Portal](https://data.ecb.europa.eu/): direct fetch received 503 in the web environment; **not declared operational**, do not treat this as a permanent provider outage.

## Still not verified
- Real article body/feed parsing; actual TradingView browser-widget integration; production Gazette market data; actual source-to-market numerical correctness; live-source comparison.
- Current daily/weekly prototype is a *design system direction*, not a full source-filled six-hour issue, V2 PNG renderer, signed quality evaluation or a live product.
- The existing last V2 231/231 suite was not rerun because this batch changed only source-catalogue and documents, not integrated V2 engines. Browser QA results above are local and independently reproducible.

## Immediate development after design signoff
1. Wire revised EN/AR daily and weekly structured plans to evidence ledger and Naysayer validator.
2. Implement TradingView news discovery and browser widget in complementary roles; get numeric prices from independently timestamped data source.
3. Replace synthetic story sections with evidence-linked real sample material in isolated previews.
4. Produce PNG/PDF/HTML pages and mobile proof; run B7 same-window comparisons before production route changes.
