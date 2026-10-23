# AggregateIT V2 — Comprehensive source landscape, 24 October 2026

## Scope and ownership
**AggregateIT only.** Owner requested a comprehensive source catalogue for **personal-use English finance/geopolitical Gazette** and **Arabic security/geopolitics briefing**, including a compact daily and expanded weekly critical-analysis section. Publisher licensing/legal analysis is out of scope for this deliverable, per owner instruction. This file is a **source inventory and research prioritization**, not a claim that automatic access, live health, language attribution, or operational suitability has been established.

## Files
- [MASTER CSV](../../config/v2/source_master_candidates_2026-10-24.csv): **518 rows** = **222 legacy V2 registry entries + 296 curated source/endpoint candidates**. Rows are *endpoints or registry records*, **not 518 unique publishers**. Existing and new entries intentionally coexist so the provenance of older settings is not lost. Some curated entries are alternative pages belonging to the same publisher; publisher-family reconciliation is pending.
- [Prioritized shortlist CSV](../../config/v2/source_shortlist_2026-10-24.csv): **105 nominated entrypoints**, spanning international, regional, national and specialist outlets plus official and data sources. This is **candidate selection**, not admission to automatic harvesting.
- [Existing registry](../../config/v2/source_registry.json): original 222 source records kept **unchanged**.

## How to read the master file
`id` identifies the row; `record_type` distinguishes baseline from curated; `stream` is a *proposed* editorial path, not certified article language; `coverage` is **candidate scope** rather than measured topical success; `priority` P1 = early probe, P2 = supporting / weekly, P3 = discovery / contextual; `entry_url` is an initial publisher/news/service entry point, **not necessarily an RSS feed**; `method` is indicative; `verification` describes whether a published interface was reviewed or the candidate is unprobed. `host_candidate` is **not validated operator-family identity**.

## Candidate decision tree
1. **Direct official observations:** government diplomacy, central banks, exchanges, maritime incident alerts, sanctions, official incident notices; preserve source attribution and observed-vs-claimed status.
2. **Independent regional reporting:** prioritise native-local journalists + diverse external correspondents for UAE/GCC, Iran, Iraq, Turkey, Yemen, Sudan, Egypt, the Levant, Horn of Africa, Sahel and Afghanistan/Pakistan.
3. **Cross-language gap filling:** Persian, Pashto, Somali, Turkish, French and Hebrew originals may help **English**, but **Arabic-native** credit only comes from authenticated Arabic-language content or separately validated translation (mark it translated).
4. **Structured corroboration:** use GDELT for discovery; ACLED for coded incidents; ReliefWeb for humanitarian events, UKMTO for maritime incident claims, and IMF/EIA/FRED/World Bank for macro fundamentals; do not count discovery indexes as additional independent publishers.
5. **Weekly context:** analyst/think-tank reports and conflict datasets should produce week-to-week trend comparisons and an evidence-grounded Naysayer; do not recycle daily headlines unchanged.

