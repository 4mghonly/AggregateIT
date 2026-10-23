# AggregateIT V2 — B2 Source Triage + B4/B5 Bilingual Critical-Review Implementation

Date: 24 October 2026 (UAE) · Branch: rebuild/aggregateit-v2

## Operating boundary
The owner authorized next isolated batches, bounded public read-only verification and development. **No production cutover, Discord delivery, CI dispatch, source-registry promotion, paid models, database provisioning/deletion, or cleanup schedule**. This batch does **not** undertake publisher licensing/legal analysis.

## B2 — 100-source shortlist triage
- New file: `config/v2/source_shortlist_triage_2026-10-24.csv`, preserving all 100 selected sources and introducing scoped evidence observations.
- **16/100 candidate entrypoints examined** using public indexed-page/HTML observations, not programmatic source-runtime HTTP+RSS fetches. Remaining 84 marked `not_yet_checked`. No candidate is accepted into the active source registry on this evidence.
- Official Abu Dhabi Media Office RSS directory directly advertises security and other category RSS endpoints, but specific feed payload/freshness remains unparsed: https://www.mediaoffice.abudhabi/en/rss-news-feeds-abu-dhabi-media-office/
- UKMTO recent incident page showed dated indexed notices (through 20 Oct) from search, but the direct page scraper returned **0 reports**. This is **web-client rendering inconsistency**, not proof of zero maritime incidents or of feed unavailability: https://www.ukmto.org/recent-incidents
- Yemen Sana'a Center accessible, with dated *Yemen Review* and analysis publications around 15 Oct: stronger **weekly context** than six-hour breaking news without fresher entries: https://sanaacenter.org/
- OCHA oPt homepage accessible, last displayed humanitarian situation notices around 19 Oct: periodic primary source, not demonstrated six-hour cadence: https://www.ochaopt.org/
- Dawn homepage accessible with 24 Oct dated headlines, but precise feed/schema parsing not tested: https://www.dawn.com/
- Sudan Tribune homepage accessible with 22 Oct dated news: https://sudantribune.com/
- State Bank of Pakistan official site lists public financial data/publications; no machine feed test: https://www.sbp.org.pk/
- GDELT data documentation and ACLED authenticated API documentation accessible; do not equate access to documentation with successful queried data: https://gdeltproject.org/data.html and https://acleddata.com/api-documentation/getting-started
- ReliefWeb bare `/v2/reports` request failed with 403 in search web client; a correctly configured app query was not attempted: https://api.reliefweb.int/v2/reports
- BBC World and Al Jazeera RSS URLs returned **unsupported XML content-type in the web client**, not a verdict that their feeds fail. BBC Arabic robots-denied, France24 Arabic 403 in the same client, WAM homepage had zero extractable lines. They remain **unknown** until an appropriate compliant RSS/HTML runner checks them.

## B4 — Evidence-bound critical analysis (Naysayer)
- New `v2_naysayer.py`: strict candidate review schema with separate English and Arabic routing; daily one review (110 EN / 95 AR word cap) and weekly three-to-five distinct reviews (550 EN / 450 AR word cap per review).
- Requires review claims and excerpt IDs from the existing B3 ledger; external verified-language map and externally established distinct publisher-family IDs; disallows syndicated-mirror corroboration, unlabeled Persian-as-Arabic, stale evidence, nonexistent excerpts and unverified translation.
- Returns visible `insufficient_evidence` or `withheld` notices instead of constructing an opposition narrative. A missing daily challenge does **not** mark substantive critique quality-green.
- No model prompt/inference, generated editorial claims, actual language certification or publisher-family registry has been connected. All Naysayer results set `delivery_authorized=False` and `factual_accuracy_verified=False` pending separate proof. It is a **candidate validator**, not an autonomous analyst or a released bulletin.

## B5 — Independent daily and weekly bilingual presentation prototypes
- New `v2_naysayer_layout.py`: standalone responsive, deterministic, locally rendered HTML, dark editorial treatment, separate `lang=en/dir=ltr` and `lang=ar/dir=rtl`, constrained daily single-panel and weekly three-to-five-panel view.
- Displays evidence excerpt IDs, week-over-week change, visible abstention; protects HTML markup by escaping user text. Rejects any report with `delivery_authorized=True`. **Not wired into the native Gazette/Arabic slide PNG production renderer.**
- Four **synthetic sample HTML previews** generated locally (not published/posted), covering EN/AR daily and EN/AR weekly. They are labelled "SYNTHETIC / UNVERIFIED — NOT FOR DELIVERY".
- New `tests/test_v2_naysayer.py` and `tests/test_v2_naysayer_layout.py`: tests written failing-first. Locally ran **23/23 focused tests passing** with Python 3.13 in disposable scratch environment: 17 validator + 6 layout tests. The broader current repository V2 suite / actual PNG renderers **were not run** in this batch because GitHub project checkout is not network-accessible from the local testing runtime. Prior 231/231 checkpoint is historical, not renewed here. The remotely committed source was inspected through GitHub; full installed-dependency regression is still a release gate.

## Remaining work before quality gate
1. B2: run a real bounded source-health probe using an appropriate public network runner for the other 84 candidates; validate the first 16 with actual RSS/HTML/API parser; capture article dates, native language and 7-day relevance; reconcile publisher operator families. Do not declare sources healthy from research pages alone.
2. B4: implement verified-language and verified-family admission maps, real claim-level LLM route with citation checks, and measure adversarial usefulness/accuracy; add weekly meaningful-change checks from event history. No forced contrarian conclusions.
3. B5: wire this standalone HTML/layout plan into actual no-post English Gazette and Arabic three-slide renderers, and build separate expanded weekly products without overcrowding daily slides; visually test mobile-scale legibility.
4. B6/B7: add offline telemetry/quality counters and paired authentic V1/V2 report replay once evidence is available. Production cutover B8 remains separately approval-gated.

## Boundary evidence
No changes to `config/v2/source_registry.json` or production routes. Repository changes confined to `rebuild/aggregateit-v2`; no Discord, paid model, CI dispatch, Cloudflare/D1 provisioning, scheduled deletion or protected `main` modifications initiated by this batch.
