# B45 Live English / Somali to Arabic — FREE-only route diagnostic

As of 27 October 2026, the older `arabic_newsletter/LLM_STATUS.json` records from September 24, not the present. This isolated workflow reuses existing read-only GitHub secret names without changing them; it has a hard HTTPS OpenRouter free-model allowlist. Production's configured non-free GLM fallback is never called. Max two primary and one optional genuinely FREE fallback calls, 400 tokens each, zero publisher-sourced text transmitted. English and Somali synthetic examples retain 12/27 and a provisional/negative claim. Model response must return the exact source digest and pass existing B45/Arabic production validation. The output includes only statuses and attempts, never model text, key or full configured URL. Live provider connectivity can pass; independent semantic equivalence and real-source translation remain HOLD.

Hosted test pending. No canary.

## Initial real hosted evidence

[Run 40485098814](https://github.com/4mghonly/AggregateIT/actions/runs/40485098814) **SUCCESS** (5/5 focused), two genuinely free primary calls: **Somali→Arabic STRUCTURAL_PASS**, English→Arabic **HOLD_RuntimeError**; configured nonfree fallback **NOT CALLED**, zero charged-model calls. Sanitized artifact `12723759715`. One materially different, shorter constrained JSON English retry is now allowed in the otherwise identical isolated free-only path, with an absolute four-request ceiling. A result does not validate independent semantics or real publisher material. Retry hosted run pending.
