# DEV bootstrap and managed-config investigation — 2026-09-06

## Scope and current status

DEV only. No preprod access or changes. Root orchestrates live operations;
isolated CAP and PaaS GSD debug sessions own source investigation and tests.
No customer pod logs, in-guest shell execution, plaintext config, keys or raw
attestation evidence are used for diagnosis. The original canary is preserved.
This report is a checkpoint; candidate changes are not yet live.

## Fresh baseline L

Normal-auth deployment started at 15:32:09.381854 UTC after the DNS fix.
CLI completed successfully in **194.402 s**; the runner observed API running
and verified HTTPS success by **199.317 s**. Real SSH login passed with strict
host-key checking after initial TOFU.

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

Test the managed cap against real local DB failure/lease/rotation regressions,
review the PR, build a signed release and promote only DEV. Add opt-in fixed-label
CLI subphase timings for bootstrap polling; preserve existing timeout/retry and
verification behavior. Repeat normal-auth deployment with metadata, verified
HTTPS/SSH and normal cleanup. Report measured improvement, not a prediction.
