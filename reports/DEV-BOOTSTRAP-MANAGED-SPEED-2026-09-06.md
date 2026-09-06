# DEV bootstrap and managed-config investigation — 2026-09-06

## Scope and current status

DEV only. No preprod access or changes. Root orchestrates live operations;
isolated CAP and PaaS GSD debug sessions own source investigation and tests.
No customer pod logs, in-guest shell execution, plaintext config, keys or raw
attestation evidence are used for diagnosis. The original canary is preserved.
The managed fix is merged, signed and live on DEV. First after-test N passed
normal authentication, verified HTTPS and real SSH. Repeat O also passed with
the additional CLI TLS reliability fix. The successful-delivery tail improved
consistently; aggregate deployment time remains variable.

## Fresh baseline L

Normal-auth deployment started at 15:32:09.381854 UTC after the DNS fix.
CLI completed successfully in **194.402 s**; the runner observed API running
and verified HTTPS success by **199.317 s**. Real SSH login passed with strict
host-key checking after initial TOFU.
The independent paired observer first sampled verified normal-DNS HTTPS 200 at
**200.817 s**, and pinned HTTPS 200 at **200.825 s**; its sampling rounds differ
from the runner. These are availability observation bounds, not contradictory
server transition times.

| CLI phase | Duration |
| --- | ---: |
| Deploy request | 14.683 s |
| Bootstrap wait | 82.772 s |
| Ownership | 0.933 s |
| Managed-config enqueue | 0.036 s |
| Managed-config wait | 84.401 s |
| Customer-config attestation | 0.584 s |
| Customer-config write | 0.165 s |
| SSH readiness | 5.414 s |

Ownership is intermittent: K took 18.363 s, L took 0.933 s. This rejects a
fixed 18-second ownership timer, not a specific network or crypto hypothesis.

Kubernetes metadata separates startup stages without reading tenant logs:

| Milestone | UTC |
| --- | --- |
| Pod created | 15:32:36 |
| Scheduled | 15:32:39 |
| Both volumes attached | 15:32:50 |
| Volume mount events | 15:32:54 |
| Pod ready to start containers | 15:33:26 |
| Tools init container completed | 15:33:26 |
| Workload container started | 15:33:37 |
| Proxy and ingress started | 15:33:38 |
| Enclava init started | 15:33:51 |

Scheduling to containers-startable is 47 seconds. Attachment accounts for
11 seconds; approximately 32 seconds remain between mount events and
containers-startable. These observations do not isolate confidential VM boot
from every runtime/image operation. Changing guest launch memory, measurements,
policy or runtime configuration is not justified by the aggregate alone.

Kubelet CPU counters show init consumed about 7.47 CPU-seconds by 15:34:27,
with observed usage around 0.21–0.25 cores during the preceding ~30 seconds,
then became nearly idle. Its limit is 250m. This is downstream of bootstrap
availability, not an explanation for the entire bootstrap wait.

Normal destroy exited zero. At 15:38:10 UTC, the disposable namespace, PVs
`pvc-16a00e75-7689-403e-aaed-fc8be6be4d93` and
`pvc-4e5e6b37-4456-48c4-9f3b-434d89ba942c`, and matching Longhorn volumes
were absent. Authenticated lookup returned 404 at 15:38:25 UTC.
The preserved canary retained UID `90f0d6c1-fab7-44ef-9cec-942ea1058efd`,
four ready containers and zero restarts. The bounded metadata observer stopped.

## Confirmed managed-delivery bottleneck

The worker already continues successful durable stages within one dispatch,
but caps admission at four stages: two write/sync pairs. H's successful sync
checkpoints then repeat at approximately five-second intervals:
12:19:36.502, 41.429, 46.521, 51.492, 56.378 and 12:20:01.436 UTC.
Individual successful bursts take about 0.4–0.5 seconds, so the stage count,
not the existing five-second admission window, forces these pauses.

Candidate: raise the finite stage cap from four to 32, enough for the current
13-key template and attachment when operations are fast. Keep the five-second
admission window, dispatch timeout, shutdown checks, durable progress, claim
reload, authority checks and fresh per-stage attestation unchanged. Retryable
423 still yields; this does not move the init-ready marker earlier.

This is not an absolute five-second dispatch deadline: an admitted operation
can finish after the admission window, subject to the existing dispatch timeout.
No timeout increase or session reuse is proposed. Existing PR #86 review
comments concerning durable attempt resets and interrupted bursts were read
and considered in the regression coverage.

## Rejected CPU-only optimization

Local synthetic LUKS tests used a disposable regular file, synthetic input,
unchanged cryptsetup defaults, no network and no host device activation.
At 250m/512Mi, format plus passphrase validation took about 14.09 seconds.
At one CPU/512Mi, the process was OOM-killed (exit 137).
At one CPU/1Gi, successful repeats took about 11.07–11.86 seconds, but
cryptsetup's adaptive Argon2 calibration selected substantially more memory.
A measured one-CPU case peaked at ~659 MB, beyond the original 512Mi limit;
the quarter-CPU/1Gi control peaked at ~189 MB.

