# B63 — Fail-closed native page geometry evidence

Date: 28 October 2026 (UAE). Development branch only.

## Observed regression (RED)

The B60 synthetic metadata checker accepted a five-page manifest whose 64-character
image digests were non-hex and whose text coordinates were `NaN`. Its result reported
zero geometry violations even though the evidence was malformed. It also accepted
an entirely empty text-box list on a page. The four new B63 unittest cases first
failed with 18 assertion failures across malformed variants.

## B63 correction (GREEN)

`v2_b60_original_edition_qa.inspect_layout_geometry` now rejects non-finite
numeric geometry, requires exact 64-character lowercase hex SHA-256 syntax, and
refuses pages with no text boxes. The existing 4K clipping and font-size checks
remain in force. No image-byte hash matching or independent visual review has
been added: this is still **metadata-only technical lint**.

Local focused checks: B63 **4/4 PASS**; existing B59–B62 **12/12 PASS**;
`git diff --check` passed. After installing missing test dependencies in a
temporary directory, the complete offline suites passed **711/711 V2**,
**153/153 English legacy**, and **55/55 Arabic legacy**, with no model or
Discord credentials available to the test processes. The isolated B59–B63
no-post workflow is prepared to repeat this on development-branch publication;
no hosted pass is claimed.

## Holds and boundaries

- The five original V1 editorial/visual defects are unresolved by this metadata fix.
- B62's nine material pre-canary technical blockers remain open, including genuine
  source-matched V2 editorial visual inspection and independent Discord receipts.
- Release state remains **HOLD**, with no B50/B51 canary.
- No production `main`, sources, model configuration, schedules, secrets, database,
  webhooks, Discord delivery, or paid-provider calls were changed.
