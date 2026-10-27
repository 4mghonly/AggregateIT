# AggregateIT V2 — B38-B39 genuine parser replay and durable no-send rehearsal

Date: 27 October 2026  
Base GitHub SHA: `907d046ec7e101df56cec078ea240368d86f5edd`  
Branch: `rebuild/aggregateit-v2`

## Objectives and boundaries

B38: Use one actual immutable publisher RSS byte buffer per source for the existing V1 parser and V2 parser on a bounded GitHub runner; compare eligible records, source SHA-256 and source-only mobile card counts. Sources: BBC World English and Al Jazeera Arabic. Do not probe France 24 again. Source raw bytes, headlines, links and HTML stay in memory and are never included in stored artifacts.

B39: Exercise the real local POSIX receipt-store code in a disposable directory. Reserve independent English and Arabic delivery slots, record simulated ambiguous network outcomes, close and reopen the store, verify no blind retry, wrong destination refusal and synthetic rollback tabletop. This never sends or changes a route.

## Test-driven verification

Tests created before production modules (RED: missing modules). New B38 and B39 tests verify exact bytes, source mismatch HOLD, bounded transport attempts, invalid URL rejection, disk reopen idempotency and caller-flag no-release enforcement. Hosted [run 40455040595](https://github.com/4mghonly/AggregateIT/actions/runs/40455040595) completed **SUCCESS** on `74e92d3375f71749de2f8469f834f9b0f312b147`. B38/B39 focused **10/10**, entire V2 **542/542**, English legacy **153/153**, Arabic legacy **55/55** passed. Live same-buffer source parser comparison reported `shadow_status=COMPARED` and `parity_all=true` for the two pinned publishers; local receipt-store crash marker persisted (`crash_marker_durable=true`). `can_release=false`. Aggregate metadata-only artifact ID `12711188931`, with 2-day retention. No original publisher XML was persisted.

## Exit conditions and holds

- Actual same-buffer source-level parser comparison **does not equal** full identical-input newsroom/LLM/render/delivery V1/V2 shadow.
- No live model translation or editorial factual assessment.
- Durable local receipt recovery **does not equal** a controlled live rollback or authenticated Discord receipt.
- No separate cutover authorization is inferred from this development request.
- Source rights/legal research intentionally excluded from AggregateIT V2 engineering acceptance.
- Overall operational evidence remains **6/8 (75%)** until two final real-world gates are demonstrated.

No production/main writes, schedule/webhook/secret/DB modifications, paid API use or Discord posts.
