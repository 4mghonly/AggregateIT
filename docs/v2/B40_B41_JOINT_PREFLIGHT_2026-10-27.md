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

Status: **PENDING hosted verification**.
