# B45 — Third distinct zero-cost model candidate

After unstable `openrouter/free` round 1 (Somali pass/English failure) and round 2 (English pass/Somali failure) on original synthetic fixtures, this bounded **final** test changes the actual selected MODEL to `nvidia/nemotron-3.5-lightning:free` while reusing only the existing OpenRouter primary credential in V2 isolated GitHub Actions. Public OpenRouter confirms $0 token price for this exact slug as of 27 October 2026. At most two calls, 400 tokens each; no publisher text, third-party secrets exposed, GLM paid calls or Discord. It is another model on the same OpenRouter platform, **not independent-provider redundancy**, and a syntactic pass is not independent factual translation quality. No production model configuration is altered.

See https://openrouter.ai/nvidia/nemotron-3.5-lightning%3Afree

Hosted measurement PENDING. If this test fails or is ambiguous, stop repeated probes and preserve translation gate HOLD.

## Final B45 live-route evidence: STOP retrying without a materially new configuration

- [First actual FREE OpenRouter run #40485098814](https://github.com/4mghonly/AggregateIT/actions/runs/40485098814) **SUCCESS** as a diagnostic workflow (5/5 focused); English synthetic structural check **failed** (`HOLD_RuntimeError`), Somali synthetic structural check **passed**, primary free model called twice; nonfree configured fallback skipped, **0 paid calls**. Metadata artifact `12723759715`.
- [Second distinct constrained-prompt run #40485758097](https://github.com/4mghonly/AggregateIT/actions/runs/40485758097) **SUCCESS** as diagnostic (6/6 focused); English **passed after a shorter JSON retry**, Somali **failed**, 3 actual free requests; actual independent fallback route still untested, **0 paid calls**. Metadata artifact `12724782710`.
- [Third distinct named model #40486907517](https://github.com/4mghonly/AggregateIT/actions/runs/40486907517) used independently listed $0 `nvidia/nemotron-3.5-lightning:free`; workflow **SUCCESS** (4/4 focused) but both real provider translation probes **HOLD_RuntimeError**. Two calls, **0 paid calls**; artifact `12725880556`.
- Original Arabic production artifact #40471115356 confirms foreign translation **3 of 8**, primary invalid JSON/empty output in several batches, and fallback attempts **HTTP 403**. That route cannot be deemed operational; no secret was modified or paid provider called.
- **B45 acceptance: HOLD.** A structural pass on synthetic text does not prove real-publisher translation, semantic accuracy, number/name preservation at scale, or independent primary-to-fallback failover. The free router was inconsistent; OpenRouter itself cautions that free tiers are rate limited and not production-reliability guarantees. Stop after these three materially different experiments. A newly configured, authorized, working independent fallback and sustained evaluation on rights-cleared source samples are required.

Production main and live credentials unchanged.
