# AggregateIT V2 — B37 genuine RSS headline mobile QA

Date: 27 October 2026  
Branch: `rebuild/aggregateit-v2`  
Base commit: `ead4ef1ced6c1eeab0f6de72217abd00a75a1a1e`

## Objective

Continue browser/mobile QA using **genuine English and Arabic RSS headline text** rather than synthetic titles. This is a private **source-watch** preview, not a full editorial edition. It does not assert article-body verification, translated accuracy, event deduplication or delivery success.

## Implementation

- `v2_b37_mobile_headlines.py`: escaped, bounded source-linked mobile page, Arabic RTL, sparse-data fallback, original-script filtering and dates.
- `v2_b37_private_capture.py`: at most one public-IP-pinned HTTPS fetch per source: BBC World English and Al Jazeera Arabic; no France 24 request; original buffers discarded after rendering ephemeral HTML.
- `v2_b37_mobile_browser_qa.mjs`: Chromium tests at 320, 390, 768 and 1320 px for each product, 22px minimum headline size, overflow, heading bounds, visible original-language text and browser error count. Source page requests are blocked in browser.
- GitHub Actions isolated no-secret no-post workflow, self-path push trigger, at most 15 minutes, metadata-only artifact retained 2 days; real headlines/HTML/screenshots are not uploaded.

## Verification

TDD RED: new renderer module initially absent, focused import test failed. TDD GREEN: 5/5 headline-renderer tests passed locally. Hosted acceptance [run 40452327376](https://github.com/4mghonly/AggregateIT/actions/runs/40452327376) **SUCCESS** on commit `9e4ef89cd3f955a4944c2079ee1a0757d892f1bb`: focused **5/5**, full V2 **532/532**. Live HTTPS capture succeeded for BBC World English and Al Jazeera Arabic, each yielding **6** rendered headlines; Playwright Chromium **8/8 viewport checks** passed at 320, 390, 768, 1320px per language. Source-only metadata ZIP artifact ID `12710644338` (2-day retention); source-body bytes, titles, HTML and screenshots were not uploaded. Live captures SHA-256: BBC World `45e762774e00fb4b39ed06f7befe298cef0ebbd85dd9ce69df0f01e8545e0236`; Al Jazeera Arabic `5d6208100c538f4da5c815ef142c34c3959d37b7a7a5570add45cc9a252fa225`. B36 earlier regression was 527/527, legacy English 153/153, Arabic 55/55.

## Limitations

A successful mobile result covers the browser layout of source-headline cards, not a genuine two-page English Gazette or three-page Arabic intelligence edition. Emulated Chromium is not a physical Discord-client rendering. Production cutover and full-system V1/V2 comparison remain HOLD; operational evidence gates remain **6/8** until their actual criteria pass. No Discord post, model call, database change or production deployment is performed.
