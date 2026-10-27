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

Result: **PENDING hosted candidate probe**.
