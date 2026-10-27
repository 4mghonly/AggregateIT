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

## Initial hosted live validation — PASS

[GitHub Actions #40465567248](https://github.com/4mghonly/AggregateIT/actions/runs/40465567248): **8/8 focused tests passed**. The unchanged actual production validator `arabic_source_audit.probe` and RSS collector succeeded on **4/4 candidates** (10 entries each). Recent 72h collector items: Shabelle **10**, Puntland Post **10**, Somali Dispatch **4**, Goobjoog English **10**. Language classifier `langdetect` classified Somali/Somali/English/English, consistent with declarations but not publisher-authenticated.

Among **34 recent stories**, the existing deduplication key plus 0.94 near-title threshold found **0 same-link or near-identical duplicate pairs**. Semantically equivalent paraphrases and cross-language duplicate reporting are not detectable by this test.

The actual production translator normalizer passed controlled Arabic-output/number-preservation/rejection tests. No model call was made. Two new focused tests also exercise the actual production primary-to-fallback control flow under simulated primary failure, and fail-closed behavior when both routes fail. This does **not** validate live primary/fallback connectivity or real English/Somali→Arabic semantic translation quality.

Initial sanitized measurement artifact `12716750335` (3-day retention). New source registration/enablement remains disabled, production unchanged.

## Final hosted acceptance — verified

[Run #40465932734](https://github.com/4mghonly/AggregateIT/actions/runs/40465932734) completed **SUCCESS** on commit `a25ad0244bec7e6bb78c9c1fc43984f3d4ea4efe`. Focused **10/10 PASS**, full V2 **578/578 PASS**, English legacy **153/153 PASS**, Arabic legacy **55/55 PASS**. The second live measurement again confirmed all four sources compatible with the unchanged production `arabic_source_audit.probe` and real `arabic_newsletter.collect.collect_source`.

Measured 72h item counts again: Shabelle 10, Puntland Post 10, Somali Dispatch 4, Goobjoog English 10. `langdetect` heuristic classified Shabelle/Puntland `so`, Somali Dispatch/Goobjoog English `en`; no candidate metadata mismatch detected. Cross-source and within-source lexical duplication **0 pairs / 34 recent articles**. The production translator normalizer contracts and simulated primary failure → fallback successful result and both routes failure→no fabricated Arabic behavior passed (no live LLM credentials used).

Sanitized artifact ID `12716696263` (3 days). Earlier run artifact `12716750335` also records the initial 8-test pass.

### Recommendation and explicit holds

All four can be **recommended for staging** on the isolated V2 branch as disabled candidates. Two have Somali-language headlines, and two English; either requires confirmed real translation before a fully Arabic product can be approved. No actual live Arabic translation, semantic duplicate resolution, publisher factual verification, model fallback connectivity or Discord delivery was completed. The B41 production Somalia source minimum is *not* closed because no production registry was changed or re-audited.

Suggested rollout (separately authorized after translation acceptance): Shabelle + Somali Dispatch first to maximize language diversity, Puntland Post as additional geographically relevant outlet, and Goobjoog English as replacement for its currently failing Somali feed, keeping one logical publisher-family identity. Validate final editorial relevance and actual LLM translation quality before enabling, then run the complete production source audit and confirm 2+ distinct compatible Somalia publishers.

Production estimated readiness **60%**, formal evidence gates **6/8** remain unchanged.
