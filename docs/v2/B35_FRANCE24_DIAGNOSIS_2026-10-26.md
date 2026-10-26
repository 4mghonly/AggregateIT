# AggregateIT V2 — B35 France 24 Arabic one-item parser diagnosis

Date: 26 October 2026  
Branch: `rebuild/aggregateit-v2`  
Starting checkpoint: `ba5f89a74ab7b6afede77682c970a20a1e946377`

## Prior anomaly

B34 one-shot run `40388155216` fetched 41,930 bytes from the registered
France 24 Arabic RSS source. V1's parser accepted 24 eligible distinct items;
V2 accepted 23. B31 comparison recorded **one V1-only item and no V2-only item**.
This was a true observation on that input, but the raw source bytes were not
retained and the missing item's rejection reason was not logged. The earlier
body **cannot be reconstructed from its SHA-256**.

## Authorized bounded investigation

- Add an isolated classifier that operates on in-memory live bytes and uses
  the actual unchanged V1 code, V2 parser, and a separate per-XML-entry
  rejection trace to identify classes of difference.
- One new GitHub-hosted workflow on V2 only, triggered only by the creation
  of its own workflow file. One new read-only, public-IP-pinned HTTPS fetch
  of the registered France 24 Arabic RSS feed; 9-second timeout; at most
  one same-host redirect; max 1 MB; no raw content retained.
- Record feed SHA-256, lengths, counts, refusal categories, and SHA-256 item
  fingerprints only. Never include article text/titles/links in the public
  artifact. The publisher RSS URL itself is not secret.
- Run focused synthetic tests and full V2 regression before the live probe.
  Keep V1, V2 parser logic, main, all production schedules, webhooks, model
  credentials and databases unchanged.
- If live one-item drift reoccurs, record reason class and whether it is a
  safety-policy difference or an actual normalization defect. If not, mark
  historical root cause NOT REPRODUCED; do not invent one.

## Status

**Queued for one qualifying workflow-file push. Not yet executed.**
The B34 operational evidence bar remains 6/8. Parser parity HOLD.
Future source promotion, parser modifications, full editorial shadow,
canary, and rollback acceptance are not authorized by this diagnostic.
