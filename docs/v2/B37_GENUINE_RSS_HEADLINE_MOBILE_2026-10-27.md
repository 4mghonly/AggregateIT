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

TDD RED: new renderer module initially absent, focused import test failed. TDD GREEN: 5/5 headline-renderer tests passed locally. Hosted live source and browser test **pending** at this first commit. The full V2 regression is rerun in hosted workflow; B36 earlier regression was 527/527, legacy 153/153 English and 55/55 Arabic.

## Limitations

A successful mobile result covers the browser layout of source-headline cards, not a genuine two-page English Gazette or three-page Arabic intelligence edition. Emulated Chromium is not a physical Discord-client rendering. Production cutover and full-system V1/V2 comparison remain HOLD; operational evidence gates remain **6/8** until their actual criteria pass. No Discord post, model call, database change or production deployment is performed.
