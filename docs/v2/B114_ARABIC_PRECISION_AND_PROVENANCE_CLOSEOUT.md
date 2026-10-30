# B114 — Arabic classification precision and capture provenance closeout

**Scope:** isolated `rebuild/aggregateit-v2` only. No production/main changes, Discord publication, model API calls, or paid resources.

## Root cause and repair
1. The article-evidence gate and Arabic newsroom previously used separate keyword classification policies. Valid source-backed security and diplomatic news could pass one and fail the other. B114 introduces `v2_b114_arabic_topic_policy.py`, used consistently by `v2_article_body_gate.classify_geography` and `v2_event_intelligence.arabic_filter`. Collector prechecks and editorial compile explicitly pass the same headline and bounded article lead to the policy. The source-country evidence gate and routine exclusions remain.
2. Arabic prefixes and common inflections were poorly handled by exact boundary matches. B114 uses bounded normalized Arabic roots and explicit lexical cue classes, retaining conservative geographic identification and rejection of mundane service/cultural headlines. Root patterns are intentionally bounded; not an LLM truth-verification system.
3. Multiple GitHub runs of one UTC date must not be counted as multiple days of historical evidence. `v2_b114_capture_provenance.py` reports capture run slots, independent dates, and differing run captures separately, without choosing conflicting snapshots or altering strict B95 historical acceptance.

## Real CI and source observations
- **CI:** run [41013654372](https://github.com/4mghonly/AggregateIT/actions/runs/41013654372), commit `c0b703a072a8061ae0d5bd6e93785b3164530195`, **SUCCESS**. Focused B114 Arabic positive/negative controls, article-body and prior regressions passed. Artifact `12958279594` (`aggregateit-v2-b80-b83-real-acceptance`).
- **Arabic:** 2 selected stories, both from original Al Jazeera source; Iran and Iraq represented. 6 article HTTP responses, 2 eligible; rejections: 2 editorial not-security-relevant, 1 missing article body container, 1 without grounded country. No fallback was needed for this capture.
- **English:** 3 selected stories, regions Palestine/Israel and Turkey.
- **Held visual products:** 5 full-resolution 3840×2160 images (3 Arabic, 2 English). Objective nonblank/banner checks passed; independent Arabic RTL, clipping and readability review **not** verified.
- **Held shadow:** 2 Arabic and 3 English stories; only parser/headline parity is verified. Independent live and shadow acquisitions were **not** a single immutable captured input, despite equal story counts.
- **Historical provenance:** 6 restored run-specific receipts spanning **2** distinct UTC dates (28–29 October 2026). Repeated runs on the same date do not satisfy the missing five days. A locally produced current-day receipt is not an independently authenticated historical run. Seven-day parity remains unverified.

## Assessment and remaining gates
This single live run demonstrates a **source-backed Arabic yield recovery** (prior B113 run: 0; B114 run: 2), but inputs changed over time, so the size of the improvement is not a same-input causal benchmark. Topic accuracy is supported by bounded positive and negative test cases, **not independently verified real-world labels**.

The following still prevent release:
- Real V1 and V2 **full editorial processing** compared on identical immutable source-byte inputs, not simply equal story counts.
- Seven date-specific bilingual comparison receipts (14 product-date rows), with authenticated V1 baseline and provenance.
- Independent provider fallback and secondary publisher coverage, if primary publisher fails on a future capture.
- Live model translation/primary-fallback exercise with approved credentials and bounded zero-cost controls.
- Human-readable RTL, clipping and native-product review, plus independent publication-receipt comparison and release authorization.

**Disposition:** B114 targeted implementation/CI complete; **release HOLD**. Next engineering task: one-pass same-capture bilingual source/HTML evidence to both shadow and editorial gates, followed by properly dated receipt collection. Do not fabricate history or lower release requirements.
