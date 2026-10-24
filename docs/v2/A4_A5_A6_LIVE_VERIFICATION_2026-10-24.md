# AggregateIT V2 — A4/A5/A6 live read-only execution, 24 October 2026
## Isolation and scope
Ran real HTTPS sources and TradingView *in a separate network-enabled Python session*, with no OpenHands, production scheduler, GitHub Actions, Discord sending, database writes, API keys, or LLM calls. Source modules used for the A6 experiment were retrieved from the existing `rebuild/aggregateit-v2` branch and executed in a temporary remote directory. Production `main` unchanged. UTC observation window approximately 03:09–03:15.

## A4 — 12 installed RSS endpoints
12 distinct URL requests attempted; ten yielded HTTP 200 and parseable RSS or RDF, with publication dates extracted from actual XML bytes; nine had an item within 72 hours. Results:

| Endpoint | HTTP | Items / recent <=72h | Verdict |
|---|---:|---:|---|
| BBC Middle East | 200 | 25 / 7 | usable dated feed |
| BBC Business | 200 | 55 / 37 | usable dated feed |
| Al Jazeera English | 200 | 25 / 25 | usable dated feed |
| Al Jazeera Arabic | 200 | 25 / 25 | usable dated native Arabic titles |
| France 24 Arabic | 200 | 24 / 24 | usable dated native Arabic titles |
| France 24 English | 200 | 24 / 24 | usable dated feed |
| Guardian Middle East | 200 | 20 / 20 | usable dated feed |
| Deutsche Welle World | 200 | 12 / 12 | usable dated RDF |
| NPR World | 200 | 10 / 10 | usable dated feed |
| Abu Dhabi Media Office security RSS | 200 | 24 / 0 | XML works; newest 2026-10-16 20:00 UTC (stale for this window) |
| Al Arabiya Arabic RSS | 403 | — | endpoint rejected this runner; not proof of site outage |
| The National root RSS URL | 404 | — | wrong/retired RSS URL; discover legitimate alternative separately |

Proof: bounded raw-byte reads, final URL, content type, SHA-256 and first two dated article links were collected at runtime. BBC Middle East initially SHA256 `b003fe44afd7fa321a434f880f28cbc4911b1c34fe404a0823dea7033a14090f`; Al Jazeera Arabic `ef32f4960314d90e0a48cbf17f16639a5cfebfc16ddce15e49360d612cef352e`. These are *feed observations*, not proof of independence of publisher families or completeness of all geographic targets.

## A5 — three real TradingView JSON scanner requests
- `https://scanner.tradingview.com/global/scan`: HTTP 200, valid JSON, **4 of 5** requested macro instruments returned; absent symbol is missing, not zero.
- `https://scanner.tradingview.com/america/scan`: HTTP 200 using original `tv.py` 11-column layout; four sample US stock rows; reported `totalCount=20130`; `change_percent` null for some rows while `change` numeric.
- Second reduced US query: HTTP 200, four sample rows.
Added `v2_live_scanner_contract.py` and 5 focused tests: partial/missing reports, null retention, nonfinite refusal and unknown-symbol refusal. **No quote-level exchange timestamp or second-provider corroboration** returned, so results may not authorize live financial publication. Only HTTP read-type scanner queries (POST with query JSON); no orders or snapshot persistence.

## A6 — actual live RSS bytes through actual V2 evidence/editorial modules
Executed the development-branch versions of `v2_feed_probe`, `v2_feed_items`, `v2_evidence`, `v2_evidence_ledger`, `v2_editorial`, `v2_script_guard` and `v2_product_compiler` in the separate networked session; fetched BBC Middle East and Al Jazeera Arabic feed bytes by HTTPS.

| Source | Response | Parsed RSS items | B3 headline-only observations |
|---|---|---:|---:|
| `en-001` BBC Middle East | HTTP 200, 20,012 bytes, SHA256 `da085a97defa9261bcf8b8b728712758a179002716741e4e667b419d18bdac49` | 25 | 3 |
| `ar-s003` Al Jazeera Arabic | HTTP 200, 26,691 bytes, SHA256 `ef32f4960314d90e0a48cbf17f16639a5cfebfc16ddce15e49360d612cef352e` | 25 | 3 |

The B3 ledger returned **6 observations, six article URL identities, six excerpt/claim records and six explicit test events**. The B4 planner and bilingual compiler returned **3 English + 3 Arabic** held candidates with exact source URL and excerpt IDs; English market status unavailable, Arabic market not applicable; `delivery_authorized=False`, model_called false, discord_sent false.

**Important limitations:** For this first real-network B3/B4 proof, `original_text` was the RSS **title**, not verified complete article text. Region, subject country and topic were **test-input annotations**, not independently determined from those news reports; geographic coverage scores therefore are **not credible coverage evidence**. All six candidates remain non-publishable.

As an independent A6 body-access check, direct HTTPS GETs of a BBC Jordan and an Al Jazeera Arabic Middle East article returned 200 and 42 / 9 extractable paragraph segments respectively. Both sample HTML reads reached the specified 220,001-byte response cap; observed SHA-256 values describe **partial bytes only**, not a full article. These paragraphs were *not* passed through the ledger in this run.

## Test results and disposition
- New scanner contract tests: **5/5 PASS**.
- Local offline full suite after addition: **369/369 PASS**, no dependency shims. The published code is logically equivalent to local-tested implementation; *remote GitHub CI was not run*.
- Batch A4: substantial successful live-source proof (10/12 parsed, nine fresh); completeness and long-term regional supply not accepted.
- Batch A5: network scanner compatibility confirmed, market quote time/corroboration still HOLD.
- Batch A6: genuine network → source candidate → evidence ledger → bilingual editorial path demonstrated, **held/not published** pending full article-body and grounded geography/topic verification.
- Configured LLM and fallback **DEFERRED per owner instruction**, no keys requested.
- Next: bounded first-party article body extraction (full bytes, rights, script/freshness), explicit geography/tag provenance, evidence-verified editorial, real no-post native PNG, wider source-family coverage and measured TradingView snapshot timestamps. No production cutover without authorization.
