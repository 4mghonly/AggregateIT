# AggregateIT V2 — A9 live-to-native integration, regional source probes and B7 shadow readiness
Date: **24 October 2026**, UAE. Development branch: `rebuild/aggregateit-v2`.

## A9 — The former single-runtime blocker is CLOSED
We copied 24 **exact GitHub V2 branch source modules** (including the unmodified existing English and Arabic renderers) to a temporary, isolated, network-capable Python execution environment. Only public article GETs were used. Pillow 11.3, Matplotlib 3.10.7 and required existing font/layout dependencies were made available in that environment. Pillow RAQM was verified.

At **2026-10-24T09:49:47Z**, one invocation of `v2_a8_single_run.run_no_post_chain(network_opt_in=True)`:
1. Performed actual HTTPS retrieval of a BBC English and Al Jazeera Arabic Jordan news article;
2. Extracted bounded full HTML article bodies and deterministic Jordan/security cues from headline and body;
3. Created two immutable B3 article revisions, two literal excerpt offsets, two attributed claims and two explicit event records;
4. Prepared one held B4 English and one held Arabic editorial candidate; and
5. Called the **REAL** native English and Arabic renderers in the **SAME PROCESS**, producing two EN and three AR 3840×2160 PNG files, with per-file SHA-256 verified, in **4.07 seconds**. **NO test double** was used in this live A9 run.

The machine-verifiable compact manifest (including 5 PNG hashes and two exact source body hashes) is in `fixtures/v2/a9_true_live_to_native_receipt_2026-10-24.json`.

**Limitations:** The files were produced in the remote temporary execution workspace; only hashes and metadata are committed to GitHub, **NOT the binary PNGs**. One English and one Arabic observed article do not constitute real regional coverage, multi-source corroboration, or a complete newsletter. Both reports concerned the Jordan church shooting, with differing casualty figures: no attribution was upgraded to confirmed truth, and no figures were reconciled by inference. The render has many empty panels because the experimental editions lack corroborated market, social or regional stories. PDF/PNG formatting is technically functional, but final mobile readability and editorial quality are not accepted.

## Additional regional source compatibility probes
Twelve registered URLs were directly fetched over HTTPS and inspected with a hard 200,000-byte RSS/Atom parsing budget, at **2026-10-24 09:51 UTC**.

| Registered source and region | Result | Notes |
|---|---|---|
| IRNA — Iran | HTTP200, RSS parse | 30 dated/recent; **Persian**, not native Arabic |
| Dabanga — Sudan | HTTP200, RSS parse | 12 recent, Arabic |
| Radio Ergo — Somalia | HTTP200, RSS parse | 10 dated, 2 recent, **Somali**, not native Arabic |
| Jerusalem Post — Palestine/Israel | HTTP200, RSS parse | 30 recent, English |
| Abu Dhabi Media Office Arabic crown-prince | HTTP200, RSS parse | 24 dated, 5 recent, Arabic |
| The National (correct RSS URL) — GCC | HTTP200 XML but over 200 KB | Must profile bounded parsing; NOT declared dead |
| Shafaq — Iraq | HTTP200 redirected RSS but over 200 KB | Needs bounded, redirect-safe integration |
| Dawn — Pakistan | HTTP200 XML but over 200 KB | Needs bounded parsing |
| Yemenat — Yemen | HTTP200 RSS but over 200 KB | Needs bounded parsing |
| Pajhwok — Afghanistan | HTTP410 | Current endpoint unavailable; find verified official replacement |
| Addis Standard — Horn of Africa | HTTP403 | Environment-specific access blockage; do not assume publisher outage |
| WAM Arabic site homepage — GCC | HTTP200 **HTML** | This entrypoint is not an RSS URL; needs a verified feed or HTML adapter |

The first A4 source probe had 10/12 parseable RSS/RDF sources, nine dated within 72h. **These are not counts of independently operated newsrooms or fully working commercial collectors.** All rights for source copying, redistribution, commercial analysis and sublicensing remain unreviewed. A registered `stream=arabic` is NOT evidence that `original_language=ar`; it can be `fa`, `so` or `en`. No unapproved translation was invoked.

## B7 shadow readiness — truthful STOP state
The existing `v2_shadow_scorecard.py` can compare **genuinely measured, same-product and same-time-window** run manifests. A current authenticated V1 and V2 simultaneous baseline **was not available**; it would be false to claim numerical V2 editorial superiority.

New `v2_a9_shadow_readiness.py` and `tests/test_v2_a9_shadow_readiness.py` force **non-comparable** when V1 data is missing, V2 data is missing, windows/products differ, revisions are identical, or metrics lack independently handled attestation. They never authorize delivery. The two booleans are merely caller assertions and **not cryptographic verification**. Tests: **7/7 PASSED**, via TDD (RED missing implementation → GREEN).

## Technical QA and no-go boundaries
- Exact live-to-native implementation run: **passed**, actual 5 PNGs and hashes.
- Native one-run controlled fixture tests: **9/9 PASSED** locally on an earlier checked-out V2 snapshot.
- New shadow admission tests: **7/7 PASSED** locally.
- A full earlier-snapshot unittest run was attempted in this session but **timed out**. It cannot be represented as a full current remote-branch regression pass. Prior full historical tests remain separate evidence, not new A9 acceptance.
- No GitHub Actions, protected main modification, paid model inference, secret use, OpenHands, data-store write, schedule change or Discord message send.
- DNS public-address preflight is defense in depth, NOT DNS-rebinding-proof; a production network egress allowlist and IP-pinned transport are still required before arbitrary third-party URLs can be accepted.

## Next acceptance sequence
1. Improve large XML source handling safely, preserve feed-family and language metadata; fix invalid HTML-only RSS entrypoints. Distinguish HTTP blocked, stale, over budget, and parseable.
2. Grow genuine source coverage across all intended regions; benchmark body extraction templates and independent publisher families. Defer translating non-Arabic sources until approved model route required.
3. Produce full, balanced editorial editions; independent evidence corroboration and licensing; assess 4K mobile legibility and final styling. **Do not promote source claims to verified.**
4. Collect actual same-window V1 and V2 no-post quality manifests from authorized environments, then run the shadow comparator. Only an explicit later owner-approved release may change production.

**Checkpoint status:** A9 technical single-process native integration **PASS**. Broader regional coverage **PARTIAL**. Full V1/V2 shadow comparison **BLOCKED by missing genuine matched V1/V2 run metrics**. Configured LLM remains **DEFERRED** as directed.
