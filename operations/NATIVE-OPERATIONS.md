# JunkRemoval native source-monitor operations

Prepared overlay only; no remote resource was changed by its author. Frontend and canonical root site-sot.json/publication-status.json remain unchanged. This is the supported GitHub state + Vercel observer pattern recovered from SHTFTV/builders-ltd, adapted to JunkRemoval's real paths and scope. It needs no new database, paid service, stored PAT, copied secret or invented publisher.

## Scope and evidence

The worker monitors five fixed official Canadian/Commonwealth sources and retains changed visible-text digests as editorial-review tasks. Baselines are not stories. Source failures, next eligible retries and per-content task IDs persist in operations/source-state.json. Automatic article generation/publication is NOT connected, and every response keeps fourRolesApproved:false. Custom API observations are not shared-role approval receipts.

Three native GitHub workflows run source monitoring at17, visual checks at37, and supervision at57 past every second hour. Separate per-role concurrency prevents one pending role being canceled by another initial push. Source jobs persist a20-minute lease before fetching; a later job may recover an unexpired lease only after GitHub proves its owner completed. Each source gets3attempts with a hard50-second subprocess deadline, retained eligibility and capped backoff. One failed source does not suppress healthy sources.

Repository-native GITHUB_TOKEN uses contents:write for scoped state commits and actions:read where provider run lookup is needed. No credential is provisioned or read from another site's configuration. check-inputs.py rejects changed script/policy/source inputs before work, lease writes or renderer installation, then persist-state.sh rechecks after each rebase before ordinary non-forced push. State writers retry at most3times. Failure artifacts are retained even if push fails. Do not run persistence from a local/non-provider context.

## Actual rendering and supervision

The visual job renders home, guide index, the real equipment article and planner at1440x900and390x844. It loads lazy images, checks unique metadata, meaningful alt text and readability, exercises guide search, generates/downloads a synthetic brief, and retains actual screenshot SHA256 digests. No image/crop/readability pass is pre-awarded: render-review.json starts empty. A genuine reviewer must inspect actual renders before adding matching reviewed digests and an actor identity. DOM success alone remains held.

Supervisor independently checks completed GitHub runs against exact repo/workflow/head/event; worker and visual schedule proof must be genuine schedule events. It checks current role/root SOT bytes, worker/visual code and public-input bytes, runtime-loaded API SOT, exact deployed article HTML and deployed public-source byte identity (queue-only commit differences allowed). Canonical parking, stale/authentic-but-old-code receipts, incomplete sources, missing screenshot review or source/deploy mismatch remain held.

## Independent observer and delivery

Vercel API endpoints are read-only: /api/operations/, /api/roles/, /api/watchdog/, /api/alerts/. Merge vercel.partial.json into the existing vercel.json without removing existing headers or settings. The proposed native cron /api/watchdog/ runs hourly at33. A request or user-agent is never proof of native execution: nativeExecutionVerified stays false until a corresponding provider log/cron observation is verified separately.

Watchdog checks source health, freshness, native event claims and current-worker/supervisor correlation; exports a stable incident and explicitly synthetic controlled-silence LOGIC canary. That canary is not proof of a real outage/fault injection. The existing authorized Command Center reader must register JunkRemoval's preview origin and exact incident/canary binding, then independently match actual delivery. Owner reading the alert is separate. No email/Slack is sent.

## Integration and remaining proof

Root owns ordinary reviewed source integration/release. Overlay files are listed in outputs/NATIVE-OVERLAY-MANIFEST.json; vercel.partial.json is a merge fragment, not a replacement. Root reports that the existing GitHub→Vercel project link is now provider verified. Do not create a duplicate project. Native state commits must automatically deploy before snapshot-based Vercel observers can see fresh receipts.

Initial state and status packets are truthful unknown/empty, not copied Builders receipts. Actual first push/manual/native runs, rendered screenshots, source failures/retry retention, provider logs, alert-reader matching and recovery must be verified after integration. No continuous uptime, unattended article publication or full Four Roles completion is claimed.

## Local checks

node --test tests/native-operations.test.cjs
PYTHONDONTWRITEBYTECODE=1 python3 tests/source_test.py

8Node+6Python checks pass, including failed-source masking, old-supervisor correlation, missing/stale/future timestamps, non-native trigger rejection, no self-awarded global/native approval, source URL/redirect bounds, provider head/event/workflow binding, and old-public-input rejection while permitting state-only changes. Python/Node syntax and bash-n pass. No actual browser, workflow, schema or production execution was performed for this preparation.
