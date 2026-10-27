# AggregateIT V2 — B40/B41 joint no-post continuation (27 October 2026)

Branch: `rebuild/aggregateit-v2`  
Starting V2 revision: `a57b920e6836de289c9f92a14ab2a54cddad5ee9`

## B40 — Real identical-input headline selection and held preview

The original V1 English/Arabic parser functions and V2 parser each consume a single, identical in-memory RSS byte buffer from BBC World English and Al Jazeera Arabic. B40 now measures identity agreement and the layout of *source-headline-only* preview cards for V1/V2 candidates without writing source bodies or titles to GitHub artifacts. The preview HTML uses the same held preview component for both sets and is **not a comparison of V1/V2 native Gazette renderers or model editorial choices**. Legacy parser blob SHA-1 identity must pass; any mismatch fails closed. France 24 is not fetched.

## B41 — Pinned live production baseline and rollback preflight

A second read-only checkout of `main` is inspected in the same GitHub runner; the exact production SHA is recorded, including routine source-audit auto-commits. A static source inspection pins cron schedules, production workflow names, candidate/production workflow differences and actual legacy parser bytes. It explicitly flags when the existing Arabic source-audit workflow has authority to advance `main`, which must be handled before a controlled cutover. The V1/V2 rollback sequence is simulated using actual checked-out commit IDs, but routes are never switched and no webhooks are contacted.

The current `main` is already known to have advanced from `cb10eb3` to `ea52e14` via `arabic_newsletter/SOURCE_AUDIT.json` only. The GitHub-hosted second checkout rechecks the live head at run time; the preview still verifies the prior pinned `main.py` and Arabic collector blobs, refusing drift.

## Acceptance boundaries

No model/translation execution; no genuine article-body-to-full-native V1/V2 comparison, authenticated Discord receipt, physical Discord-client verification or tested live rollback. B40 genuine full-editorial acceptance and B41 live production canary **remain HOLD**. No release is authorized. Six of eight historic verification checkpoints remain complete; existing estimated production readiness of 60% is not advanced by unmeasured evidence.

## Execution

B40 and B41 focused tests authored first; one isolated Actions run with a max runtime of 18 minutes, full installed regression once, no secrets, no Discord, no paid inference, no production/main writes. No publisher feed originals saved. Tests and run observations will be added after completion.

Status: **B40/B41 no-post preflight executed successfully; live full-system/canary gates remain HOLD**.

Corrected hosted run [#40461615674](https://github.com/4mghonly/AggregateIT/actions/runs/40461615674) **SUCCESS** on `78e78e104a4a4b38bf9363b4a1ac7537fdbf12e2`: focused **19/19**, V2 **561/561**, legacy English **153/153**, legacy Arabic **55/55**. BBC World EN and Al Jazeera AR true identical-input candidate+held headline previews both returned `COMPARED` and `parity=true`; this is source-only preview agreement, not native Gazette or LLM equality. B41 production baseline pin `ea52e14bc7fd2973058fd659f0ff2e8d617111dc`; its findings: `production_audit_can_advance_main_during_canary` and `production_source_floor_below_two_somalia`. Release status remained `can_release=false`. Sanitized artifact `12714647105`, 2-day retention. Neither workflow, production branch, database, LLM nor Discord was changed. The original failed test-only run is retained in history.

## Verification correction and production source-floor finding

Initial [Actions run 40461369606](https://github.com/4mghonly/AggregateIT/actions/runs/40461369606) exposed a syntax error in one newly authored B41 test. No full-suite or live preflight result is claimed from that failed run. The B41 test was corrected and a regression was added for the actual production audit's insufficient Somalia source floor.

The separately checked current production [Arabic Source Audit #40460139191](https://github.com/4mghonly/AggregateIT/actions/runs/40460139191) returned **FAILURE** with `somalia: 1` compatible source where the workflow requires at least **2**. This is a live source-coverage issue to resolve before cutover. The B41 preflight now reads the checked-out production audit record, reports underfloor regions, and keeps release on HOLD. No production files were changed here.

Corrected one-shot hosted CI: **PASS** (run 40461615674).

## B41 Somalia source audit — precisely identified

Current production `arabic_newsletter/SOURCE_AUDIT.json` (checked 2026-10-27 06:17:20 UTC) reports **59 compatible out of 118 audited sources overall**. For Somalia: **one compatible source**, below the production minimum of two. Publisher status in that audit:

| Source ID | Publisher | Audit result |
| --- | --- | --- |
| `s056` | Radio Ergo (Somali-language) | compatible (`ok`) |
| `s057` | SONNA Arabic | zero entries |
| `s058` | Goobjoog | HTTP 404 |
| `s094` | Hiiraan Online | no feed |

Note that the earlier `arabic_newsletter/sources.json` still records Goobjoog as enabled/previously compatible; this is historical metadata, not evidence it still works. The correct remedy is a separately revalidated feed or repaired publisher URL, followed by a clean compatibility audit. Nothing was enabled, promoted or changed in production as part of this batch.

