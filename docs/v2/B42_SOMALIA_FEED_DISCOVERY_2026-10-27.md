# AggregateIT V2 — B42 Somalia feed source discovery

Date: 27 October 2026  
Starting development commit: `7758d4a716bea9d9ba414682e075dde16396e4f8`  
Current production issue: October 27 scheduled Arabic Source Audit requires at least 2 compatible Somalia feeds but found 1 (`s056` Radio Ergo). SONNA Arabic `s057` returned zero entries; Goobjoog `s058` HTTP 404; Hiiraan Online `s094` had no feed.

## Research shortlist

Existing sources revisited: Radio Ergo, SONNA Arabic, Goobjoog Somali.
New publisher candidates: Shabelle Media, Puntland Post, Horseed Media, Somali Dispatch, The Somali Digest, Somali Guardian, Radio Dalsan, Caasimada Online. Alternate URLs: SONNA English, Goobjoog English, Horseed root.

External research found RSS addresses documented by FeedSpot's 2026 Somalia RSS list (Shabelle, SONNA English, Puntland Post, Horseed category feed, Somali Dispatch, Somali Digest). The Goobjoog/SONNA/R. Ergo URLs already appear in the existing system or publisher pages. Unlisted root feeds are guesses to verify, not presumed valid.

## Method

One bounded read-only HTTPS request per feed URL via pinned-public-IP/SNI transport; max four concurrent probes, 8s per request, 1 MB per response, one same-origin redirect, no retry, no browser or proxy use. Parse RSS/Atom through the same `feedparser` family as the production compatibility audit. Distinguish:
- **production_audit_compatible:** one or more parseable entries (matches the current audit's len(entries)>0 logic).
- **recent_feed_candidate:** at least 3 entries, at least 1 publication within 72h, and at least 3 unique HTTPS item links.
- **distinct publisher family:** do not double-count English/Arabic, root/category or alternate feeds from the same publisher.

Sanitized evidence only (counts, URL and SHA-256, HTTP status, failure classes, freshness, language-script sample counts). No feed XML, article URLs or headlines written to GitHub artifacts. Actual success/promotion depends on measured results and a later independent run.

## Boundaries

Candidate discovery does NOT modify `arabic_newsletter/sources.json`, `SOURCE_AUDIT.json`, production `main`, scheduled workflows, webhooks or databases. Candidates remain disabled. No model calls or Discord posts. The original B41 production source-floor failure is not declared solved until a second publisher passes an actual production-style compatibility audit.

Result: **First hosted source discovery PASS** (source candidates found; production compatibility promotion not performed).

## Hosted B42 verification — PASS

[GitHub Actions run 40464140654](https://github.com/4mghonly/AggregateIT/actions/runs/40464140654) executed on `041ebd87c8105c366397ebde029ccea2e3cfbbde`. Focused checks: **7/7 PASS**; 14 bounded HTTPS feed probes completed; metadata artifact ID `12716330716` (3-day retention).

**Measured totals:** 11/14 technical feed URLs compatible under the current production feedparser semantics; 10/14 with at least one article dated within 72 hours and qualifying linked stories; **9 distinct publisher families** in that latter set (not an audit of their editorial independence). The 10 qualifying URL variants represent Radio Ergo, Shabelle Media, Puntland Post, Horseed Media, Somali Dispatch, Somali Digest, Somali Guardian, Caasimada Online and Goobjoog English. Horseed root/category variants are the same publisher and must never be double-counted.

| ID | Publisher / source | Technical feed result | Recent entries (72h) | Candidate URL |
| --- | --- | --- | ---: | --- |
| radio-ergo-existing | Radio Ergo | Recent | 1 | https://radioergo.org/feed/ |
| sonna-ar-retry | SONNA Arabic | Zero entries | 0 | https://sonna.so/ar/feed/ |
| goobjoog-retry | Goobjoog Somali | HTTP 404 | — | https://goobjoog.com/feed/ |
| shabelle | Shabelle Media Network | Recent | 10 | https://shabellemedia.com/feed/ |
| puntland-post | Puntland Post | Recent | 10 | https://puntlandpost.net/feed/ |
| horseed-somali | Horseed Media Somali | Recent | 10 | https://horseedmedia.net/category/somali-news/feed/ |
| somali-dispatch | Somali Dispatch | Recent | 4 | https://www.somalidispatch.com/feed/ |
| somali-digest | The Somali Digest | Recent | 3 | https://thesomalidigest.com/feed/ |
| sonna-en | SONNA English | Zero entries | 0 | https://sonna.so/en/feed/ |
| somali-guardian | Somali Guardian | Recent | 4 | https://www.somaliguardian.com/feed/ |
| dalsan | Radio Dalsan | Parseable but no recent entries | 0 | https://radiodalsan.com/feed/ |
| caasimada | Caasimada Online | Recent | 10 | https://www.caasimada.net/feed/ |
| goobjoog-en | Goobjoog English | Recent | 10 | https://en.goobjoog.com/feed/ |
| horseed-root | Horseed Media root | Recent, same publisher as category | 10 | https://horseedmedia.net/feed/ |

A technically compatible URL need not be editorially suitable. The reported candidate language tags are prior hypotheses, not verified language classifications. Source article bodies, factual quality, translation into Arabic, duplicate content, channel destinations and live newsroom integration were not exercised by this probe.

## Recommended next development work

1. Independently revalidate **Shabelle Media Network**, **Puntland Post**, and **Somali Dispatch** with the unchanged production `arabic_source_audit.probe` contract on one pinned, read-only runner. Include at least one English-language option for stronger Arabic translation support if the Somali language model is weak.
2. Test **Goobjoog English** as a potential repair for `s058`, but update its declared language to English only after matching feed/article evidence confirms it; avoid silently retaining `language=so`.
3. Keep **Horseed**, **Caasimada**, **Somali Guardian** and **Somali Digest** as diverse alternates.
4. Add passing candidates to a V2-only *disabled* source candidate manifest; after a complete compatibility audit and translation test, plan production registry changes separately. Do not equate two URLs from one publisher with the target floor.
5. Check the production Arabic `somalia` compatible-source floor **>=2**, plus genuine 72-hour item freshness and bilingual content QA, before considering the original B41 blocker resolved.

**Production registry modifications: NONE.** Current `main` continues to report Somalia coverage shortfall until real deployment and a successful re-audit. Operational acceptance remains 6/8; V2 production cutover remains HOLD.

