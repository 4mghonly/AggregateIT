# Independent production cadence

The scheduler is ready but **not deployed or active**. The connected Cloudflare account has no AggregateIT dispatch credential. GitHub's connected app cannot export its credential, and the workflow GITHUB_TOKEN cannot be used as a persistent external credential.

Activation requires a fine-grained GitHub credential scoped only to 4mghonly/AggregateIT with Actions read/write and repository metadata read. Put it directly into the new Worker's `GITHUB_DISPATCH_TOKEN` secret through Cloudflare's secure secret UI or `wrangler secret put`; never commit or paste it into chat. Deploy from this directory with `wrangler deploy` after the secret is provisioned.

The five-minute cron dispatches due editions only when no native queued/running/successful run exists for the slot. A Durable Object serializes and remembers accepted dispatches. Production workflows independently skip a completed scheduled slot, covering delayed native GitHub runs. A failed dispatch is retried on the next tick; an accepted dispatch is never repeated in the same slot. Existing production schedules and manual runs remain supported. No Discord or model secrets are copied into the scheduler.

After activation, verify a read and dispatch receipt and the next hourly, Arabic and Gazette slots. Local tests cannot prove external cadence.