Increasing CPU alone is unsafe; increasing both resources has only modest
synthetic latency benefit and changes capacity requirements. Neither is being
shipped. KDF strength, encryption, fresh/existing volume checks and readiness
ordering remain unchanged. These local tests are not confidential-guest
benchmarks and cannot attribute every live init subphase.

## Next verification

[PaaS PR #92](https://github.com/enclava-labs/enclava-paas/pull/92) contains
candidate `d7da0ac`: the production code change is the finite cap plus a comment.
Local validation passed 82 worker DB tests, 422 unit tests (one existing ignored),
formatting and all-target clippy. Actual Pi CLI GLM-5.3 final review and automated
Devin GitHub review found no blockers. Exact-head CI passed and the PR merged
as `826a921` at 15:54:55 UTC. Signed release run `34043806567` succeeded;
digest `sha256:5f4f2e88ef8000238aa90778279c06a3f0ac1cd6c1110238238b7ea64e13b189`
passed exact source/workflow/main/dispatch/release signature verification.
Migration remains 102; native SPDX was downloaded and validated.
[Ops PR #153](https://github.com/enclava-labs/enclava-ops-manifests/pull/153)
updates only DEV PaaS references, both immutable Job names and both generated
configuration checksums. Initial CI caught stale checksums; the existing updater
refreshed them and local environment-release validation then passed. No failed
candidate was promoted. Actual Devin CLI SWE-1.7 independently traced bootstrap.

Ops #153 merged as `0b511a8` at 16:11 UTC after exact-head CI and review;
Flux applied it automatically. Both release Jobs succeeded. Two API replicas
and the worker were ready on the verified digest before the after-test.

## Diagnostic run M: bootstrap attribution before promotion

[CAP PR #101](https://github.com/enclava-labs/cap/pull/101) adds only opt-in
fixed-label bootstrap subphase timings. All 330 CLI tests, CLI clippy, formatting,
and full CAP CI passed; automated review found no issues. It merged as `67b2287`.
The diagnostic CLI uses the unchanged verified public release root and signed
artifact; no CAP API/init/tenant image or runtime setting changed for this run.

M began at 15:52:51.673991 UTC using normal authentication. CLI succeeded in
217.111 s; API/verified HTTPS converged by 223.295 s; real SSH passed.
Bootstrap wait was 86.069 s, with these nested, non-additive details:

| Bootstrap child | Count | Sum |
| --- | ---: | ---: |
| Endpoint acquisition, success | 1 | 0.041 s |
| Attestation, unsuccessful polls | 19 | 27.826 s |
| Poll sleep | 19 | 57.020 s |
| Final successful attestation | 1 | 0.607 s |
| Successful challenge | 1 | 0.091 s |

The longest unsuccessful attempt lasted 20.037 s, approximately 15.217–35.254 s
into the child sequence; another took 7.208 s at 38.255–45.463 s. Both occurred
before proxy availability. Later unsuccessful polls took about 34 ms. Removing
early blocking time would mostly replace it with more polling, not eliminate
the underlying provisioning interval. The fixed three-second poll interval
adds detection jitter; its entire 57-second sum is not removable startup time.
Child sums do not include every line of orchestration/progress overhead.

M ownership took 18.440 s and managed-config wait 86.320 s. Managed delivery's
first-claim-to-completion window was 80.209 s, including nine HTTP 423 write
rejections. First successful write was 15:55:51.011916 UTC; delivery finished
15:56:20.996966, a **29.985-second post-success tail** on the old four-stage cap.

Normal destroy exited zero. At 16:01:48 UTC, M's namespace, PVs
`pvc-716e57f3-91ab-46db-ab90-5d7358eb6f1f` and
`pvc-90acf013-8326-4056-a513-e1851e3ffc44`, and matching Longhorn volumes
were absent. Authenticated lookup returned 404 at 16:01:53 UTC. The original
canary retained its UID, four ready containers and zero restarts. Exact
read-only DB and metadata observers were stopped.

[PaaS PR #93](https://github.com/enclava-labs/enclava-paas/pull/93) updates the
strict collector/analyzer for these fixed labels. Review caught parent/child
double counting; the fix groups repeated child outcomes separately and retains
unsuccessful polls while requiring successful parent phases. Both self-tests
pass and historical H parent totals replay unchanged. A review claim that the
fractional timestamp self-test fails was not reproducible on Python 3.12.3 or
the passing CI self-test job; no parser relaxation was made.

## Additional confirmed reliability defect

The shared CLI certificate-fetch helper bounded TCP connection attempts but
did not bound the TLS handshake after TCP connected. A local peer accepting TCP
without speaking TLS exceeded a one-second test watchdog despite a 50ms helper
budget. [CAP PR #102](https://github.com/enclava-labs/cap/pull/102) applies the
existing transport budget to the handshake, with stalled-peer and successful
TLS/SPKI regression checks. Review additionally identified its transient-error
classification requirement; exact timeout classification was fixed in `eac3588`.
All four current-head CI checks passed and the PR merged. The original bot
review and all subsequent comments were assessed; this is not a claim that a
bot re-reviewed the final revision. PaaS #93 also merged after CI and all review
findings were either corrected or answered with reproducible evidence.

This is bounded failure handling, not an observed deployment speedup. DNS
fallback remains limited to TCP failures; TLS failure does not authorize fallback
or bypass. No aggressive shorter bootstrap budget, attestation-session cache,
KDF change, or early readiness marker is introduced.

## After-test N: targeted improvement, residual init wait

N started at 16:12:28.667082 UTC using the same CLI as M and the new PaaS image.
CLI succeeded in **230.563 s**, API running and verified HTTPS by **235.537 s**.
Real SSH on the disposable relay port passed; strict checking followed initial
TOFU, not an attestation-bound SSH host-key claim.

| Metric | M: four stages | N: 32 stages |
| --- | ---: | ---: |
| Bootstrap wait | 86.069 s | 86.088 s |
| Ownership | 18.440 s | 0.963 s |
| Managed wait, CLI | 86.320 s | 117.117 s |
| Managed first claim to delivery | 80.209 s | 111.747 s |
| HTTP 423 rejections before success | 9 | 20 |
| First successful write to delivery | 29.985 s | 2.564 s |
| CLI total | 217.111 s | 230.563 s |

The targeted successful-delivery tail fell **91.4%**, saving **27.421 s** in this
comparison. First write succeeded at 16:16:08.618175, delivery completed at
16:16:11.182230. All 13 writes and syncs succeeded, with fresh per-write
attestation and durable checkpoints. The existing stage admission window held.

The whole deployment did **not** improve: init readiness took longer, with
20 actual 423 responses before the first successful write. This precedes the
changed success-burst behavior and must be investigated independently rather
than hidden by reporting only the improved tail. Two runs are not a latency
distribution or proof of a whole-system regression.

Normal destroy exited zero. At 16:18:44 UTC, authenticated lookup returned 404;
the exact namespace, PVs `pvc-f6e83c7e-00ea-4c9e-8fae-a7842112b834` and
`pvc-c72a6475-4348-4bb4-88da-7cebc3317d51`, and matching Longhorn volumes
were absent. The original canary retained its UID, four ready containers and
zero restarts. Both exact read-only observers were stopped.

## Repeat O and remaining measured gaps

O started at 16:19:25.459278 UTC using the same PaaS release and the CLI from
CAP #102 (`eac3588`, merged as `4cf9d4b`). The CLI binary SHA256 was
`73bee0f1a3d9bf671b25c7a147393b1c3760f8610af143fe45bb264f5b4e7d7a`.
CLI completed in **167.798 s**, API running and verified HTTPS by **172.739 s**;
real SSH passed. Bootstrap was 82.972 s, ownership 0.942 s, managed CLI wait
57.555 s. First successful write to delivery was **2.378 s**, independently
confirming removal of the old scheduling tail.

Managed delivery still spent 52.981 s from first claim to completion, including
two 20-second attested-session timeouts. The bounded attestation records include
two KDS HTTP 429 responses. There were no 423 writes in this run: time was spent
before a write could be attempted. A missing 423 does not establish earlier init
readiness. Fresh attestation was retained; timeout/budget/cache behavior was not
changed to hide provider rate limiting.

N's metadata also narrows a different residual: init had consumed 7.442 CPU-s
by 16:14:47, then only another 0.075 CPU-s through 16:15:55 while readiness
remained blocked. That rejects sustained CPU-heavy work as the extra delay,
but cannot exclude blocked disk I/O inside a LUKS operation. Static certificate
provisioning is a source-supported candidate, not a proven cause. Its broker
currently performs DNS visibility, ACME validation and certificate retrieval
before init readiness. Fixed-label, opt-in broker timing is being prepared to
separate those stages without reading tenant logs or exposing certificate inputs.

Normal destroy exited zero. At 16:24:35 UTC, O authenticated lookup returned 404;
its namespace, PVs `pvc-f47b9957-5496-4655-91a9-887ab1d296b3` and
`pvc-045daeb7-ae5f-460f-bee3-cdb5a92bbd12`, and matching Longhorn volumes
were absent. The preserved canary retained the original UID, four ready
containers and zero restarts. Exact read-only DB/metadata observers stopped.

Confidentiality regression checks and real attested deployments passed; that is
not a proof of absolute security or production readiness. No crypto reduction,
plaintext logging, attestation bypass, readiness bypass or preprod change was
introduced. The unsafe CPU-only experiment was explicitly rejected.
