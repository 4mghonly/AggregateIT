# AggregateIT V2 — Arabic source-bound three-slide no-post bridge

**Date:** 24 October 2026 (UAE). **Branch:** `rebuild/aggregateit-v2`.
**Parent published branch checkpoint:** `9c3888a0b2ea00741fb779c890067cfe614a051c`.

## Genuine renderer boundary exercised

The V2 source-bound B3 journal/replay, B4 original-Arabic admission, B5 layout
contract, and B6 unsent reservation feed a new `v2_arabic_application_rehearsal.py`.
It passes only admitted native-Arabic quote strings and associated source IDs
to `arabic_layout.render_pages.render`, the **actual original Arabic three-page
4K renderer**, in a disposable temporary directory with socket creation
blocked. It never imports the Arabic live collection/sender entry point.

The explicitly synthetic seven-document fixture has three native Arabic
source IDs (`ar-s001/002/003`) admitted and three separate events withheld
for lack of an Arabic original (English/Persian). Actual output: three 3840×2160
PNGs, **0 renderer-reported clipped text items**, no LLM, translation,
Discord, database, source acquisition or external model call. The optional
CLI uses an existing non-symlink output directory and exclusive-create writes,
refusing to overwrite existing paths.

Every story's headline is exactly the permitted Arabic source quote. The
brief's accompanying summary states **synthetic and not independently
verified**; all model assessments are blank. Source IDs and `.invalid`
fixture URLs are shown as attribution without claiming publication rights,
publisher independence or a real event. Actual article language and truth
have NOT been independently verified; the earlier Unicode script guard only
refuses obvious mismatch and cannot detect Persian text mislabeled Arabic.

## Two substantive page-3 fidelity bugs exposed

1. `arabic_layout.render_engine.severity` silently mapped `unknown`/missing
   severity to **Low**. It now displays the neutral label **غير مصنف**
   (unclassified). Explicit `low` is unchanged.
2. `arabic_layout.render_pages` previously used broad geography or a generic
   `security` topic to fill militant/conflict/maritime panels with unrelated
   stories. A simulated port-safety drill was portrayed as a maritime tension.
   Page-3 category membership now requires direct lexical support in factual
   title/summary; speculation in `assessment_ar`/`watch_ar` does not qualify.
   Unsupported panels honestly show **لا توجد مادة مؤهلة**. Counts use the
   same source-text screening. A real attack on a Red Sea ship still qualifies.

These are conservative category filters, **not** factual verification or
complete Arabic semantic understanding. Lexical false positives/negatives
remain possible and require evidence-backed evaluation before production.
No approved production branch or live renderer deployment was modified.

## Verified isolated sample

Final regenerated three-page Arabic synthetic files are uncommitted temporary
QA artifacts. SHA-256:

- Page 1: `14a53d3dbbaaad95b72a883617d9709dce8ffcee76e47c02297ab8f8f98a1f90`
- Page 2: `62d0367c49a820bdb21045fc22401b862c1b3ce02ac47451a928dd4910c8da77`
- Page 3: `a8ab8ee3e2ccf5887038b58738da33f603941494b1b485727b538d18a5a29885`

Page 3 was visually inspected after correction and shows 0 militant, conflict
and maritime-tension categories for three unrelated simulated drills/notices,
with no invented category filler. B5 mobile-scale and final-font decisions
remain open; desktop 4K legibility does not prove Discord preview legibility.

## Test gate

- Arabic V2 renderer/no-post bridge: **7/7 PASS** after a failing-first
  regression showed unknown severity previously mapped to Low.
- Arabic categorical integrity: **4/4 PASS** after three failing-first
  regressions exposed the geography/security-topic fallbacks.
- Full installed V2 suite: **231/231 PASS**, including the 11 new cases.
- Original Arabic application: **55/55 PASS** with mocked Discord/model routes.
- Original English layout: **6/6 PASS** on a fresh isolated rerun after the
  Arabic renderer changes.

**Product gates remain:** B1/B4/B5 PARTIAL; B2 source-rights searches remain
STOP after three nonqualifying alternative approaches; B6/B7 PARTIAL;
B8 BLOCKED. No transfer of synthetic examples to production and no new
authority to publish, provision, schedule, dispatch CI or pay for resources.
