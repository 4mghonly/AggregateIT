# AggregateIT V2 — B1 Reliability Package (isolated)

Date: 23 October 2026 (UAE)  
Branch: `rebuild/aggregateit-v2`  
Status: **B1 targeted reliability slice verified offline; B1 production-equivalent validation pending**

## Implemented in this package

1. English audit runner now installs `requests`, which the imported `social.py` actually requires. `check_reddit` catches a single provider exception and emits one failed source record with exception **type only**; other source tasks may complete. Audit still only produces a report, not a registry rewrite.
2. English `llm.chat` remembers the last healthy credential route after the independently configured fallback succeeds. It can return to the primary if the fallback later fails. Existing global API-call ceiling still bounds attempts.
3. Arabic synthesis retains the existing initial strict-JSON retry. If both primary responses are malformed, its compact, geographically balanced recovery now switches to a configured independent fallback **before** allocating more primary tokens. One-route installs retain the compact repair on their only route. The same evidence validation and editorial review still apply.
4. Arabic analysis that degrades to deterministic content now records `analysis_degraded`; the final `llm_health.json` reports `degraded` if editorial fallback, analytical fallback, or unresolved source regions exist. The report lists unresolved regions and a coarse, safe reason. It does not invent missing content or block an otherwise permitted degraded edition.
5. `v2_route_health.py` defines a bounded in-memory (64 events per production gateway, hard maximum 128) telemetry contract with fixed stage/route/outcome/HTTP-code fields. No provider messages, credentials, prompts, article content or URLs are stored. This is **not** a Cloudflare D1 integration or a persistent dashboard; those remain B6.

## Offline evidence

10 focused `unittest` regressions passed on Python 3.12. The harness loaded the actual candidate modules from memory and stubbed missing third-party imports / external boundaries. Cases:

- HTTP 403 classification and fallback with no secret-bearing logs.
- English fallback sticky preference and recovery to primary.
- English call-budget denial of further network attempts.
- Arabic compact recovery switches route after two invalid primary responses.
- Arabic 403 failover.
- Arabic two timeouts then fallback, with retry ceiling.
- Arabic truncated content requests compact recovery rather than silent acceptance.
- Arabic analytical degradation is explicitly recorded.
- One Reddit audit timeout becomes an isolated source failure.
- Journal caps, fixed schema and unknown-route rejection.

No live model, news-source, Discord, Cloudflare or paid API calls were made. No Actions were dispatched. Python source syntax checked for all edited Python modules. A full dependency-installed repository suite and an actual zero-post Arabic/English end-to-end rehearsal were **not run** because this container lacks application dependencies and a writable clone.

## Residuals / next work

- Run `python -m unittest discover -s tests -p 'test_b1_*.py' -v` in an isolated clone with `pip install -r requirements.txt -r arabic_newsletter/requirements.txt`. Then run existing nearby suites. No GitHub Actions trigger.
- Run a simulated, no-post English and Arabic briefing against frozen local fixtures. Verify generated `llm_health.json` reports degradation and accepted events retain evidence. This is required to close B1 fully.
- Audit the entire source registry in B2. A fixed audit dependency does not imply sources are live. Somalia source-family gap and fallback credentials remain unresolved; **do not** ping live providers or change secrets in B1.
- `RouteJournal` is intentionally in-memory, so the dashboard, retention, SQLite/D1 budgets, and manual Drive export remain B6 only. Policy: `docs/v2/ANALYTICS_STORAGE_POLICY.md`.
- Historical quality baseline has missing independent corroboration and Arabic translated yield. Neither is claimed fixed by this routing package.

## No-go confirmation

Main and other production branches are outside scope. No schedules, webhooks, provider credentials, database, migrations or existing source registry were modified. No cutover or dispatch is authorized.
