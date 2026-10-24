# AggregateIT V2 — B13 regional rights, balanced visual editions and authenticated V1/V2 shadow evidence

**Date:** 24 October 2026 UAE · **Repository:** `4mghonly/AggregateIT` · **Working branch:** `rebuild/aggregateit-v2` · **Production `main`: READ-ONLY**

## Executive verdict

- **Source reachability coverage:** **17/17** target geographic regions now have at least one real, recently dated, parseable technical feed candidate. This is NOT full article-level topical coverage, rights clearance or native-Arabic analysis across all regions.
- **Regional rights status:** **0/17** regions are approved for publisher-article redistribution or commercial reuse. A 21-source review register names the exact technical candidates, original-language candidates, URLs, and the outstanding permission for each. This is deliberately a **rights-reviewed HOLD**, not a fictitious blanket license.
- **Bilingual visual design:** implemented `v2_b13_balance.py` (geographic fair selection and UAE priority) and `v2_b13_readable_preview.py` (2 English + 3 Arabic large-text 4K pages), both unpublishable and masking real-source copy without permission. Five design previews produced offline using invented text; no model or Discord.
- **Authenticated V1 evidence:** downloaded **three genuine production GitHub Actions artifacts** through the connected GitHub API. Locally recomputed ZIP SHA-256 matches GitHub's recorded artifact digest **for all three**. Extracted run-report and Arabic health/window metadata below.
- **V1/V2 performance comparison:** **HOLD**. Authentic V1 records now available, but V2 remains a two-article no-post pilot. V1 English production runs **bracket** the V2 run in wall-clock time; input sets and observation windows are not matched. The authenticated Arabic V1 window ends at 12:09 UAE, before the V2 midday pilot. Do not publish a misleading win/loss or imply zero measured where an input is missing.

## 1. Regional source coverage and rights research

The previous B11 snapshot had technically usable feeds in **12/17** regions. B13 probed 15 further registered URLs and found recently dated parseable RSS in all **five remaining regions** (not all the tested URLs worked):

| Region previously missing | Source | Lang. | 24 Oct read-only RSS result |
|---|---|---|---|
| Sahel | Studio Tamani `ar-s036` | French | 10 dated, 10 recent |
| Sahel | APS Senegal `ar-s041` | French | 10 dated, 10 recent |
| North Africa | Libya Al Ahrar `ar-s048` | Arabic | 30 dated, 30 recent |
| North Africa | Hespress `ar-s045` | Arabic | 12 dated, 12 recent |
| Egypt | Mada Masr `ar-s046` | Arabic | 10 dated, 10 recent |
| Afghanistan | Amu TV `ar-s055` | Persian | 10 dated, 10 recent |
| Afghanistan | Khaama Press `ar-s091` | English | 100 dated, 35 recent |
| Levant | Enab Baladi `ar-s068` | Arabic | 19 dated, 19 recent |

Also checked but **not** admitted as fresh parseable feeds: Alwihda (Sahel) was parsed French/Latin with 1 Arabic-script title among 15; Masrawy Egypt parsed ten Arabic titles but no dated timestamps; Al Masry Al Youm was HTML, not RSS; SANA returned invalid XML; TOLOnews and L'Orient Today returned HTTP403; Morocco World News HTML endpoint HTTP403. HTTP403 denotes the request path/runner failure, not the publisher being permanently offline.

