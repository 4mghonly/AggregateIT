# B58 chosen models and actual release blockers

Select Gemini 3.1 Flash Lite as the candidate primary, GPT OSS 120B as the candidate independent fallback. Both passed synthetic EN/Somali structural tests. Actual production controller successfully switched to GPT-OSS under *injected* primary failure; this is not a real primary outage or full quality test.

User's $0.50 cap remains intact. Recorded B55+B56+B57: 12 model requests, provider-reported total $0.0024507, conservative budget reservation $0.101496. No further paid calls scheduled.

Staged config only in config/v2/b58_staged_paid_models.json (explicit disabled), reuses LLM_API_KEY name. Does not modify production main model/secrets.

Qualitative inspection of real EN+AR original five 4K pages found English title/lead mismatch, plot/sector label clipping; Arabic empty UAE priority panel, tight font and repeated sections. These are original V1 issues and must not be mistaken for V2 defects without same-source pairing.

Material remaining gates: rights-cleared actual source-grounded Arabic translation and independently checked semantic quality; complete corresponding V1 and V2 editions sourced from identical inputs/window; successful production audit dependency, full 7 genuine weekly-day snapshots, verified client-side Discord receipts, and authorized separate canary.

Production acceptance HOLD; no model change, Discord post, DB write, deployment or main edit.
