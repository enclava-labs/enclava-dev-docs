# Next deployment-speed investigation — 2026-09-06

## Current checkpoint — run G complete, 12:10 UTC

[PaaS PR91](https://github.com/enclava-labs/enclava-paas/pull/91) merged as
`d009631ecc108fd9941b596096d6edad3677b41d`. Its signed release
[34030938453](https://github.com/enclava-labs/enclava-paas/actions/runs/34030938453),
tag `manual-20260906-dev-health-cadence1`, produced image digest
`sha256:80717cbd8951dbb6ba309c145a867ee16d8a8b3f108b0c08de49d8e915b2647a`.
[Ops PR151](https://github.com/enclava-labs/enclava-ops-manifests/pull/151)
merged as `e0d4beb`; Flux automatically applied the DEV change. At 12:02 UTC,
both API replicas and the worker were ready on that exact image ID, and both
Jobs were complete. Preprod was not changed.

Fresh normal-auth run G started at 12:01:59 UTC and completed deployment,
external SSH/HTTPS verification and normal deletion. CLI completion was
214.430 seconds versus F's 202.832 seconds: this single run was 11.597 seconds
slower, not an end-to-end speed improvement. The marker-only in-guest probe remains
offline-only: Kata blocked shell execution. No policy bypass was attempted and
no raw denial output is published.

[CAP PR99](https://github.com/enclava-labs/cap/pull/99) merged as
`f1cd1e0e4c7f541b3f7c91f3da31a419b610de45`; build
[34031244839](https://github.com/enclava-labs/cap/actions/runs/34031244839)
is the associated release build. Its DEV promotion PR is being prepared;
that CAP change has **not** been promoted to DEV and did not affect run G.

## Run G: measured outcome

The versioned timing filter and analyzer attribute the following metadata to the
same managed-delivery event. Durations are rounded to milliseconds; nested stages
must not be summed into an end-to-end total.

| Measurement | F | G |
| --- | ---: | ---: |
| CLI completion | 202.832 s | 214.430 s |
| Ownership phase | 0.945 s | 18.434 s |
| CLI managed-config wait | 86.353 s | 86.438 s |
| Managed-delivery window | 82.230 s | 80.636 s |
| First rejected write to first successful write | 43.511 s, status unavailable | 47.029 s, all 9 rejections HTTP 423 |
| Payment-health passes in delivery window | 15 | 2 |
| Worker health-cache phase, summed | 44.407 s | 5.959 s |
| Worker sleep in delivery window, summed | 14.768 s / 15 intervals | 55.378 s / 16 intervals |

G's bootstrap wait was 82.945 seconds. Its ownership phase increased sharply,
but one sample does not establish why. The two health passes included 3.763 seconds
of sync-list work and 2.042 seconds of readiness work, nested inside the health
phase above. Cadence reduced repeated monitoring work substantially; measured
loop sleep increased instead, while managed-config wait stayed almost unchanged.
The existing five-second tick floor and per-tick stage scheduling still limit
progress, alongside initialization. This does not mean all sleep can be removed:
sleep overlaps init readiness and retry/backoff constraints.

For G's matching event, the first rejected write was at
12:04:08.990490 UTC and the first successful write at 12:04:56.019569 UTC,
a 47.029079-second interval. All nine early failures were HTTP 423. This confirms
the write-readiness gate was closed during those attempts, not which confidential
init subphase consumed the interval. The blocked in-guest probe provides no phase
or CPU-throttling evidence. F's missing numeric statuses remain unknown.

CLI completion is not the same milestone as externally usable deployment:

| G milestone | Observation |
| --- | --- |
| Pod scheduled | 12:02:32 UTC |
| Pod ready to start containers | 12:03:17 UTC; 45 seconds after scheduling |
| Pod Ready | 12:06:29 UTC; 269.803 seconds after run start |
| First API running sample | 278.381 seconds after run start |
| External SSH | Around 12:06 UTC; strict host-key verification after initial TOFU returned `SSH_OK` |
| First external HTTPS 200 sample | 12:07:00.575 UTC; 301.378 seconds after run start |

These are observation/sample bounds, not exact underlying transition times.
TLS handshakes failed before the eventual HTTPS 200; no TLS root cause is
established by these measurements.

Normal destroy exited zero. By 12:09 UTC the exact disposable namespace,
the two PVs identified by `5576c502` and `961919d9`, and their corresponding
Longhorn volumes were absent. Authenticated lookup returned 404 at 12:10:32 UTC.
The preserved canary retained its UID, all four containers ready and zero
restarts. Only sanitized generated metadata is summarized here; private/raw
evidence files and customer pod logs are not published.

## Completed prerequisite

[PaaS PR90](https://github.com/enclava-labs/enclava-paas/pull/90) merged at
08:10:40 UTC as `99d0219ef2637ac7dfd2da2aac377866fa8900d0`. Its tree matches
reviewed head `4020c94d68b517179d305777b4349d7508827586`. Exact-head Rust,
frontend, collector, story-contract and image-validation CI passed. Release-only
hardware/supply-chain checks were skipped on the PR, not represented as passed.
All five concrete review findings were fixed and resolved; the final automated
review reported no major issues. Independent narrow recheck passed as well.

The change emits only a bounded numeric HTTP status from typed managed-write
errors. No response body, header, endpoint, token or configuration value is
exported. Zero/absence means unavailable, not success. Retry, authority,
attestation and readiness behavior is unchanged. Collector regressions reject
arbitrary poll fields, mismatched/embedded logger targets, contradictory status
records, invalid calendar timestamps and duplicate fields.

Signed release build
[34021138045](https://github.com/enclava-labs/enclava-paas/actions/runs/34021138045)
was dispatched from that main revision with tag
`manual-20260906-dev-write-status1` and completed successfully. This diagnostic-only
release was not separately promoted; the subsequent PR91 release above includes
the diagnostic changes.

## Historical F baseline and causal limits

Previous run F measured 202.832 seconds CLI completion, including an 82.230-second
managed-delivery window. Nine early write failures preceded the first successful
write by 43.511 seconds. Those historical records do not contain numeric status;
they cannot retrospectively establish a 423 readiness failure.

Source tracing found that owner-seed acknowledgement precedes encrypted volume
setup. Init then performs mount ownership, Trustee policy verification, optional
static TLS provisioning, component-seed delivery, workload namespace binding and
runtime handoff before marking ready. Proxy writes return 423 while the init-ready
gate is closed. This is a hypothesis for F, not live causal attribution. Do not
move the ready marker earlier or disable the gate to obtain a faster result.

Payment-health refresh consumed 44.407 seconds over 15 passes during that same
window. These nested durations cannot be added to total latency. Separating its
scheduling needs preservation of actual observation timestamps, startup/failure
semantics, wallet locks/fences, and checkout freshness. A longer healthy-cache TTL
is not an approved optimization.

Devin CLI SWE-1.7 independently traced the scheduling boundary. Health probes
hold the same PostgreSQL advisory transaction fence used by Spark destination
and readback dispatch. Those dispatches participate in the outbox phase's join,
so a blocked payment can still delay a whole worker tick. Health and tick
finalization write one combined heartbeat snapshot consumed by
internal health, metrics and checkout readiness. A direct background-task move
would introduce competing snapshot writers and wallet contention.

A future split therefore needs explicit ownership of independently timestamped
health observations, unchanged consumer freshness/failure checks, lifecycle and
cancellation tests, and a tested contention policy. A try-lock only avoids
waiting to acquire an already-busy fence; it does not prevent a probe that already
holds the fence from delaying a later payment. No new table, background SDK
session or persistent wallet cache has been implemented. Instead, PR91 implements
the simpler in-loop monitoring cadence described below.

## Remaining execution gates

1. Verify the CAP PR99 release and separately review its DEV promotion before
   applying it. Do not attribute CAP changes to run G.
2. Repeat a fresh normal-auth deployment after promotion. Use the versioned
   timing filter and analyzer, check pipeline exit status, and observe actual
   SSH/HTTPS, public running and pod readiness beyond CLI exit. Repeat normal
   deletion and exact storage/canary checks. Never collect customer pod logs.
3. Separate the initialization gate, ownership variance and five-second worker
   scheduling floor using permitted metadata, then select the smallest causal
   optimization. The Kata shell restriction remains in force; no measurement
   warrants bypassing confidentiality or readiness controls.

DEV normal-auth preflight and encrypted backup/isolated four-database restore
passed before this checkpoint. The backup is per-database logical snapshots,
not a coordinated full recovery point. No preprod environment access or changes.
This change-scoped verification is not an absolute confidentiality guarantee or
a declaration of full production readiness.

## Follow-up: simpler monitoring and fresh-app priorities

[PaaS PR91](https://github.com/enclava-labs/enclava-paas/pull/91), now merged and
promoted to DEV as recorded above, implements startup-plus-30-second completion-relative monitoring in
the existing loop. No background task/table/session/cache was added. Skipped
checks preserve JSON and time; fresh observations use the existing PostgreSQL
heartbeat-start timestamp. Transaction checks, locks and two-minute freshness
predicates remain unchanged. Local DB, consumer, clippy and formatting checks
passed, with exact coverage recorded in the PR. Run G confirms reduced monitoring
work, but not a faster user deployment. Monitoring can detect
outages and recover more slowly: the 30-second interval is completion-relative
and busy ticks/backoff can delay it further. Failed persistence is not proof
that old healthy observations were invalidated; unchanged staleness remains
the fallback.

A read-only check of the preserved DEV canary confirmed app and ingress readiness
initial delays of 180 seconds and an init CPU limit of 250m. The canary UID remains
`90f0d6c1-fab7-44ef-9cec-942ea1058efd`, all four containers ready, zero restarts.
These settings matched the CAP defaults observed before PR99. Earlier identical
readiness predicates are a candidate in the separate CAP work, but no 180-second user-latency saving is established:
measure first external HTTPS/SSH separately from declared rollout readiness.

Next fresh-app candidates: measure init phase/throttling before raising its bounded
CPU allowance; split G's 45-second scheduled-to-ready-to-start interval into volume attachment, runtime boot
and image pull/unpack; prefetch only verified immutable public artifacts into the
actual runtime cache if pulls are material. Never reuse tenant keys, decrypted
volumes, private-image plaintext or attested sessions. CAP PR99 is source-merged,
not deployed; the running DEV CAP settings have not been changed by that PR.