**Rights review conclusions**
- BBC RSS/metadata: [BBC terms](https://www.bbc.co.uk/usingthebbc/terms-of-use) require permission for business use; website visibility alone does not confer commercial reuse rights.
- Al Jazeera [terms](https://terms.aljazeera.net/) restrict unauthorized copying, data mining and automated scraping and commercial reuse.
- Reuters Connect [terms](https://www.reutersconnect.com/general-terms) limit automated access and commercial republication without written permission (specific Reuters products/licenses need separate inspection).
- WAM [application rights notice](https://wns.wam.ae/public/Privacy-Policy.html) restricts commercial use of application material, without proving anything about other licensed agency feeds.
- WHO [publication copyright](https://www.who.int/about/policies/publishing/copyright): broad WHO publication license is typically **CC BY-NC-SA 3.0 IGO** and cannot be interpreted as commercial permission; third-party materials require distinct review.
- World Bank Open Knowledge Repository: **document-specific** CC BY or CC BY-NC licenses occur; one licensed research paper does not license the site's entire feed. For example [publication 10986/40661](https://openknowledge.worldbank.org/handle/10986/40661) states CC BY 3.0 IGO, a contextual research document, NOT a source of six-hour breaking news.
- For Studio Tamani, APS, Libya Al Ahrar, Hespress, Mada Masr, Amu TV, Khaama Press, Enab Baladi and the remaining candidates, **no usable explicit commercial article-republication grant has been documented**. Their content is withheld and marked `hold_until_document_specific_rights_or_permission_confirmed`. An RSS endpoint and ordinary attribution are not a commercial license.

The machine registry `config/v2/b13_regional_rights_review_2026-10-24.json` records **17 regions and 21 selected technical sources**, no invented publisher ownership independence, no silently translated Persian/Somali/French/Turkish/English content in the Arabic product, and no verified article-level rights.

## 2. Newsletter balance and readability

`v2_b13_balance.py` (9 focused tests) prioritizes source-supported UAE candidates on the Arabic first page, then selects one item from distinct source-grounded regions before repeating a high-volume region. Limits of 2 cards per source and 2 per region apply during fill. It forbids duplicate events, excluded topics, mis-tagged native language, and HTML/unsafe source URLs. No claim is automatically upgraded to verified.

`v2_b13_readable_preview.py` (4 focused tests) generates **3840×2160** PNG pages with enlarged legible headlines, clearly separated country/source, high contrast and lower story density: 2 English pages × up to 5 titles, 3 Arabic pages × up to 4 titles. Real unlicensed article headlines are replaced by an explicit rights hold; only `synthetic=True` rows can display arbitrary test titles. It refuses overwrite, dangerous copyright-bypass text, and duplicate IDs. The previews are an optional **design candidate**, not a silent replacement of the approved production Gazette. User-facing PNGs are locally generated synthetic samples. Readability on actual Discord mobile screens remains to be formally accepted.

Current branch snapshot `b41c1a622e9cd3fae3fb087988ad59b893e8a275` was downloaded and independently tested in an isolated network-enabled environment: **441/441 tests PASS** with no GitHub Actions launched and no model credentials supplied. Archive SHA-256 `df4d2f073bffbe490c3b308bd9e06f15cfb819a72e4ecd89195d4678990e9b72`.

## 3. Authenticated production V1 records and fair comparison

These were downloaded through the **connected GitHub Actions artifact endpoint**, not recreated from a synthetic harness. The archive SHA-256 exactly matched GitHub's recorded `sha256:` value.

| Evidence | Run | Time (UTC) | Authentic artifact digest | Metrics |
|---|---|---|---|---|
| English V1 | [40080890753](https://github.com/4mghonly/AggregateIT/actions/runs/40080890753) | 09:11:56 report | `6163809a…eb07fb` | 515 fetched, 83 new, 48 matched, 3 events, 45 wire, GREEN |
| English V1 | [40084841968](https://github.com/4mghonly/AggregateIT/actions/runs/40084841968) | 10:12:05 report | `3cea8835…7f410` | 511 fetched, 87 new, 47 matched, 3 events, 44 wire, GREEN |
| Arabic production on main | [40076664942](https://github.com/4mghonly/AggregateIT/actions/runs/40076664942) | 08:09:38 completion | `9a19f9d4…48c2a` | 70 inputs, 13 events, 5/9 translated, health degraded, one Discord message confirmed |

Both English engine runs reported **RSS OK 95, RSS failed 2, Discord skipped 4** in their report's `health.json` and did not prove Gazette delivery. Arabic artifact supplied `briefing.json`, `health.json`, three authentic PNGs and state; actual briefing window was **2026-10-24 06:09:38–12:09:38 +04:00**. Degradation was `translation incomplete` with fallback `http_403`; a successful workflow conclusion did **not** mean a healthy translation path.

The V2 genuine one-process HTTP→full body→B3/B4→five native PNG rehearsal occurred **09:49:47 UTC**, between the two English production runs, but used only two explicitly selected articles. Its evidence is `fixtures/v2/a9_true_live_to_native_receipt_2026-10-24.json`. This is a **matched broad midday slot** only; English feed populations, metrics and exact cutoffs differ, and the Arabic V1 window is earlier. It is not a scientifically comparable benchmark.

The machine handoff `fixtures/v2/b13_authenticated_shadow_evidence_2026-10-24.json` records all three authenticated ZIP digests and both V1/V2 timing limitations. `tests/test_v2_b13_authenticated_shadow.py` (4 tests) enforces `same_window_comparison_available=False` and `delivery_authorized=False` until a genuine identical-input, identical-window comparison exists.

## 4. Remaining acceptance gates
1. Establish publisher/item licenses for commercial article quotation or instead transition to legally permissible independently written summaries, with per-item source linking and legal review. **Rights clearance is 0/17**, despite technical feed coverage 17/17.
2. Prepare and score a rights-permitted balanced multi-region real briefing (not synthetic design) with measured mobile and source-balance outcomes.
3. Obtain two **same-input, same-window** V1/V2 manifests with authenticated original bytes and uniformly defined counts; only then use `v2_shadow_scorecard` for a quality comparison. Current evidence is authenticated but NOT like-for-like.
4. Resolve the independently discovered Arabic translation degraded/fallback 403 and English delivery-off production conditions under a separate owner-authorized production batch. This B13 did not modify either.
5. Continue with LLM primary/fallback **DEFERRED** per owner decision until source rights and reliability are cleared. Never change production `main`, secrets, database, scheduling, GitHub Actions or Discord in this batch.

**Bottom line:** source-reachability gap closed across all 17 target regions; rigorous rights statuses documented; demonstrably more region-balanced and readable design candidate; authenticated V1 evidence obtained and checksummed; fair V1/V2 quality comparison correctly held rather than invented.
