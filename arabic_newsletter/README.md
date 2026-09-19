# Arabic Newsletter

An isolated geopolitical / security edition on branch **Arabic**.
This branch is intentionally minimal: the runtime lives in `arabic_newsletter/`
and the only GitHub Actions workflow is `.github/workflows/arabic-newsletter.yml`.
Legacy market, English briefing, Gazette, daily/weekly digest and general engine
components have been removed from this branch.

## Approved scope

- Modern Standard Arabic from original-language evidence; three 3840×2160 PNG slides
  in the approved Gazette palette and panel geometry, with native RTL shaping.
- Every six hours: **03:30 / 09:30 / 15:30 / 21:30 Asia/Dubai**. Each edition covers
  its previous six-hour publication window. Publication can be delayed by runner queues.
- GCC (AE/SA/QA/KW/BH/OM), Iran, Turkey, Iraq, Yemen, Sudan, Sahel
  (Mali/Burkina Faso/Niger/Mauritania/Chad/Senegal), North Africa
  (Algeria/Tunisia/Morocco/Egypt/Libya, including Western Sahara developments),
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
python -m arabic_newsletter.run --preflight --send
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
The workflow's default model matches the existing slide workflow; model/API
compatibility must be demonstrated on a live run. Preflight validates presence
and syntax only, not authentication.

GitHub cron does not run a workflow existing only on a non-default branch.
The connected scheduled automation instead edits **only** the dedicated new
`arabic_newsletter/trigger.json` on **Arabic**. Its push runs the new workflow.
The default branch keeps its non-delivery utility workflows, but its legacy Discord
delivery workflows are disabled. A self-hosted alternative can run the same CLI under cron:
`30 5,11,17,23 * * *` (UTC), equivalent to the four UAE times. Use only one scheduler.

## Evidence and source policy

`sources.json` is an inventory with explicit verification states, never a promise
of universal access. `--audit` discovers feeds and publisher-linked social URLs,
tests parsing and records dated-item counts. The audit report distinguishes
network failures, forbidden pages, unparseable feeds and undiscovered feeds.
A failed source remains visible as a coverage gap and is retried on later runs.
No paywall bypass, private group collection, CAPTCHA bypass, or guessed account IDs.

RSS/Atom, dated article pages, reviewed publisher-linked public Telegram channels
and YouTube feeds with verified channel IDs are supported. X, Facebook, Bluesky
and unreviewed social links remain discovery-only; availability is never fabricated.

Items without a publication timestamp cannot become fresh news merely because
retrieved now. Same-URL and same-title duplicates are removed before the model;
multilingual/syndicated event copies are grouped during synthesis and review.
Model inputs and outputs are bounded and cached. At most six editorial model HTTP requests per run, including retries.
If every event is rejected, one correction pass uses the reviewers’ reasons and
then repeats the same deterministic checks and editorial review. A second failed
review blocks publication; there is no unbounded correction loop. The cached preflight probe
can use up to two additional requests on its first run. Early scheduler wakeups
within two minutes of an edition boundary wait for that boundary.
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
- Empty/failed collection, invalid model output or failed editorial checks block
  publication. Failure remains visible in Actions and uploaded diagnostic artifacts.
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
