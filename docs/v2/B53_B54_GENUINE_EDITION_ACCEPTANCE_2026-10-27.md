# B53–B54 — Recover genuine English and Arabic originals; enforce release blockers

Date: 27 October 2026. Isolated `rebuild/aggregateit-v2`, **NOT a production canary**.

## New original V1 evidence

Authentic production main `ea52e14bc7fd2973058fd659f0ff2e8d617111dc`:
- English Gazette original two-page 4K (RGBA) `Intelligence Slide Deck` [run 40497262560](https://github.com/4mghonly/AggregateIT/actions/runs/40497262560) ZIP artifact **12731017257**, SHA256 `0f1353b89266a0ba3171abfe6823db5cdcc64c493a9477c6c23baf430803f1c1`, native page SHA256 `b024bf5768bf0470c8f60e31f388c15c839483055d27289ec52e72a5a0d80601`, `518756c1bdf3acb2e15c56dfeb6e69e7f62eb207a5763da99ce207ab3926fa22`. Health **degraded** and `llm_ok=false`; application claims delivery, no independently fetched Discord receipt.
- Arabic original 3-page 4K (RGB) [run 40517778731](https://github.com/4mghonly/AggregateIT/actions/runs/40517778731) ZIP artifact **12741710341**, SHA256 `3ba4943ebeeaab828f8285d727a1787d6178000f8d8377004b9edf7a3f1ff1bd`, original window 12:08:46–18:08:46 UAE. Translation **2/8**, several fallback HTTP 403s. Three full original PNGs measured with exact SHA256 and dimensions.

Previously B49 identified only an English engine JSON archive without finished PNGs; the Gazette's separate slide-deck artifact resolves that *one evidence discovery gap*. It **does not** supply original source byte snapshots, synchronized V1/V2 inputs, a successful original LLM, full-week history, legal rights, semantic translation acceptance, or independent Discord verification.

## B54 acceptance logic

New deterministic test/runner takes pinned real originals and keeps `can_release=false` regardless of caller assertions. Tests cover archive digest tampering, ZIP traversal/size bounds, correct native pages, nonpublishable cross-slot originals, model/translation degradation, production audit dependency and external receipt/rights absence. Production `main` read-only checkout checks the Source Health Audit workflow dependency (missing `requests` previously observed). No workflow dispatch, paid API, source scrape or external posting.

The visual pages exist, but **manual visual legibility/content QA and a real synchronized source-to-edition V1/V2 comparison are not proven**.

Run verification: **PENDING**. B45 live independent fallback and source-grounded semantic quality: **HOLD**. B49 genuine full-edition parity: **HOLD**. B50 canary: **not authorized**.
