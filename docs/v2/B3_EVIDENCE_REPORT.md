# AggregateIT V2 — B3 Evidence Core (Isolated Prototype)
Date: 23 October 2026 (UAE)  
State: **PARTIAL — pure in-memory provenance contracts and 34 synthetic regression tests including an append-only in-memory graph; no collector/editorial integration**

## Implemented (`v2_evidence.py`)
1. **Stable article identity** from normalized canonical URL (known tracking parameters removed conservatively). Different snapshots or product collectors pointing to the same canonical URL share article identity; original source observations remain separately identified.
2. **Revision identity** from canonical URL and unmodified original Unicode text. Every observation preserves source ID, retrieved-at time, optional published-at time, original language, exact text, and its SHA-256.
3. **Literal source excerpts** with exact Unicode code-point offsets, revision/source linkage, literal SHA-256 and deterministic ID. A changed source text invalidates the previous revision's excerpt identity; helper methods check article/excerpt integrity.
4. **Attributed claims** require source excerpts and remain `attributed_only`. Analyst inferences are labelled `not_a_reported_fact`. Unattributed `verified_fact` claims are refused.
5. **Events** require an explicit, separately assigned event key. Their identity survives additions of claims; versions reflect claim/status changes. A missing event from a collection is **not** interpreted as closed; explicit closure requires a linked claim.
6. **Translation** stores only `unverified_candidate` output linked to the original article revision; original text and offsets are never rewritten.

## B3b in-memory graph ledger (`v2_evidence_ledger.py`)
- Stores source observations separately from canonical article identity and immutable revisions. Duplicate article observations are counted, but never promoted to corroboration by independent publisher families.
- Enforces stored-revision existence for verbatim excerpts, stored-excerpt existence for claims, and stored-claim existence for event versions. Rejects tampering with source text, excerpt literals, claim statements or observation IDs.
- Uses bounded in-memory observations (default 20,000; caller may lower), idempotent append behavior, and a raw-text-free counters view. No database, archive or telemetry writes.
- Accepts explicit correction/contradiction relations only when both claims were linked to an existing event; marks them `explicit_but_unverified`. It does not infer logical contradiction or factual truth automatically.
- Source ID is now included in excerpt identity so two collectors observing identical article bytes retain separate source provenance. 

## Offline proof
- 19/19 evidence-core and 15/15 graph-ledger standard-library unittest cases passed with synthetic Arabic, English-source identity, emoji code-point offsets, query normalization, revisions, cross-product observation identity, integrity tampering, claim evidence requirements, event changes/closure and translation provenance.
- All 34 actual Python test cases executed in an isolated in-memory Python 3.12 test harness. No model inference, network collection, D1 write or publication.

## Boundaries and unanswered acceptance criteria
- This **does not** prove trustworthy source content, language classification, safe identity clustering or real-world event matching. A caller must supply the explicitly reviewed event key; there is no automatic multilingual merge.
- Hashes protect internal consistency; they do **not** authenticate publishers. A future B3 collector must persist immutable raw article revisions, fetch receipts, publisher provenance and original bytes, then verify excerpts against those stored bytes.
- An in-memory ledger now enforces referential existence and exact source text for excerpts; **durable persistence, transactional integrity, replay/recovery and authenticated publisher provenance** still require storage-linked tests.
- URL canonicalization deliberately avoids guessing about non-tracking query keys; requires production sample evaluation for false merges/splits.
- Contradictions, corrections, multiple publisher families, semantic clustering, cross-language alignment and durable event lifecycle remain open B3 work.
- B2 source live certification is still incomplete. This B3 prototype is isolated and safe to test while B2 remains PARTIAL; it is **not** ready to ingest production evidence.

## Next coherent batch
- Prove deterministic replay/restore and memory bounds, connect diverse real source-grounded fixtures (with rights checked), record cross-language mapping decisions and compare against existing English/Arabic editorial behavior before any storage integration.
