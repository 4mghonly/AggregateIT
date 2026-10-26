# AggregateIT V2 — B35 France 24 Arabic RSS discrepancy

Date: 26 October 2026  
Branch: `rebuild/aggregateit-v2`  
Prior acceptance evidence: B34 [run 40388155216](https://github.com/4mghonly/AggregateIT/actions/runs/40388155216)  
B35 diagnostic commits: `4f41f340` initial, `b165642f` duplicate-classifier correction

## Observed B34 issue, not resolved

B34 captured **41,930** original bytes from `https://www.france24.com/ar/rss`
with HTTP 200. Exact-byte V1/V2 parser comparison found **24 eligible
V1 items, 23 V2 items, one V1-only and zero V2-only**. The capture's
SHA-256 was retained in B34 metadata, but the bytes and exact rejected
record were intentionally **not** retained. It is impossible to infer the
missing record or its cause from its hash alone.

## B35 execution record

| Hosted run | Test outcome | Live capture | Outcome |
| --- | --- | --- | --- |
| [40391914604](https://github.com/4mghonly/AggregateIT/actions/runs/40391914604), initial `4f41f340` | 5/6 synthetic diagnostic tests; duplicate-link classification assertion failed | **Not attempted** (step skipped) | FAIL; no publisher-byte artifact |
| [40392140574](https://github.com/4mghonly/AggregateIT/actions/runs/40392140574), corrected `b165642f` | **6/6** focused and **516/516** full V2 Python regression PASS | Single bounded pinned-HTTPS France 24 request returned **HTTP 403** | FAIL at live feed step; no RSS bytes and no diagnostic JSON artifact |

The classifier error was specific to a case where a rejected duplicate
link shares a URL with an admitted item. It initially misreported the
later record as title/timestamp identity drift because a URL-level lookup
found the admitted record first. Corrected classifier now resolves an
exact rejected duplicate by title and timestamp before inspecting the
admitted URL. This is **diagnostic-only** code; it does not modify the V2
source parser or V1.

The corrected run attempted one public-IP-pinned HTTPS request with
9-second timeout, 1 MB limit and one permitted same-host redirect.
HTTP 403 was a refusal from the endpoint, not a successful capture.
The B34 and B35 requests used the same source and transport code but
slightly different `Accept` headers (B34 included Atom, B35 did not).
No causal attribution is possible from that difference. Rate-limiting,
publisher policy, and transient edge behavior remain unverified
hypotheses; **no circumvention or repeat probe was attempted**.

## What the evidence establishes

- On B34's original input, V1 and V2 parser eligibility **did not align**.
- The B35 diagnostic classifier passes focused synthetic tests, including
  duplicate-link classification and metadata-only redaction.
- A new live same-byte comparison was **not obtainable**, and the
  historical exact cause is **NOT DETERMINED**, **NOT REPRODUCED**.
- Static parser review: V1 uses `feedparser` and canonicalizes URLs;
  V2 uses strict ElementTree fields, date freshness, URL gating and
  duplicate detection. These are potential differences, **not an
  explanation of the actual B34 item** without source bytes.
- No raw article titles, URLs, bodies, feed XML, or publisher bytes were
  written into GitHub artifacts for B35; no file artifact was generated.
- Production `main`, V1 source, V2 parser, schedules, models, webhooks,
  Discord delivery and database state remain unchanged.

## Acceptance and handoff

B35 has **2/3 diagnostic gates met** (focused tests, full V2
regression); fresh original-source comparison is blocked by HTTP 403.
**Operational evidence bar remains 6/8 (75%)**, carried over from B34,
not increased by this incomplete diagnosis. Parser parity **HOLD**,
genuine editorial/delivery shadow **HOLD**, and canary/rollback **HOLD**.

To close the specific B34 discrepancy, obtain a permitted exact publisher
RSS capture with provenance and short-lived isolated access, then apply
the unchanged V1/V2 in-memory comparison and the B35 reason classifier.
A new source request or capture path is a separate authorization decision.
Do not change parser or promote source on conjecture.
