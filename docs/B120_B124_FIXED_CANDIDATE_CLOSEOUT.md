# AggregateIT V2 B120–B124 engineering closeout — no release authority

**Target:** rebuild/aggregateit-v2 only. **Main and production:** unchanged.
**Position:** B115 has seven real bilingual-positive dates on changing commits.
One fresh seven-day window on a single final tested SHA is required; no backfill.

## B120: Future authentic weekly source evidence

The no-post B46 runner now creates b120_daily_source_roster.json during a
genuine GitHub Action with full B115 same-capture evidence.
Only original-language source links, source identity hashes, event IDs,
priorities, geography, and per-product story counts are persisted.
No captured publisher article, original headline or original quote is stored.

v2_b120_weekly_source_roster.seven_day_roster validates seven distinct UTC
days, exact same candidate SHA, each language positive, and GitHub Actions
metadata (run ID, workflow, branch, status, timestamps) supplied independently
from an authenticated GitHub API. It quarantines duplicate dates rather than
cherry-picking one. Only then can render_source_roster_html produce a
source-linked, nonanalytic, nonpublishable weekly HTML roster. Original
weekly analytical English/Arabic publications and PDFs remain unverified;
do not substitute the roster for model/editorial acceptance.

Run offline after downloading real artifacts and GitHub API run metadata:
python -B v2_b120_weekly_source_roster.py --roster-dir b120-history
 --github-runs-json b120-authenticated-runs.json --candidate-sha SHA
 --as-of YYYY-MM-DD. This never invents dates or sends Discord messages.

## B121: Conflicting B95 history preservation

v2_b121_history_quarantine.py records each B95 receipt variant, source run
ID hints and distinct conflicting SHA values. Different same-day SHA values
stay quarantined. The observed 30 October 2026 B95 legacy sample has two
distinct evidence hashes even though both have 3 English + 3 Arabic stories.
The absence of a conflict from a smaller restored subset is not
historical resolution. Original receipts are not rewritten or deleted.
B121 never authenticates a GitHub run itself; it never grants release.

## B122: Delivery / rollback dry-run

The V1 production schedule and route files are read-only and validated
against the non-sending V2 routes. Local durable receipt stores prove
ambiguous-send state survives restart, blind retry is refused and cross-channel
destinations fail closed. A local rehearsal is not Discord receipt parity,
a production rollback, or an authorization to post. Do not inject webhooks
into this no-post workflow.

## B123: Rights and provenance inventory

v2_b123_publisher_rights_inventory.py enumerates native-language
publisher identities in the V2 live source catalog and sets
UNVERIFIED for source redistribution rights, licence evidence and independent
factual corroboration. A working RSS feed is never a republication license.
Owner-approved publisher-by-publisher documentation is required before
any production publication.

## B124: Human editorial adjudication

b124_editorial_review_queue.json contains URLs and SHA-256 identities
for V1-only and V2-only article decisions, plus V2 rejection reason and rank.
There is no publisher headline or article body. Separate analyst reviews
must label material omissions and record substantiated rationale. The
operator must investigate V1-only geography, body extraction, relevance
and budget differences; never weaken guards simply to inflate selection overlap.

## Full regression suite

The complete local suite (python -m unittest discover -s tests -q)
passed 940 tests after restoring the missing open-source langdetect
dependency and correcting two outdated tests:
- B46 previous 20-article assertion updated to the 64-article B115 capacity.
- Arabic rendering test now checks the full exact publisher quote in
  summary_ar and a shorter verbatim prefix in title_ar; source text
  remains unaltered.

The whole suite is not the same as independent V1/V2 model/visual/delivery parity.
A completed GitHub Action on the final commit is required for CI proof.

## Remaining mandatory gates and owner decision

1. Seven consecutive future real UTC bilingual-positive capture dates on
   one final immutable candidate SHA; one run per UTC day unless failure
   requires a documented retry; never backfill.
2. Seven-day English/Arabic analytical weekly documents from authentic,
   rights-cleared source evidence; model insight and translation evaluated
   independently. B120 is not a replacement for this content.
3. Human review of source-linked disagreements in B124 and independent
   factual corroboration, especially missing Arabic body/geography cases.
4. Full actual V1/V2 model, translation and fallback acceptance on identical
   frozen inputs and authenticated previous history, subject to explicit
   model credentials, agreed spend ceiling and reviewer criteria.
5. Same-slot V1/V2 visual, RTL, clipping, readability and charts review
   using original V1 reference images and complete V2 pages.
6. Live authenticated delivery receipts and real rollback cutover rehearsal
   only in an explicitly separately approved release setting. Mock testing
   alone (B122) cannot authorize posting.
7. Full B95 provenance and old variant resolution by original-run evidence
   rather than a favourable sample; B115 counts remain independent.
8. Verified publisher licences/republication permissions and factuality.
9. Owner's explicit final release/cutover approval.

**Release decision: HOLD.** Never mutate main/production or post Discord
to manufacture compliance with any missing gate.
