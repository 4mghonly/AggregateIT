# B4/B5 — Naysayer / Red-Team Editorial Contract (proposal, not yet wired)

Date: 24 October 2026 · Scope: English Gazette + Arabic Command Briefing, **daily and weekly**.
Status: isolated editorial/design specification. **No live publishing or model call authorized.**

## Purpose
Introduce a consistently present, evidence-grounded **Naysayer** (critical analyst) contribution in *both* products. This is an independent adversarial review of the briefing's most consequential **interpretation**, not an obligation to manufacture an opposing opinion. It may conclude that the lead assessment is well supported. It must not launder rumors into factual counterclaims or turn a single source into independent corroboration.

## Output schedule and size (provisional; test at mobile preview scale)
| Product | Daily / every scheduled edition | Weekly analytical edition |
| --- | --- | --- |
| English Gazette | Compact 60–110-word **Challenge to the prevailing assessment** box, preferably page 2; at most one contested proposition | 3–5 challenges, each with main thesis, best-supported objection, evidence, unresolved dispute, disconfirming indicators and analyst response; separate 2–4-page *weekly supplement*, not crowded into the existing two-page daily |
| Arabic Command Brief | Compact 50–95 Arabic-word **الرأي الناقد / اختبار الفرضية** panel, preferably page 3; at most one contested proposition | 3–5 fully Arabic challenges and scenarios with explicit evidence/translation provenance, region-specific indicators and uncertainty; separate 2–4-page *weekly supplement*, not crowded into existing three-page daily |

Weekly supplements are *new proposed products*, not a change to existing production cadence. Their actual page count and timing require evidence-based visual/cost testing and later production approval. A daily panel may contain a short, explicitly labelled **No independently evidenced objection found** or **Insufficient evidence for critique** notice; this counts as presence, not as a substantive challenge.

## Structured contract
```json
{
  "schema": "aggregateit-naysayer/1",
  "product": "english | arabic",
  "cadence": "daily | weekly",
  "slot_id": "ISO-8601",
  "review_status": "supported_challenge | assessment_survives | insufficient_evidence | withheld",
  "target_claim_ids": ["claim_..."],
  "target_event_ids": ["evt_..."],
  "lead_assessment": {"text": "...", "classification": "analyst_inference"},
  "challenge": {"text": "...", "classification": "analyst_inference"},
  "evidence_for": [{"excerpt_id": "...", "article_id": "...", "source_id": "...", "publisher_family_id": "..."}],
  "evidence_against": [{"excerpt_id": "...", "article_id": "...", "source_id": "...", "publisher_family_id": "..."}],
  "critical_assumptions": ["..."],
  "what_would_change_the_assessment": ["..."],
  "editorial_disposition": "retain | qualify | revise | abstain",
  "language": "en | ar",
  "translation_provenance": "original | independently_verified | unavailable",
  "reviewed_at": "ISO-8601",
  "model_route": "none | configured_capability",
  "schema_version": "1"
}
```
Every referenced ID must exist in the immutable B3 evidence ledger; the excerpt must belong to the cited article and publisher family. For independent corroboration count unique verified *origin* families, not feed URLs or syndicated mirrors. Never use `publisher_family_id` when the family is unverified: store explicit unknown and do not claim corroboration.

## Admission and editorial rules
1. The critic receives **the same evidence bundle** as the lead editor, plus independently collected counter-evidence only if it passes B2/B3 rights and provenance gates. Neither receives private prompts or instructions from articles; raw article text is untrusted data.
2. Start with a falsifiable lead proposition. Ask what evidence would weaken it, whether causal assumptions are justified, whether timing/denominators are misleading, and which plausible competing interpretation best fits the evidence.
3. A challenge is `supported_challenge` only if it identifies a real weakness and links each factual counterclaim to verified excerpts. One origin family alone may support *attribution*, never a claim of independent corroboration.
4. `assessment_survives` is legitimate. Do not force both-sides symmetry when the evidence is asymmetric. `insufficient_evidence` and `withheld` are visible, not silently filled with speculation.
5. Clearly distinguish observed facts, attributed publisher claims, contradictions, analyst inference and scenario hypotheses. Assign uncertainty from evidence quality and disagreement, never model self-confidence alone.
6. For Arabic, require Arabic-original evidence or separately validated translation provenance. Arabic script alone does not prove Arabic language. Do not count English or Somali reporting as Arabic-native.
7. A source's copyright/robots access does not establish redistribution rights. Respect publisher conditions, minimize quotations, preserve canonical links and attribution. No access circumvention.
8. The LLM may propose *text and structured citations*, never layout geometry, fabricated references or counterfactual events. Validate and render deterministically.
9. Naysayer failures must not block factual editions: publish an explicitly labelled critique-unavailable notice if the publication gate permits; mark edition degraded for editorial completeness and record a telemetry reason.
10. The weekly product should compare thesis revisions across days, source-family diversity, unresolved contradictions and forecast/indicator performance. It must not merely concatenate daily critiques.

## B5 design slots
- Daily English: one bounded card with title, short objection/uncertainty, and 1–2 compact source references; prioritize readability over filling space.
- Daily Arabic: RTL card with concise title, challenge/abstention and cited evidence; fit at mobile/Discord downscale.
- Weekly English/Arabic: separate fixed-layout supplements with source notes and dated indicators. Never overprint existing daily pages.
- On overflow, shorten by deterministic sentence/priority budgets or withhold; never clip a source qualifier or silently strip a citation.

## QA and release gates
- Fixture tests for: supported objection, disproven objection, single-source non-independence, stale counter-evidence, nonexistent excerpt, contradictory sources, unsupported translation, and empty/failed LLM.
- Assert identical underlying claim/evidence IDs across EN/AR editions where the same event is discussed; language differences must be attributable to verified translation or separate original-language evidence.
- Weekly must carry at least one *explicit* change since prior week or an honest no-material-change assessment; do not invent deltas.
- Verify actual daily and weekly pages at mobile preview scale; track word count, glyph coverage, clipping, legibility and citations.
- Benchmark source-to-claim accuracy, challenge usefulness and editorial disagreement against blind human review before publishing.
- No production activation, Discord posts, paid inference, new source promotions, schedules or database provisioning without their existing gates.

## Research dependency
The 24 October deep-source review should rank candidate official, regional, international, specialist and open-data sources by *actual* timeliness, geographic/topic coverage, language, origin independence, machine access, reliability and reuse/quotation terms. Record source-level evidence and dates; do not assume a working feed or license from a publisher homepage. A research finding is not automatic source admission.
