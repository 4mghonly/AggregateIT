# Arabic Newsletter

An isolated geopolitical / security edition on branch **Arabic**.
This branch is intentionally minimal: the runtime lives in `arabic_newsletter/`
and the only GitHub Actions workflow is `.github/workflows/arabic-newsletter.yml`.
Legacy market, English briefing, Gazette, daily/weekly digest and general engine
components have been removed from this branch.

## Approved scope

- Modern Standard Arabic from original-language evidence; three 3840×2160 PNG slides in the approved clean analytical-dashboard format
  in the approved Gazette palette and panel geometry, with native RTL shaping.
- Every six hours: **00:00 / 06:00 / 12:00 / 18:00 Asia/Dubai**. Each edition covers
  its previous six-hour publication window. Publication can be delayed by runner queues.
- GCC (AE/SA/QA/KW/BH), **Oman** as a dedicated country view, Iran, Turkey, Iraq,
  Yemen, **Egypt** as a dedicated country view, Sudan, Sahel
  (Mali/Burkina Faso/Niger/Mauritania/Chad/Senegal), North Africa
  (Algeria/Tunisia/Morocco/Libya, including Western Sahara developments),
  Pakistan, Afghanistan, Horn (Ethiopia/Djibouti/Eritrea), Somalia (including
  Somaliland developments), Palestine/Israel, Lebanon, Syria, Jordan.
- Include diplomacy, conflict, security, instability, sanctions, arms embargoes,
  strategic infrastructure and conflict-related humanitarian reporting.
- Include cautious, explicitly labelled analytical assessments and watch points.
- Exclude financial feeds, market prices, tickers, crypto and business sentiment.
  Legacy market and non-Arabic delivery code is not present on this branch.

## Runtime

```bash
python -m pip install -r arabic_newsletter/requirements.txt
python -m unittest arabic_newsletter.test_arabic -v
python -m arabic_newsletter.run --sample --long
python -m arabic_newsletter.run --audit
python -m arabic_newsletter.run --preflight --probe-model --probe-discord
python -m arabic_newsletter.run --send
```

Linux fonts: `fonts-dejavu-core`; Pillow must have RAQM enabled. Rendering fails
rather than drawing disconnected Arabic letters. All output and state lives under
`arabic_newsletter/runtime/` or an explicitly configured `ARABIC_STATE_DIR`.

## Secrets and deployment

Required GitHub Actions secret: `DISCORD_WEBHOOK_ARABIC` for the Arabic briefing channel.
It never falls back to `DISCORD_WEBHOOK`, and the Arabic branch contains no legacy
Discord sender. The former default-branch sender workflows for Market Pulse / engine,
Gazette slides, daily digest, weekly review and executive briefing are disabled by
removing their workflow files, so they cannot post automatically. Set the Arabic
webhook in repository Settings → Secrets and variables → Actions. Never commit a
webhook or API key.

The workflow can reuse existing `QWEN_API_KEY` and `QWEN_BASE_URL` secrets without
changing them. Optional isolated overrides: `ARABIC_LLM_API_KEY`,
`ARABIC_LLM_BASE_URL` (secrets) and `ARABIC_LLM_MODEL` (repository variable).
The workflow uses `qwen3.8-omni-flash`. Live preflight bypasses the model cache, performs a real API probe, and verifies the dedicated Arabic Discord webhook route before publication.

GitHub cron only schedules workflows from the default branch. Production timing is
therefore owned by a tiny launcher workflow on **main** that runs at
`0 2,8,14,20 * * *` UTC (06:00/12:00/18:00/00:00 UAE), checks out **Arabic**,
and executes only this isolated runtime with `DISCORD_WEBHOOK_ARABIC`. The launcher
does not import or execute the main engine. The Arabic branch workflow remains for
tests, previews and explicit manual live runs. The former commit-based external
scheduler is retired; `trigger.json` is no longer a production scheduling mechanism.

## Evidence and source policy

`sources.json` is an inventory with explicit verification states, never a promise
of universal access. `--audit` discovers feeds and publisher-linked social URLs,
tests parsing and records dated-item counts. The audit report distinguishes
network failures, forbidden pages, unparseable feeds and undiscovered feeds.
A failed source remains visible as a coverage gap. Production rotates a bounded
retry batch through prior audit failures (weighted toward non-Arabic sources), while
`--audit` probes the entire registry so a transient outage cannot retire a source forever.
No paywall bypass, private group collection, CAPTCHA bypass, or guessed account IDs.

RSS/Atom, dated article pages, reviewed publisher-linked public Telegram channels
and YouTube feeds with verified channel IDs are supported. X, Facebook, Bluesky
and unreviewed social links remain discovery-only; availability is never fabricated.

Items without a publication timestamp cannot become fresh news merely because
retrieved now. Same-URL and same-title duplicates are removed before the model;
multilingual/syndicated event copies are grouped during synthesis and review.
Model inputs and outputs are bounded and cached. At most eight editorial model HTTP requests per synthesis/review client, including retries.
If every event is rejected, one correction pass uses the reviewers’ reasons and
then repeats the same deterministic checks and editorial review. A second failed
review blocks publication; there is no unbounded correction loop. The cached preflight probe
can use up to two additional requests on its first run. Early scheduler wakeups
within ten minutes of an edition boundary target and wait for that boundary.
Each event needs literal supporting evidence, known article IDs, Arabic prose,
supported numeric values and an editorial consistency review. All published
claims remain attributed: a model review is not independent verification.

Slides use measured text boxes and visible ellipses for oversized content.
`sources-ar.txt` carries all complete summaries, analysis and links; no content is
silently lost solely to the slide layout. The chart measures selected coverage,
not real-world incident prevalence or quantified geopolitical risk.

## Reliability and remaining operational limitations

- Original pipeline and caches are never loaded; Arabic concurrency is separate.
- Dedicated six-hour edition IDs, SQLite ledger and exclusive execution lock.
- Confirmed sends are skipped. Ambiguous POST responses are marked `uncertain`
  and are NOT retried automatically, preventing blind duplicate delivery.
- Inspect Discord before manually reconciling any `uncertain`/`sending` entry.
- GitHub Actions cache persistence is best-effort, not a durable database.
  Cache eviction can lose delivery history. A persistent runner/state volume is
  preferred where exactly-once guarantees are required; this implementation does
  not claim exactly-once delivery across cache loss.
- Total source-collection failure still blocks publication. A cycle with active sources but no qualified events publishes an explicit no-material-change briefing; invalid model output or failed editorial checks remain visible in diagnostics. Failure remains visible in Actions and uploaded diagnostic artifacts.
- Cross-language semantic deduplication and translation still require quality
  monitoring; deterministic guards cannot prove every interpretation correct.
- Region-level source health is not a claim that every country is fully covered.
- Samples are explicitly synthetic; `--sample --send` is prohibited.

## Acceptance

No inherited-file changes; sample, empty and long RTL slides render offline;
financial stories rejected; changed casualty numbers and invented citations
rejected; publication windows correct across midnight; legacy webhook fallback
blocked; duplicate/uncertain delivery tested. Live completion additionally needs
successful collection, model translation and confirmed delivery to the new channel.


## Locked visual format

The Arabic briefing uses the approved three-slide, image-free command-brief design. It is typography-first, uses no generated imagery or vector maps, preserves the regional dashboard on page 2, and reserves page 3 for expanded evidence-bound analysis. Do not reintroduce decorative rendering that competes with legibility.
