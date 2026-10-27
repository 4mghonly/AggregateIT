# AggregateIT V2 — B43 production source validation, Arabic translation and duplication

Date: 27 October 2026
Repository: 4mghonly/AggregateIT
Branch: rebuild/aggregateit-v2

## Objective and exact requirements

Progress four previously discovered Somalia source candidates (Shabelle, Puntland Post, Somali Dispatch, Goobjoog English) using the **unchanged production** arabic_source_audit.probe, then the actual arabic_newsletter.collect.collect_source RSS collector on the captured exact feed bytes, the existing arabic_live_v2 translator _normalize_translations validation rules and _source_is_arabic routing, and the existing _dedupe_key + 0.94 SequenceMatcher threshold.

The actual source-validator function runs with the actual requests transport intercepted only to retain feed bytes in process memory for deterministic collector checks. Exactly one website URL and one feed URL per candidate; the four publishers are processed sequentially. This does not use production credentials, workflows, secrets or database writes.

## Translation evidence boundary

The hosted environment has no connected Arabic translation model API; a controlled fixture is tested against the unchanged real production translation validator: Arabic output acceptance, number mutation rejection, non-Arabic output rejection. The source's actual title language is also screened by langdetect (heuristic; output often uncertain for Somali/English). No machine translation is performed, and semantic fidelity, proper-name preservation, actual model failover and local Somali->Arabic support **are not established** by these tests. Any metadata-language mismatch requires correction and revalidation before promotion. Imported foreign headlines remain unpublishable without working translation.

## Deduplication evidence boundary

Actual collected article headlines are compared using production _dedupe_key plus the current near-identical threshold (>=0.94), with exact normalized URLs and cross-publisher duplicate counts. This test detects exact/near-identical lexical duplicates but not distinct paraphrases in English/Somali nor genuine event/entity merging. Only counts enter artifacts; no publisher text is stored.

## Safety and staging

- Four candidates stay explicitly **disabled** in config/v2/somalia_b43_disabled_candidates.json; no production/main writes, no source promotion.
- Feed and website HTTP response data are examined only transiently in an isolated runner; only sanitized counts, statuses and feed digests retained for 3 days.
- This run does not change schedules, webhook routes, models, LLM budgets or Discord channels.
- Previous B42 run validated candidate technical RSS feeds but did not execute the actual production validator. This run provides a separate qualification pass.
- B41 production Somalia 2-source minimum remains a HOLD until validated replacements are actually integrated, re-audited and translated.

**Hosted B43 run status: PENDING.**
