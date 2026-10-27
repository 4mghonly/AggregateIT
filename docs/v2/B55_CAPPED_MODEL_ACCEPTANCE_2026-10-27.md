# AggregateIT V2 — B55 paid-model acceptance under USD 0.50
27 October 2026. **User-authorized cap USD 0.50**; existing `LLM_API_KEY` GitHub secret reused as OpenRouter credential in isolated V2-only job. Production secrets/models untouched.

OpenRouter listings used:
- `qwen/qwen3.5-flash-20260224` primary translation — published $0.065/M input, $0.26/M output.
- `deepseek/deepseek-v4.1-flash` independent-family fallback — varying provider rates, public approximately $0.13/$0.52 per million.
- `google/gemini-3.1-flash-lite` independent quality-check candidate — $0.25/$1.50 per million.

Six deterministic maximum one-shot calls (three models × English/Somali), 600 output tokens per call and conservative doubled cost reservations at rates well above published price. The runner refuses further requests rather than exhausting cap; reserved ceiling across this batch is substantially below $0.50. No automatic retry, no production inference routing, no Discord, no publisher text: self-authored fixtures preserve 12/27 and explicit negation. Same B45 existing production Arabic validator/digest gate reused. Only aggregate statuses and spend reported, no raw model outputs/keys/prompts in artifacts. This proves runtime connectivity and limited structural correctness at most; **not** source-grounded semantic fidelity, official issuer permissions, full V1/V2 parity or a live production-ready fallback. External changes to provider pricing or insufficient credit can cause HOLD.

The previous 3 free-model experiments and their failure evidence remain closed, not repeated. Original authentic English/Arabic V1 full PNG archives are already verified by B53/54, but they lack like-for-like original source feed bytes and same-slot V2 final outputs; no fabricated equivalent evidence is allowed.

Hosted run: PENDING. Production readiness 60% planning estimate; formal gates 6/8, canary HOLD.
