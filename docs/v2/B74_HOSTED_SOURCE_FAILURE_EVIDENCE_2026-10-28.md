# B74 — Hosted publisher audit: source-by-source evidence

Run: https://github.com/4mghonly/AggregateIT/actions/runs/40718530045
UTC: 2026-10-28 15:42; branch: rebuild/aggregateit-v2.
The actual hosted job log was read, not merely the green workflow badge.

**114 sources checked; 111 OK; 3 failed (97.37% endpoint audit success).**

| Failed source | Observed status | Classification | Treatment |
| --- | --- | --- | --- |
| IntelNews | 429 | Rate limited | Preserve source; no aggressive retries; investigate feed access later |
| The Independent - Breaking | 429 | Rate limited | Preserve source; avoid immediate retry; seek alternate permitted RSS path |
| Naked Capitalism | 403 | Access denied | Preserve source; investigate alternative public feed; do not treat as parser failure |

Observed URLs: https://intelnews.org/feed/ ; https://www.independent.co.uk/news/world/rss ; https://www.nakedcapitalism.com/feed/ .

The 111 successes mean HTTP 200 plus nonempty parseable entries for RSS or relevant provider-specific audit checks. They **do not** prove freshness, editorial accuracy, independent corroboration, Arabic translation, V1/V2 parity or Discord delivery. The source audit did not validate Somalia's two-publisher floor. No production config changed.

B74 engineering improvement: `audit.py` now emits `audit_summary.json` with rate-limited, access-denied and other categories; the isolated no-post workflow retains it with the raw audit artifact. Await next hosted run to confirm the new summary, not to assert that the three sources have recovered.

## Next execution
- Inspect and repair failed endpoints only when new live evidence justifies a safe replacement.
- Add freshness and independent publisher evidence beyond the HTTP-only audit.
- Capture real synchronized editions, original-to-Arabic semantic checks, and visual QA.
- Keep production release HOLD pending genuine acceptance.