## Shortlist by geographic / analytical need
### Global newsroom backbone — 10
- [Reuters](https://www.reuters.com/) — en; Official site / section; cur-001; P1
- [Associated Press](https://apnews.com/hub/middle-east) — en; Official site / section; cur-002; P1
- [Al Jazeera Arabic](https://www.aljazeera.net/) — ar; Official site / section; cur-005; P1
- [BBC Arabic](https://www.bbc.com/arabic) — ar; Official site / section; cur-004; P1
- [Sky News Arabia](https://www.skynewsarabia.com/) — ar; Official site / section; cur-007; P1
- [Asharq News](https://asharq.com/) — ar; Official site / section; cur-009; P1
- [Al Jazeera](https://www.aljazeera.com/xml/rss/all.xml) — en (registry stream; not certified); feed; en-006; B
- [BBC World](https://feeds.bbci.co.uk/news/world/rss.xml) — en (registry stream; not certified); feed; en-001; B
- [France 24](https://www.france24.com/en/rss) — en (registry stream; not certified); feed; en-017; B
- [DW World](https://rss.dw.com/rdf/rss-en-world) — en (registry stream; not certified); feed; en-018; B

### UAE primary and local — 8
- [WAM](https://www.wam.ae/ar) — ar (registry stream; not certified); html_headlines; ar-s011; B
- [Abu Dhabi Media Office security RSS (AR)](https://www.mediaoffice.abudhabi/ar/security/rss) — ar; RSS (documented or candidate); cur-031; P1
- [Abu Dhabi Media Office security RSS (EN)](https://www.mediaoffice.abudhabi/en/security/rss/) — en; RSS (documented or candidate); cur-030; P1
- [Dubai Media Office](https://mediaoffice.ae/) — ar,en; Official site / section; cur-029; P1
- [UAE Ministry of Foreign Affairs](https://www.mofa.gov.ae/) — ar,en; Official site / section; cur-026; P1
- [UAE National Emergency Crisis and Disasters Management Authority](https://www.ncema.gov.ae/) — ar,en; Official site / section; cur-038; P1
- [Central Bank of the UAE](https://www.centralbank.ae/) — ar,en; Official site / section; cur-041; P1
- [Abu Dhabi Securities Exchange](https://www.adx.ae/) — ar,en; Official site / section; cur-255; P1

### GCC official and financial — 10
- [SPA](https://www.spa.gov.sa) — ar (registry stream; not certified); unverified; ar-s012; B
- [QNA](https://www.qna.org.qa) — ar (registry stream; not certified); unverified; ar-s013; B
- [KUNA](https://www.kuna.net.kw) — ar (registry stream; not certified); unverified; ar-s014; B
- [ONA](https://omannews.gov.om) — ar (registry stream; not certified); unverified; ar-s016; B
- [BNA](https://www.bna.bh) — ar (registry stream; not certified); unverified; ar-s015; B
- [GCC Secretariat General](https://www.gcc-sg.org/) — ar,en; Official site / section; cur-049; P1
- [Argaam](https://www.argaam.com/) — ar,en; Official site / section; cur-056; P1
- [Mubasher](https://www.mubasher.info/) — ar,en; Official site / section; cur-057; P1
- [Saudi Exchange (Tadawul)](https://www.saudiexchange.sa/) — ar,en; Official site / section; cur-053; P1
- [Qatar Ministry of Foreign Affairs](https://www.mofa.gov.qa/) — ar,en; Official site / section; cur-061; P1

### Iran, Iraq & Turkey — 9
- [Iran International](https://www.iranintl.com) — ar (registry stream; not certified); unverified; ar-s022; B
- [IRNA](https://www.irna.ir/rss) — ar (registry stream; not certified); feed; ar-s019; B
- [Tasnim News Agency](https://www.tasnimnews.com/) — fa,en,ar; Official site / section; cur-075; P1
- [IranWire](https://iranwire.com/) — fa,en,ar; Official site / section; cur-082; P1
- [Shafaq](https://shafaq.com/ar?rss=1) — ar (registry stream; not certified); feed; ar-s026; B
- [Iraqi News Agency](https://ina.iq) — ar (registry stream; not certified); unverified; ar-s027; B
- [Anadolu](https://www.aa.com.tr/tr/rss/default?cat=guncel) — ar (registry stream; not certified); feed; ar-s023; B
- [TRT World](https://www.trtworld.com/) — en; Official site / section; cur-093; P2
- [Turkey Ministry of Foreign Affairs](https://www.mfa.gov.tr/) — tr,en; Official site / section; cur-091; P1

### Levant and Israel/Palestine — 9
- [WAFA](https://www.wafa.ps) — ar (registry stream; not certified); unverified; ar-s063; B
- [Times of Israel](https://www.timesofisrael.com/feed/) — ar (registry stream; not certified); feed; ar-s065; B
- [UN OCHA occupied Palestinian territory](https://www.ochaopt.org/) — en,ar; Official site / section; cur-095; P1
- [UNRWA](https://www.unrwa.org/) — en,ar; Official site / section; cur-096; P1
- [Israel Ministry of Foreign Affairs](https://www.gov.il/en/departments/ministry_of_foreign_affairs) — en,he,ar; Official site / section; cur-098; P1
- [Syria Direct](https://syriadirect.org/) — en,ar; Official site / section; cur-107; P1
- [Al Mayadeen](https://www.almayadeen.net/) — ar; Official site / section; cur-113; P2
- [Petra](https://petra.gov.jo/ar/) — ar (registry stream; not certified); html_headlines; ar-s070; B
- [Jordan Ministry of Foreign Affairs](https://mfa.gov.jo/) — ar,en; Official site / section; cur-116; P1

### Yemen and Red Sea — 8
- [Yemen Monitor](https://www.yemenmonitor.com/feed/) — ar (registry stream; not certified); feed; ar-s102; B
- [South24](https://south24.net/) — ar (registry stream; not certified); html_headlines; ar-s082; B
- [Belqees](https://belqees.net) — ar (registry stream; not certified); unverified; ar-s031; B
- [UK Maritime Trade Operations (UKMTO)](https://www.ukmto.org/) — en; Official site / section; cur-119; P1
- [EUNAVFOR ASPIDES](https://www.eeas.europa.eu/eunavfor-aspides_en) — en; Official site / section; cur-120; P1
- [Combined Maritime Forces](https://combinedmaritimeforces.com/) — en; Official site / section; cur-123; P1
- [Sana'a Center for Strategic Studies](https://sanaacenter.org/) — ar,en; Official site / section; cur-125; P1
- [The Maritime Executive](https://maritime-executive.com/) — en; Official site / section; cur-130; P1

### Sudan and Horn of Africa — 9
- [Dabanga](https://www.dabangasudan.org/ar/feed) — ar (registry stream; not certified); feed; ar-s033; B
- [Sudan Tribune](https://sudantribune.com/feed/) — ar (registry stream; not certified); feed; ar-s034; B
- [Radio Tamazuj](https://radiotamazuj.org/) — en; Official site / section; cur-138; P1
- [Garowe Online](https://www.garoweonline.com/) — en,so; Official site / section; cur-141; P1
- [Hiiraan Online (Somali-language edition)](https://www.hiiraan.com/) — so,en; Official site / section; cur-145; P1
- [Radio Ergo](https://radioergo.org/feed/) — ar (registry stream; not certified); feed; ar-s056; B
- [Addis Standard](https://addisstandard.com/feed/) — ar (registry stream; not certified); feed; ar-s059; B

- [IOM DTM Sudan](https://dtm.iom.int/) — en; Official site / section; cur-153; P1
- [UNHCR Sudan situation](https://data.unhcr.org/) — en,ar; Official site / section; cur-154; P1

### Sahel and North Africa — 8
- [Studio Tamani](https://www.studiotamani.org/feed) — ar (registry stream; not certified); feed; ar-s036; B
- [Sidwaya](https://www.sidwaya.info/feed/) — ar (registry stream; not certified); feed; ar-s037; B
- [Alakhbar](https://www.alakhbar.info/latest/rss/) — ar (registry stream; not certified); feed; ar-s039; B
- [Jeune Afrique](https://www.jeuneafrique.com/) — fr; Official site / section; cur-156; P1
- [RFI Afrique](https://www.rfi.fr/fr/afrique/) — fr; Official site / section; cur-157; P1
- [Libya Al Ahrar](https://libyaalahrar.tv/) — ar; Official site / section; cur-162; P1
- [Studio Kalangou Niger](https://www.studiokalangou.org/) — fr,ha; Official site / section; cur-170; P1
- [Burkina24](https://burkina24.com/) — fr; Official site / section; cur-172; P2

### Afghanistan and Pakistan — 7
- [TOLOnews](https://tolonews.com/feed) — ar (registry stream; not certified); feed; ar-s053; B
- [Pajhwok](https://pajhwok.com/feed/) — ar (registry stream; not certified); feed; ar-s054; B
- [Dawn](https://www.dawn.com/feeds/home) — ar (registry stream; not certified); feed; ar-s050; B
- [Afghanistan International](https://www.afintl.com/) — fa,ps,en; Official site / section; cur-178; P1
- [Afghanistan Analysts Network](https://www.afghanistan-analysts.org/) — en,fa,ps; Official site / section; cur-182; P1
- [Pakistan Ministry of Foreign Affairs](https://mofa.gov.pk/) — en,ur; Official site / section; cur-186; P1
- [State Bank of Pakistan](https://www.sbp.org.pk/) — en,ur; Official site / section; cur-188; P1

### Cross-cutting evidence and research — 9
- [GDELT DOC API](https://api.gdeltproject.org/api/v2/doc/doc) — multi; API / structured data; cur-219; P1
- [ACLED Middle East monitor](https://acleddata.com/region/middle-east) — en; Official site / section; cur-221; P1
- [ReliefWeb reports API](https://api.reliefweb.int/v2/reports) — multi; API / structured data; cur-223; P1
- [International Crisis Group](https://www.crisisgroup.org/) — en,ar; Official site / section; cur-196; P1
- [Institute for the Study of War](https://understandingwar.org/) — en; Official site / section; cur-200; P1
- [RUSI](https://www.rusi.org/) — en; Official site / section; cur-198; P1
- [Security Council Report](https://www.securitycouncilreport.org/) — en; Official site / section; cur-210; P1
- [UN Security Council briefings](https://press.un.org/en) — en,fr; Official site / section; cur-227; P1
- [ICRC Middle East](https://www.icrc.org/en/news/middle-east) — en,ar; Official site / section; cur-228; P1

### Finance and macro evidence — 13
- [IMF Data API](https://data.imf.org/en/Resource-Pages/IMF-API) — en; Official site / section; cur-237; P1
- [World Bank Indicators API](https://api.worldbank.org/v2/) — en; API / structured data; cur-238; P1
- [FRED API](https://fred.stlouisfed.org/docs/api/fred/) — en; API / structured data; cur-239; P1
- [US EIA Open Data API](https://www.eia.gov/opendata/) — en; API / structured data; cur-240; P1
- [OPEC publications](https://www.opec.org/) — en; Official site / section; cur-241; P1
- [International Energy Agency](https://www.iea.org/) — en; Official site / section; cur-242; P1
- [Dubai Financial Market](https://www.dfm.ae/) — ar,en; Official site / section; cur-254; P1
- [US Treasury OFAC](https://ofac.treasury.gov/) — en; Official site / section; cur-246; P1

### Cyber and communications — 5
- [Cloudflare Radar](https://radar.cloudflare.com/) — en; Official site / section; cur-264; P1
- [NetBlocks](https://netblocks.org/) — en; Official site / section; cur-265; P1
- [CISA advisories](https://www.cisa.gov/news-events/cybersecurity-advisories) — en; Official site / section; cur-260; P1
- [OONI Explorer](https://explorer.ooni.org/) — multi; Official site / section; cur-267; P2
- [UAE Cyber Security Council](https://csc.gov.ae/) — ar,en; Official site / section; cur-274; P1

## Verified interface examples from official/documented pages, not live source probes
- Abu Dhabi Media Office lists English/Arabic RSS categories including security, government affairs and economy. The individual listed feeds still require an actual parse/freshness probe.
- GDELT offers a news discovery/document API; indexing news stories does not certify the underlying report.
- ACLED documents a data API requiring a myACLED account and token; do not assume anonymous polling.
- ReliefWeb reports API requires a pre-approved `appname` for every call; public documentation does not certify a working account-specific request.
- UKMTO publishes recent maritime security incident records; operational updates should retain event and timestamp attribution.
- World Bank v2 indicators, EIA v2 data API, IMF SDMX and FRED API are **structured macro datasets**, not breaking news sources. Some require registered credentials.
- UNHCR, OCHA, UN Security Council and EUNAVFOR ASPIDES provide humanitarian/official event context, not substitutes for independent news reporting.

Research anchors:
- https://www.mediaoffice.abudhabi/en/rss-news-feeds-abu-dhabi-media-office/
- https://gdeltproject.org/data.html
- https://acleddata.com/api-documentation/getting-started
- https://apidoc.reliefweb.int/
- https://www.ukmto.org/
- https://www.eeas.europa.eu/eunavfor-aspides_en
- https://fred.stlouisfed.org/docs/api/fred/
- https://www.eia.gov/opendata/documentation.php
- https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
- https://data.imf.org/en/Resource-Pages/IMF-API
- https://data.unhcr.org/

## Candidate scoring for B2 integration (100 points)
- 25: proven topical and country-specific relevance over a 7-day evaluation window.
- 20: observed publication freshness and successful HTTP+parse+article timestamp checks.
- 20: primary reporting/record value and independently operated origin diversity.
- 15: native-language suitability and accurate translation provenance where applicable.
- 10: completeness of article-level citation, timestamp and stable URL metadata.
- 10: reliable zero-cost access within bounded rate/volume limits.
**Do not invent scores yet.** All new candidates start `unprobed`; no `PASS` flags until a live test logs status, article dates, parse results and editorial utility. When a homepage is given, discover a feed/API from the publisher rather than fabricating a `/rss` suffix.

## Recommended validation order
**First:** UAE/GCC official + native Arabic, Yemen/Red Sea, Sudan/Horn and Palestine/Israel/Levant. **Second:** Iran/Iraq/Turkey, Sahel/North Africa, Pakistan/Afghanistan and economic data. **Third:** niche analysis, cyber and community discovery. Run 10–20 geographically balanced candidates per bounded probe batch; back off on access failures and never loop the same failing approach more than three times.

Capture per probe: endpoint, publisher, observed HTTP/status, source-supplied publication date, first/last dated item, parsability, count, native language evidence, regions and topics, redirect/duplicate origin, observed freshness, structured-data fields, errors and next action.

## Daily vs weekly product
Daily (English and Arabic): high-confidence new developments, UAE-first in Arabic, succinct attributed claims and **one small critical/Naysayer counter-assessment**. Weekly (separate English and Arabic products): bigger geopolitical/market trend synthesis, changed theses, contradictory accounts, scenarios, review of 3–5 critical assumptions and forecast indicators; think-tank/data sources gain weight. The bilingual Naysayer contract is already specified in `docs/v2/B4_B5_NAYSAYER_DAILY_WEEKLY_CONTRACT.md` and **is not yet implemented**.

## Do not confuse planning with deployment
This batch added **catalogues only**; no sources admitted to production, no live bulk probing, no Discord posts, no model calls, no D1/SQLite resources, no CI dispatch, no scheduling, no protected branch edits. Existing B1–B7 stay partially open; B8 remains blocked.


## 24 October 2026 — trading and market expansion amendment
Owner requested **TradingView** be retained explicitly in English market coverage, with primary macro and exchange sources where necessary. These entrypoints were absent from both the original 222-record V2 baseline and original 509-row candidate catalogue; this amendment adds **9 curated rows** (4 TradingView functions and 5 macro/market alternatives), and **5** to the prioritized shortlist. These are research candidates, not live admission.

- [TradingView News](https://www.tradingview.com/news/): broad markets editorial discovery, symbols and providers; deduplicate syndicated Reuters/Dow Jones items against their origin.
- [TradingView Economic Calendar](https://www.tradingview.com/economic-calendar/): expected/actual/prior economic events as an editorial and calendar reference.
- [TradingView News Feed Widget](https://www.tradingview.com/widget-docs/widgets/news/news-feed/) and [TradingView Markets](https://www.tradingview.com/markets/): browser-display components and context, not a historical numeric API.
- [CME FedWatch](https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html), [Cboe VIX](https://www.cboe.com/tradable-products/vix), [ECB Data Portal](https://data.ecb.europa.eu/), [Bank of England monetary policy](https://www.bankofengland.co.uk/monetary-policy) and [US Treasury yields](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?field_tdr_date_value=2026&type=daily_treasury_yield_curve) complement existing FRED, EIA, IMF, World Bank, ADX and DFM source references. Confirm each machine-readable endpoint and date semantics before using values.

TradingView's widget documentation confirms browser-display components and states there is **no general public API to extract its market data**. The English product therefore should show TradingView news and widgets when appropriate but calculate market statistics from primary structured feeds. The Arabic geopolitical-only product must not import any trading widgets or market-news sections. Full revised editorial boundary: `docs/v2/EDITORIAL_PRODUCT_ARCHITECTURE_2026-10-24.md`.
