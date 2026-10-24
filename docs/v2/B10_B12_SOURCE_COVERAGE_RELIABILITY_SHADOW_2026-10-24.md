# AggregateIT V2 — B10–B12 source, language, compatibility, and shadow batch

**Date:** 24 October 2026 (UAE) · **Branch:** `rebuild/aggregateit-v2` · **Production main:** read-only.

## 1. Source-size diagnosis and corrected implementation

Fresh read-only HTTPS retrieval found that four supposedly incompatible RSS feeds are actually parseable; they exceeded the original 200 KB source-probe cap:

| Source | Bytes seen | Entries | Original language | Result after fix |
| --- | ---: | ---: | --- | --- |
| The National `ar-s017` | 813,693 | 100 | English | usable; **not** native Arabic |
| Shafaq `ar-s026` | 381,684 | 25 | Arabic | usable after direct HTTPS path fix |
| Dawn `ar-s050` | 346,348 | 26 | English | usable; **not** native Arabic |
| Yemenat `ar-s081` | 224,442 | 50 | Arabic | usable |

Original Shafaq URL `https://shafaq.com/ar?rss=1` redirected first to **HTTP** before returning to HTTPS. The new V2 adapter refused this (correctly). B10 instead uses `https://shafaq.com/rss/ar` directly; live test returned HTTP 200, 25 recent entries. The **immutable historical source registry remains unchanged**, and the approved endpoint correction is explicitly scoped to `v2_large_feed_adapter.py`.

`v2_feed_probe.py` / `v2_feed_items.py`: default cap **200,000 bytes**, optional strictly validated cap at most **1,000,000 bytes**. New `v2_large_feed_adapter.py`: exact-source allowlist, limited redirects, public DNS preflight, no-network default, bounded data, stored SHA-256 metadata, fail-closed XML parsing, safe original-language profile. Only specific pre-profiled sources receive the larger cap; all candidate reports remain `delivery_authorized=False`. This mitigates but does not eliminate DNS rebinding risks; production requires IP-pinned/egress-controlled transport.

**TDD:** `tests/test_v2_b10_large_regional_feeds.py` first failed because the new module did not exist. Shafaq regression first failed against the legacy redirect path; both RED conditions were reproduced. After the repairs, **11/11 B10 focused tests passed**, and all four real large-source probes returned usable dated feeds.

## 2. Regional checks and coverage honesty

During this batch: six B10 profile-based source checks, twelve additional region-focused URLs, and eight Somalia alternatives were examined over real read-only HTTPS. Of the extra regional checks, Oman Observer (EN), TRT Haber (Turkish), Ammon News (EN) and Shabait (EN) returned parseable fresh feeds. The eight other selected regional endpoints returned **HTTP 403** to this runner. This is a runner-specific result, **not proof of site outage**.

Somalia alternatives probed:
- Shabelle Media: 10 dated/recent RSS entries, English.
- Somali Guardian: 10 dated RSS entries, four in 72h, English.
- Somali Dispatch: 10 dated RSS entries, one in 72h, English.
- SONNA Arabic and generic URLs returned HTML rather than valid feed payload; Goobjoog/Hiiraan 404, Garowe proposed feed URL 500.

These three credible **technical feed candidates are not yet registered, independently vetted, rights-cleared, or native Arabic**. They do **not automatically close the production Arabic Somalia requirement**.

`fixtures/v2/b10_b11_live_source_receipts_2026-10-24.json` records 21 distinct *registered* read-only observations across this batch plus prior A9 sample sources, and three **separately classified unregistered** Somalia alternatives. 13/21 registered observations were usable dated feeds. Their distribution spans **12 of 17 target regions**, while only **four regions** (GCC, Iraq, Sudan and Yemen) have any *native-Arabic language candidate*. These counts are **source reachability**, not evidence of full topical reporting or independent regional news coverage.

New `v2_b11_coverage_readiness.py` and `tests/test_v2_b11_coverage_readiness.py` explicitly refuse to infer:
- verified publisher independence from different URLs/hosts;
- native Arabic from a source merely assigned to the Arabic stream (Persian, Somali, English and Turkish require language-aware handling);
- editorial topic/geography from feed reachability;
- actual release readiness without rights, source body, corroboration and end-to-end QA.

