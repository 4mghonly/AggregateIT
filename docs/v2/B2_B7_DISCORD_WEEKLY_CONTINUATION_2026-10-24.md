# AggregateIT V2 — Discord-first, Weekly Intelligence, and RSS Probe Batch

Date: 24 October 2026 (UAE) · Isolated branch: `rebuild/aggregateit-v2`

## Authorization and boundaries
Approved direction: 6-hour news briefing rhythm starting 06:00 UAE, English *geopolitics + financial markets*, Arabic *geopolitics/security only*, weekly analytical counterparts, improved professionalism for **daily Discord output**. Live production URLs, `main`, webhooks, schedules, GitHub Actions, D1 provisioning, deletions and paid inference were not modified.

## Repo inspection — major correction
- **Existing `tv.py` is active code candidate for reuse.** It already implements TradingView scanner pulse/universe/movers and macro scanning with persisted prior snapshot. Absence from the V2 source registry did **not** imply TradingView functionality had been removed from the repo. `market.py` builds English market pulse summaries; preserve and characterize both before rewriting.
- Existing `weekly.py` is an English-only embed over event counts/statuses with a direct webhook sender. It does **not** implement the newly requested deep EN+AR weekly synthesis. Do not call its `main()` as part of testing.
- Official TradingView documentation says widgets supply their own data and do not provide a general market-data export API. The existing Python scanner endpoint is a separate pre-existing implementation, whose current live compatibility and operation remain unverified. Do not remove it; add provenance and fallback after isolated integration tests.
- Discord attachments policy is evolving. V2 intentionally uses a conservative 8 MiB per-file internal ceiling and at most ten attachments per *one logical message* pending deployment-specific validation. Do not extrapolate a passed packaging mock into a confirmed Discord receipt.
Research: https://www.tradingview.com/widget-docs/faq/data/ , https://www.tradingview.com/widget-docs/widgets/news/news-feed/ , https://support.discord.com/hc/en-us/articles/25444343291031-File-Attachments-FAQ .

## Batch D1 — Discord-first packaging (new functionality)
Files: `v2_discord_edition.py`, `tests/test_v2_discord_edition.py`.
- Constructs **one** English `discord_webhook` or Arabic `discord_webhook_arabic` symbolic message manifest with 2 English or 3 Arabic daily PNGs.
- Rejects false hashes, bad file signatures, mixed attachments, duplicate names, unbounded sizes, naive slot timestamps, unsafe mention markup, and non-synthetic publishing attempts. Weekly may contain bounded image or PDF attachment packs.
- English daily must include geopolitical and financial editorial topics (actual market values remain explicitly unavailable where absent); Arabic rejects all financial/trading topic labels.
- No webhook URL or sender is included; `can_send=False` is contractual, **not** a surrogate for durable receipt integration.

Bridge: `v2_discord_rehearsal.py`, `tests/test_v2_discord_rehearsal.py` wraps existing safe V2 real-English and real-Arabic renderers and passes their resulting PNG hashes into the new bundle, all NO-POST. Python tests mock renderer boundaries but actual end-to-end bridge against the full repository remains unrun.

## Batch D2 — Bilingual weekly synthesis
Files: `v2_weekly_rollup.py`, `tests/test_v2_weekly_rollup.py`.
- Consumes multiple previous B4 evidence-gated daily plan snapshots across seven days, deduplicates by stable event ID, records observed event version revisions and covered/missing regions.
- Does **not** falsely call an event `new` without an explicit comparison baseline.
- English accepts dated numerical market observations from a named compatible primary data source, produces a measured weekly percentage only when two comparable dates exist; single observations report unknown. Rejects TradingView *widget* values as unverified backend input.
- Arabic rejects all financial snapshots. Analysis / model interpretation and fact checking remain separately unverified.

## Batch D3 — Schedule contract
Files: `v2_rhythm.py`, `tests/test_v2_rhythm.py`.
- Produces four UAE time slots **00:00, 06:00, 12:00, 18:00** (+04:00), marks **06:00 full morning**.
- Proposes Sunday 06:00 for separate weekly report as a *non-enabled planning option*, not an authorized change to production.
- No scheduler is created or modified.

## Batch D4 — Read-only feed adapter foundation
Files: `v2_feed_probe.py`, `tests/test_v2_feed_probe.py`.
- Bounded HTTPS read-only RSS/Atom parsing with small byte/timeout budgets and basic private-address/unsafe-redirect refusal.
- Distinguishes `usable_dated_feed`, `stale_feed`, `undated_feed`, `empty_feed`, `not_a_feed`, `invalid_xml`, `oversized_body`.
- Discards story bodies, returns metadata counts only. **No live-source probes performed by this module in this batch**, since the isolated container cannot resolve external hosts; status after runtime remains unknown. The parser is a first adapter, not a fully verified RSS/HTML/API ingestion stack.
- A failing-first test exposed RSS date parsing that mistakenly classified `GMT` (which contains uppercase `T`) as ISO; fixed parser now tries ISO and RFC email formats. The focused suite passed afterward.

## Local validation
- **34/34** focused isolated `unittest` tests pass against local equivalents: 10 Discord manifest, 3 renderer bridge, 9 weekly rollup, 4 UAE rhythm, 8 RSS/Atom feed probe.
- New modules and tests were published to the V2 GitHub branch individually and remotely fetched/inspected for file presence. **Do not claim the repository-wide 231/231 suite has been rerun**, or that the remote GitHub working tree was executed locally: direct repository clone is unavailable in this runtime. Before integration, clone in an authorized connected runner and execute `python -B -m unittest discover -s tests -p 'test_*.py' -q` plus Arabic and English layout regression suites.
- Mobile/desktop editorial CSS prototypes were polished, source metadata and Discord edition labels added. Playwright Chromium check reports **8 view screenshots, 4 mobile overflow checks, 0 uncaught JS exceptions**; the user-visible ZIP preview is an external artifact, not a code-integrated native PNG final design.

## Next engineering work (continue in permitted batches)
1. B2 real bounded public RSS/API/HTML compatibility and source-language verification, beginning with TradingView news *discovery* and regional feed candidates.
2. B4 integrate supported LLM editorial analysis and critical reviewer behind evidence/citation validators. Existing Naysayer engine only validates a supplied candidate; it does not generate analysis yet.
3. B5 replace the older native PNG designs after visual approval with Discord-scale fixed layouts; keep one logical message with all page images. Add separate English and Arabic weekly renderers using weekly rollup.
4. B6/B7 durable scheduling/receipt reconciliation, affordable metrics, real equal-window V1/V2 comparison and dashboard. Cutover B8 needs deliberate release approval.

## No silent release claims
The above is tested component engineering and design QA, not completed production deployment. The current published source candidates and TradingView integrations are not certified operational; no Discord deliveries were attempted by this batch.
