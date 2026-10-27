# B45 Live English / Somali to Arabic — FREE-only route diagnostic

As of 27 October 2026, the older `arabic_newsletter/LLM_STATUS.json` records from September 24, not the present. This isolated workflow reuses existing read-only GitHub secret names without changing them; it has a hard HTTPS OpenRouter free-model allowlist. Production's configured non-free GLM fallback is never called. Max two primary and one optional genuinely FREE fallback calls, 400 tokens each, zero publisher-sourced text transmitted. English and Somali synthetic examples retain 12/27 and a provisional/negative claim. Model response must return the exact source digest and pass existing B45/Arabic production validation. The output includes only statuses and attempts, never model text, key or full configured URL. Live provider connectivity can pass; independent semantic equivalence and real-source translation remain HOLD.

Hosted test pending. No canary.

## Initial real hosted evidence

[Run 40485098814](https://github.com/4mghonly/AggregateIT/actions/runs/40485098814) **SUCCESS** (5/5 focused), two genuinely free primary calls: **Somali→Arabic STRUCTURAL_PASS**, English→Arabic **HOLD_RuntimeError**; configured nonfree fallback **NOT CALLED**, zero charged-model calls. Sanitized artifact `12723759715`. One materially different, shorter constrained JSON English retry is now allowed in the otherwise identical isolated free-only path, with an absolute four-request ceiling. A result does not validate independent semantics or real publisher material. Retry hosted run pending.

## Final B45 live-route evidence: STOP retrying without a materially new configuration

- [First actual FREE OpenRouter run #40485098814](https://github.com/4mghonly/AggregateIT/actions/runs/40485098814) **SUCCESS** as a diagnostic workflow (5/5 focused); English synthetic structural check **failed** (`HOLD_RuntimeError`), Somali synthetic structural check **passed**, primary free model called twice; nonfree configured fallback skipped, **0 paid calls**. Metadata artifact `12723759715`.
- [Second distinct constrained-prompt run #40485758097](https://github.com/4mghonly/AggregateIT/actions/runs/40485758097) **SUCCESS** as diagnostic (6/6 focused); English **passed after a shorter JSON retry**, Somali **failed**, 3 actual free requests; actual independent fallback route still untested, **0 paid calls**. Metadata artifact `12724782710`.
- [Third distinct named model #40486907517](https://github.com/4mghonly/AggregateIT/actions/runs/40486907517) used independently listed $0 `nvidia/nemotron-3.5-lightning:free`; workflow **SUCCESS** (4/4 focused) but both real provider translation probes **HOLD_RuntimeError**. Two calls, **0 paid calls**; artifact `12725880556`.
- Original Arabic production artifact #40471115356 confirms foreign translation **3 of 8**, primary invalid JSON/empty output in several batches, and fallback attempts **HTTP 403**. That route cannot be deemed operational; no secret was modified or paid provider called.
- **B45 acceptance: HOLD.** A structural pass on synthetic text does not prove real-publisher translation, semantic accuracy, number/name preservation at scale, or independent primary-to-fallback failover. The free router was inconsistent; OpenRouter itself cautions that free tiers are rate limited and not production-reliability guarantees. Stop after these three materially different experiments. A newly configured, authorized, working independent fallback and sustained evaluation on rights-cleared source samples are required.

Production main and live credentials unchanged.
