# AggregateIT V2 — B1–B4 installed-runtime and source-rights evidence

Date: **23 October 2026 (UAE)**. Branch `rebuild/aggregateit-v2`, starting SHA `0f252ce0fb3680c2424907f58d5fc7d3879d9438`; unchanged observed main `c7a53e9f6ffa8167c8538b236af6d2bfaddabdf9`.

## Acceptance receipts

| Gate | Observed evidence | Decision |
| --- | --- | --- |
| B1 Python dependencies | Disposable isolated Python 3.12 virtualenv; installed `requirements.txt` and `arabic_newsletter/requirements.txt` (all resolved, no global installs) | INSTALLED |
| B1 V2-focused unit and module integration | `python -B -m unittest discover -s tests -p 'test_*.py' -q`: **162 run, 162 PASS** (5.733 s), no network/Discord/model | PASS — synthetic only |
| B1 inherited Arabic application suite | `python -B -m unittest arabic_newsletter.test_arabic -q`: V2 **55 run, 11 FAIL, 3 ERROR**; unchanged main **same 55, same 11 FAIL + 3 ERROR** | HOLD — 14 pre-existing failures; not V2 regressions demonstrated |
| B3 file-backed recovery | 4 real `/tmp` disposable journal cases: `fsync`, exact receipt replay, torn-tail rejection, complete-tail loss rejected by separately held receipt, durable append after verified replay | PASS at bounded single-process file level; multiwriter/receipt atomicity unresolved |
| B2 bounded feeds | 9 versioned candidates reviewed, three sampled feeds, three robots unavailable, three rights-restricted not directly probed; max 96kB/feed, one attempt/host | PARTIAL — not a corpus- or region-floor acceptance |
| B4 language correctness | Official Ammon English site; Radio Ergo publisher site offers Somali/English sections. Stream membership alone does not prove native Arabic. | HOLD for Arabic-native reuse; validated translation required |

14 inherited Arabic failures are genuine failing checks, not harmless warnings. Their clusters: editorial validation/repair, legacy delivery receipt/retry expectations, source rotation, workflow reference expectation and layout capacity. Product contracts must adjudicate test drift versus actual defects in a separate bounded repair batch. No retry loop was used.

## B2 publisher/rights and capped public probe observations

Probes at **2026-10-23 08:00 UTC comparison anchor**, with HTTP response observed during the 23 October batch. Robots was checked first per host. When robots was unavailable, no content fetch occurred. No source was promoted or disabled and no article body was stored.

| Source ID / publisher | Live technical observation | Rights / language status | Gate |
| --- | --- | --- | --- |
| `ar-s056` Radio Ergo | robots allowed; RSS HTTP 200; XML 88,166 sampled bytes; 10 entries, 3 dated ≤72h | Reuse rights unverified; official publisher offers Somali/English, not demonstrated Arabic-native | TECH PASS, RIGHTS/NATIVE HOLD |
| `ar-s081` Yemenat | robots network unavailable | Rights unverified | UNPROBED |
| `ar-s082` South24 | robots allowed; HTTP 200 `text/html`, 95,008 bytes; 0 RSS entries | Rights unverified; HTML page does not prove dated entries via RSS | HTML, RSS HOLD |
| `ar-s101` Ammon News | robots HTTP error; feed not fetched | Official `en.ammonnews.net` English edition; publisher copyright reserved | UNPROBED, ARABIC-NATIVE HOLD |
| `ar-s070` Petra | robots network unavailable | Rights unverified | UNPROBED |
| `ar-s108` Masrawy | robots allowed; RSS HTTP 200; XML 10,668 bytes; 10 entries, **0 dated ≤72h** | Rights unverified; no freshness floor | FRESHNESS HOLD |
| `ar-s017` The National | intentionally no feed/robots automated request | Publisher terms restrict copying, republishing and redistribution absent express written consent | PERMISSION REQUIRED |
| `ar-s118` Abu Dhabi Media Office | intentionally no feed/robots automated request | Terms prohibit automated content collection and extraction without express permission | PERMISSION REQUIRED |
| `ar-s046` Mada Masr | intentionally no feed/robots automated request | Publisher terms restrict automated access/monitoring and content exploitation without express permission | PERMISSION REQUIRED |

First-party evidence pages:
- The National: https://www.thenationalnews.com/terms-and-conditions/
- Abu Dhabi Media Office: https://www.mediaoffice.abudhabi/en/terms-conditions/
- Mada Masr: https://www.madamasr.com/en/2022/05/16/feature/u/privacy-policy/
- Ammon: https://en.ammonnews.net/
- Radio Ergo language sections: https://radioergo.org/en/ and https://radioergo.org/

These are conservative operational classifications, not legal clearance opinions. Accessibility and robots allowance do **not** confer republication permission. Copyright text or lack of visible terms is not an open license. All sources remain blocked from automatic rights promotion; no publisher-family independence is certified. The 222-source registry and 18-region historical coverage remain exactly as before this batch.

## B3 disk proof and its limit

`tests/test_b3_file_backed_recovery.py` supplies four durable-file cases and disposable synthetic Arabic UTF-8 content. It confirms the existing journal's fail-closed parsing and fsync behavior under normal disposable-file operation. It does **not** prove exclusive multi-process writer locks, crash-atomic independently persisted head receipts, sudden power-loss behavior, database parity or live publisher identity. Do not upgrade B3 to COMPLETE.

## Product and platform boundaries

- English Gazette: 2 pages, English/finance+geopolitics. Arabic briefing: 3 slides, security/geopolitics, UAE-first when verified evidence exists. Routes remain isolated.
- B5 rendered previews previously used DejaVu Sans fallback, while current Arabic production rules declare **Noto Sans Arabic** approved and Siraj Noir staged. Resolve design/owner font decision before claiming production typography pass; no font swap in this batch.
- B6 D1 free-plan quotas and authentication still need evidence and later resource approval. No D1 or PocketBase created, no retention deletion or Drive backup.
- B7 needs lawful, captured, same-window V1/V2 no-post evidence and independent language/quality QA. B8 cutover still expressly blocked.
- All work was free, isolated, no-post; no secret inspection, paid model calls, external publication, Discord/CI dispatch, production workflow edits, database provisioning or deletion.

## Next gated actions

1. Triage 14 inherited Arabic failures against accepted product contracts; fix *only* proven actual defects on V2 with regressions, preserve same-main comparison. Do not repeat identical failing tests while mechanism is unchanged.
2. Acquire permission or use alternative licensed first-party sources. Demand native-language correctness and dated freshness before regional floor claims, especially Somalia/Jordan/UAE.
3. Build no-post application E2E and external receipt/lock contract for B3; follow with release-font and real-density screenshot QA. D1 live/retention and B8 await separate authority.
