# AggregateIT V2 — B34 one-shot GitHub-hosted acceptance

**Date:** 26 October 2026
**Branch:** `rebuild/aggregateit-v2`
**Starting HEAD:** `8681fb2fcc01ea034d9b4918c763f7f1df489b15`
**Unchanged production reference:** `cb10eb38c056755903434d1327de878b0d1d0b38`

## Purpose and safety

A single branch-only `push` trigger, matching only a change to
`.github/workflows/v2-isolated-acceptance.yml`, executes a read-only
GitHub-hosted verification. Existing production workflows are not triggered
by a V2 branch push. Workflow permissions are `contents: read`.
No production secrets, model calls, webhooks, database mutations, source
registry promotions, or deployment are used.

## Runner acceptance

1. Installed-dependency offline regression: V2, English legacy, Arabic legacy.
2. Four bounded, configured publisher-owned RSS feeds (two English, two Arabic):
   pinned resolved public IP, hostname-verified TLS, no off-origin redirects,
   9-second timeout, 1-MB limit, at most one request per feed with normal
   same-host redirects. Raw source bodies remain ephemeral in runner memory.
3. B33 receipt plus B26 feedparser and B31 unchanged-V1 parser comparison
   on identical observed bytes; only counts/hashes/transport metadata are
   uploaded as a public GitHub artifact. Source signatures, per-article rights,
   native content verification and end-to-end editorial/delivery acceptance
   are **not** claimed by successful RSS parsing.
4. Real Playwright Chromium execution of B32 synthetic EN/AR page fixtures at
   320, 390, 768 and 1320 px; network aborted; synthetic screenshots and
   browser metrics artifact only. Emulation is not physical-phone QA.
5. No hidden retry loop. If a source fails, record one classified result and
   leave the language-specific live-source checkpoint HOLD unless at least
   one configured feed of that language succeeds.

## Initial status

**Workflow staged for one qualifying branch push. Runner results pending.**
The eight-checkpoint evidence bar remains **4/8** pending independent outcome
review: the other four checkpoints are real-source HTTPS capture, browser QA,
genuine same-slot full V1/V2 editorial/delivery comparison, and separately
authorized canary/rollback acceptance.

After observing the run, append exact run URL, job statuses, sanitized artifact
receipts, parser drift, browser metrics, and revised gate dispositions.
This record must not be treated as a pre-emptive PASS.