**B11 focused tests: 8/8 passed** after a demonstrated missing-module RED test.

## 3. Python dependency repair

The V2 remote environment installed the latest runtime libraries, but the legacy `tests.py` failed importing `trafilatura` because modern `lxml` loads `lxml.html.clean` from the separate package `lxml_html_clean`. The regression test `tests/test_v2_b12_dependency_compatibility.py` reproduced that ImportError (RED).

`requirements.txt` on **V2 development branch only** now explicitly includes `lxml_html_clean>=0.4,<1.0`. After installation, the import test passed and **legacy tests: 153/153 passed**.

## 4. Full current-branch verification

A fresh, pinned *public GitHub commit archive*, not the user's older ZIP, was fetched **read-only** for commit `abc02430db9399d0be5b88a9e8642b8278259a1c`. Its ZIP SHA-256 was `6e110433d3518e21f5e6d308d4dac2841570d30768a244512e1e079d3f3805ff` (252 archive entries). The complete 51-module unittest suite executed in an isolated Python process with outbound network sockets blocked and model/Discord secrets absent:

- `python -B -m unittest discover -s tests -p 'test_*.py' -q`: **420 tests passed** (11.864 seconds).
- `python -B tests.py`: **153 tests passed**.
- Neither suite started CI or sent Discord/LLM requests.

The **static source-compatibility evidence fixture** was committed immediately afterwards; no behavior-changing code was modified after this pinned test run.

## 5. Read-only inspection of actual production workflows

Existing GitHub Actions runs (read-only; **none started**):
- [Source Health Audit 40077911411](https://github.com/4mghonly/AggregateIT/actions/runs/40077911411): failed because workflow installed `feedparser`/`aiohttp` but missed `requests`. Requires workflow dependency repair on production only when separately authorized; not an API-key or source outage.
- [Arabic Source Audit 40067986572](https://github.com/4mghonly/AggregateIT/actions/runs/40067986572): failed floor assertion `{'somalia':1}`; the audit committed `SOURCE_AUDIT.json` to main, independently of our V2 work.
- [Arabic Briefing 40076664942](https://github.com/4mghonly/AggregateIT/actions/runs/40076664942): workflow success and **one confirmed Discord message**, but multiple primary translation validation failures and fallback HTTP 403. Degraded output remains a meaningful production-quality concern.
- [English News Engine 40084841968](https://github.com/4mghonly/AggregateIT/actions/runs/40084841968): workflow success, 153/153 embedded tests; run environment logged `ENGINE_DELIVERY: false`, so do not claim it delivered a newsletter.

These existing workflows are not proof of V1 editorial correctness or of V2 quality improvement. **Production main and existing workflow files have not been touched**.

## 6. V1/V2 comparison disposition

V2 A9 proved a genuine two-article BBC/Al Jazeera → full-body evidence → native five-PNG **no-post** run. But this is not comparable with a complete V1 newsletter in a matched time-window and format; source counts, topics, market analysis, translation and receipt collection differ. The existing `v2_a9_shadow_readiness.py` remains **HOLD**. Do not invent improvement scores or substitute missing source counts with zero.

## 7. Next acceptance gates

1. Extend full-body collection to rights-reviewed sources across more regions, with remote egress restrictions and feed-family deduplication; test true native Arabic intake and explicit translated-source labels separately.
2. Fix production audit workflow dependencies only on approved release; qualify a genuinely usable **second Somalia provider** (and its native-language/translation handling) before changing production floor status.
3. Resolve Arabic primary/fallback translator failures only when model execution is re-authorized; until then treat degradation as an observed risk and retain evidence-only fallback.
4. Complete balanced multi-region editions and mobile-sized screenshot QA; then gather authentic same-window V1/V2 run logs to score.
5. Separate owner approval required before any webhook publication, schedule or protected main changes.

**Status:** B10 implementation + RSS live compatibility **PASS** for profiled sources; B11 regional audit/gates **PARTIAL**; B12 reproducibility **PASS**; production remediation **PENDING**; shadow comparison **HOLD**. No paid model calls, production writes, database provisioning, GitHub Actions reruns or OpenHands.
