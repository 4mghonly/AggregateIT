# AggregateIT V2 — A7 real article-body and no-post native rehearsal

Date: 24 October 2026 UAE. Isolated development branch `rebuild/aggregateit-v2`; production/main, schedules, CI, Discord and model secrets untouched; no OpenHands.

## Actual public source acquisition
A separate network-enabled Python runner fetched full HTML within an 850KB hard cap from:
- BBC [Jordan church funeral report](https://www.bbc.co.uk/news/articles/ck87zlpzny15o), BBC RSS publication 2026-10-23 19:46:30 UTC: HTTP 200; 402,791 HTML bytes; 34 article paragraphs and 4,310 body characters. Body SHA-256 `e634bb168348475d6c1b04e987a3cde15305084970623a82b30e020cc29e118f`.
- Al Jazeera Arabic [Jordan Karak report](https://www.aljazeera.net/news/2026/10/24/%d8%a7%d8%b1%d8%aa%d9%81%d8%a7%d8%b9-%d9%82%d8%aa%d9%84%d9%89-%d9%83%d9%86%d9%8a%d8%b3%d8%a9-%d8%a7%d9%84%d9%83%d8%b1%d9%83-%d8%a5%d9%84%d9%89-8-%d9%88%d9%88%d8%a7%d8%b4%d9%86%d8%b7%d9%86), RSS publication 2026-10-24 07:49:59 +03:00: HTTP 200; 557,684 HTML bytes; 9 article paragraphs and 1,742 body characters. Body SHA-256 `a5ff3557bceb553446500b65f9845d9526921ec13f01cc450a6e75b0212280e4`.

## Actual full-body chain verified
The exact GitHub branch versions of `v2_article_body_gate.py`, `v2_evidence.py`, `v2_evidence_ledger.py`, `v2_editorial.py`, `v2_script_guard.py` and `v2_product_compiler.py` were executed in the networked temporary runner. Unlike the earlier RSS headline-only test, **entire extracted article bodies** were input into `make_article.original_text`. The renderer text-span offsets and immutable excerpts were traced back to the actual in-memory source revision.

Outcome: 2 in-memory full-body articles, 2 immutable source revisions, 2 exact quotes/excerpts, 2 claims, 2 explicit events; 1 English and 1 Arabic **nonpublishable** editorial candidate. Both showed explicit Jordan in headline **and** body; security category supported by literal headline cues. English market unavailable; Arabic finance excluded, 16 Arabic target regions absent in this small sample. Records and per-source digests saved to `fixtures/v2/a7_full_body_ledger_proof_2026-10-24.json`.

**Not proven:** independent truth of either publisher's casualty figure, legal redistribution rights, source-family independence, complete regional coverage, or full deployment/scheduling. The two publishers' reported numbers differ; no automatic reconciliation or false confirmation took place. No model or Discord call.

## Source code and offline 4K rehearsal
New `v2_article_body_gate.py` implements bounded source-specific body anchoring (`article` for BBC; `.wysiwyg--all-content` for Al Jazeera), excludes video boilerplate/script/site chrome, verifies rough original-language script, refuses ungrounded/ambiguous country labels and unsafe quote sizes. `tests/test_v2_article_body_gate.py`: **11/11 passed in the independent remote test runner using exact newly committed GitHub files**.

A separate isolated ChatGPT-local 4K render script, `v2_real_body_no_post.py`, consumed short copied original-language excerpts and remotely reported hashes (not complete local HTML) and generated **2 English PNG + 3 Arabic PNG**, all 3840×2160 and prominently marked `UNVERIFIED | DO NOT PUBLISH`. Its 4 focused local gate tests passed. The source, fixture, 4K PNGs, manifest, and screenshots are packaged in the ChatGPT artifact `AggregateIT_A7_Real_Article_No_Post_2026-10-24.zip`. Full article bytes did **not** enter the local renderer; the exact full-body B3/B4 test was run remotely and is evidenced separately.

The original user ZIP (older checkpoint) plus local fixes/tests ran **325/325 local tests**, including 15 new focused cases; this is **not comparable** to the later 369-current-branch checkpoint, and remote GitHub CI was not triggered.

## Handoff and remaining gates
A7 proof accomplished for **two individual articles**, with real complete HTML → B3 immutable body/excerpt → B4 editorial candidate. Next: route the stricter parser through the durable source collector with enforced network egress restrictions; add publisher templates and rights/syndication review; expand source-grounded region/topic extraction across required coverage without guessing; connect exact-body ledger to the native render/send-gate within **one** no-post runtime; assess 4K readability and then undertake a full V1/V2 shadow comparison. LLM/fallback execution remains **DEFERRED** by owner instruction. No branch cutover.


## A7 final native bridge and regression closure (2026-10-24)
- `v2_native_evidence_render.py` added to the isolated GitHub branch. It accepts only held original-language B4 plans, produces actual English 2-page and Arabic 3-page 3840×2160 PNGs, stamps `UNVERIFIED | DO NOT PUBLISH`, and exposes no live sender, model or collector.
- `tests/test_v2_native_evidence_render.py`: 4/4 PASS locally, including actual five-PNG rendering. The new native module/test bytes were checked against their exact GitHub blob hashes. `v2_article_body_gate.py` and its test ran 11/11 in a separate execution against the **exact branch-fetched files**.
- Source-bound 4K artwork and local reproducibility scripts are in the ChatGPT-generated `AggregateIT_A7_Real_Article_No_Post_2026-10-24.zip`; that archive also contains the local `v2_real_body_no_post.py` recipe (not promoted as a production collector), two source receipts, byte/revision proof and image SHA manifests.
- Complete `tests/` on the isolated user-uploaded older branch ZIP plus the already-shipped lazy `audit.py` import repair and these A7 additions: **329/329 PASS**. Do not conflate this with the **current GitHub branch's** historical 369-test checkpoint; its complete updated suite was not executed and CI was deliberately not triggered.
- Source bodies were genuinely fetched and passed into B3/B4 in a separate remote run, with quote offsets bound to the in-memory full revision. **Native 4K rendering was separately performed from the transferred source excerpts**; one uninterrupted network→full-body→native PNG same-runtime dry-run remains an integration acceptance gate. Zero Discord, database, model, secrets, CI or protected-branch writes.


## Operational main observation (read-only; not caused by this batch)
At closure, GitHub shows production `main` at `745c5b7a32d7da84dadfbcc088b43eb7ce32ed0d`, rather than the earlier `c7a53e9...`. GitHub commit metadata identifies `aggregateit-bot` at **2026-10-24 05:53:19 UTC**, message `Arabic sources: update compatibility audit`, with one changed path `arabic_newsletter/SOURCE_AUDIT.json` and parent `c7a53e9...`. The A7 session only wrote to `rebuild/aggregateit-v2`; **A7 did not cause or modify this main advance**. Treat this as production bot activity, not a V2 migration.
