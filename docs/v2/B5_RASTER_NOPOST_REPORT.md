# AggregateIT V2 — B5b Synthetic Raster Preview Evidence

Date: 23 October 2026 (UAE)  
Branch: `rebuild/aggregateit-v2`  
Classification: **In-memory visual prototype only — no live briefing delivery authorization**

## Result

- `v2_raster_preview.py` renders the existing strict B5 layout contract into actual Pillow PNG bytes **entirely in memory**. It never opens an output file, reaches a network, discovers credentials or sends Discord.
- English Gazette: exactly two 2480×3508 pages; 1200-pixel-width resized preview.
- Arabic command briefing: exactly three 3840×2160 slides; 1600×900 resized preview with Pillow/RAQM for RTL shaping.
- Original `v2_layout.py` admission and `delivery_authorized=False` remain unchanged. The rasterizer rejects tampered styles, claimed publishable layouts, missing preview fonts, oversized unbroken words and quote content exceeding fit. No ellipsis, silent crop or automatic unsafe shrink below the font floor.
- Colors are inherited from the source contract: Arabic dark navy, muted gold, high-contrast light text; English warm ivory, dark brown and terracotta. Both have prominent **OFFLINE • SYNTHETIC** and **NOT FOR DELIVERY** notices.
- The rendered images were visually inspected **at 900px wide (Arabic) and 900px wide (English)** in the isolated execution tool. A sparse bilingual fixture showed readable native-script content with no visible clipping. Empty space was expected from the one-item synthetic sample.
- A separate stress case exercised a synthetic Arabic regional page containing six 165-character quote cards, within the page's 1,000-character budget. All six rendered with no clipping reported. This does not establish fit for every possible quote/script/font or real briefing.

## Evidence

- `tests/test_b5_raster_preview.py`: **8/8 PASS** with actual Pillow/RAQM, including full PNG headers/SHA-256, required 2/3 dimensions, scaled image dimensions, dense card fit, wrong-font and fail-closed conditions.
- Combined B3–B7 offline and B2 gate suite: **125/125 PASS** in memory (previous 117 + B5 8), using the current branch's actual Python module source. Full dependency-installed application tests were not run.
- Preview used the installed **DejaVu Sans** fallback. The preferred **Siraj Noir** font was **not** available in this environment; therefore the observed Arabic shaping/visuals cannot certify Siraj Noir legibility, kerning or metrics.
- No real source texts, verified translations, Arabic image encoding in Discord, smartphone screenshot, Discord image compression, source-specific terms, verified SLO, or production scale test are established.

## Remaining B5 acceptance

1. Supply approved Siraj Noir font binary with provenance/license and reproducible font installation; repeat RAQM and glyph fallback test using it.
2. Render actual frozen and rights-qualified sample editions, including longer mixed Arabic/Latin text, source dates, Eastern/Western digits, multiple countries and worst-case page density; revise admission if pixels cannot fit instead of cropping.
3. Review full-size and actual phone/Discord-size screenshots for sharpness, sufficient body size, contrast, RTL correctness and source attribution. Capture QA approval as explicit evidence, not inferred from green unit tests.
4. Test actual Discord-upload response image dimensions/quality only with separate owner-approved controlled no-post/canary infrastructure. Until then B5 remains PARTIAL.

**No external modification:** main, scheduled CI, production workflows, Discord, Cloudflare, analytics database, source registry or paid resources untouched.
