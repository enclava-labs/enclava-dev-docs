# DEV certificate broker / DNS follow-up — 2026-09-06

## Scope

Continuation of `DEV-BOOTSTRAP-MANAGED-SPEED-2026-09-06.md`. DEV only;
no preprod access or changes. Preserve the original canary UID
`90f0d6c1-fab7-44ef-9cec-942ea1058efd`. No confidential tenant logs, guest
diagnostic exec, plaintext config, private keys or raw attestation evidence.

## Review and release

CAP #103 merged as `947a752` after full workspace and API image CI passed.
The review's outstanding-CI note was answered with exact successful run IDs
`34045696164` and `34045696101`. Nested lookup phases remain non-additive;
no extra status/error fields were introduced. PaaS #94 also merged after all
applicable comments were assessed; the unrelated stale relay review was
explicitly retracted by its author and was not treated as broker evidence.

Signed API release dispatch `34056052074` targets exact main `947a752`, tag
`manual-20260906-dev-broker-timing`. Only the API digest will be promoted;
tenant images, appraiser, PaaS, trust roots and migration version stay unchanged.
The exact target `cap::workload_tls_timing=debug` will be appended to existing
CAP API logging directives, without enabling global debug logs.

The release completed successfully. Its downloaded digest is
`sha256:0e2e37f1cfc5311da81f8b7bae8755416ab76446fbabe7b9d69823bfe0070daf`,
migration46. Official API reference and exact main-workflow keyless signature
verification passed. Source/dispatch/release profile are bound through the
successful workflow record and artifact; the cosign payload has no optional
source annotations, so none are claimed. [Ops #154](https://github.com/enclava-labs/enclava-ops-manifests/pull/154)
contains the DEV promotion. Review caught stale README provenance, now corrected
for both current API and already-live PaaS images. DEV-only server dry-run,
environment contracts, kustomize render and contained-rollout regressions passed.
Ops #154 merged as `e1490cb` after exact-head CI `34057250453` passed and the
reviewer marked the provenance finding resolved. Flux applied it without a
manual reconcile. New API pod `cap-api-b698456cb-pjwkp`, UID
`f0c3b1fe-ed33-4ad4-bb51-e557fe985fa4`, is ready with zero restarts on the exact
digest; migration Job succeeded on the same image. Readiness reports ten checks.
Fresh normal-auth baseline P started at 20:17:13 UTC with the unchanged O CLI.

## Public-name control from ordinary CAP API pod

On the existing non-confidential control-plane pod
`cap-api-57fd7c8968-v4wvc`, public `example.com` lookups to 1.1.1.1 and
1.0.0.1 each timed out under a two-second probe budget. TCP connects to port53
on both addresses also timed out. The system resolver at 10.43.0.10 answered
the same public name in about 10ms. No tenant hostname or DNS token was used.

DEV policy permits DNS to kube-system, while public egress permits TCP443/6443,
not arbitrary public port53. Therefore TCP-only external DNS is not a suitable
fix for this deployment. These probes show reachability, not actual broker
duration; the instrumented deployment is still required to attribute the wait.

## Confirmed configuration gap

DEV already sets `ACME_DNS_LOOKUP_PREFER_SYSTEM=true` and
`ACME_DNS_LOOKUP_TIMEOUT_SECONDS=2`. Current CAP main does not consume either.
The broker always tries Cloudflare first and falls back to system DNS only on
error. Historical commit `6d04794` implemented similar tuning on an unmerged
internal branch; this is not evidence that current main previously supported it.

The candidate fix will honor the existing settings at startup, validate explicit
values, retain current external-first/native-timeout behavior when unset, and
bound each resolver lookup only when configured. Successful empty/wrong TXT
answers will not trigger resolver switching: exact token matching and ACME
validation remain mandatory. No network-policy widening or TLS/attestation
bypass is proposed. Candidate merge waits for the instrumented baseline.

[CAP #104](https://github.com/enclava-labs/cap/pull/104), head `00cc252`, implements
that candidate. All 452 API tests passed against a dedicated local database;
formatting and all-target clippy passed. Tests cover both resolver orders,
successful empty/mismatched answers, timeout/drop/fallback, outer cancellation,
strict settings parsing and non-disclosure of answer/error contents in timing.
Actual Devin CLI SWE-1.7 trace and Pi CLI GLM-5.3 review were used. Pre-existing
ACME cleanup/parser concerns were noted separately, not silently changed. Zero
propagation wait skips only the local visibility wait, not ACME validation.

## Instrumented baseline P

Normal-auth CLI completed successfully in **174.390 s**, and the runner observed
API running plus verified HTTPS by **178.944 s**. Bootstrap took 86.099 s,
ownership 0.925 s and managed-config wait 61.710 s. Worker evidence includes six
423 responses and one KDS429; those durations are separate from broker stages.

Exactly one broker request (pod `cap-api-b698456cb-pjwkp`, sequence1) completed:

| Nested broker phase | Duration / outcome |
| --- | --- |
| External DNS lookup | **15.003 s, error** |
| System DNS lookup | **0.034 s, success** |
| DNS visibility (encloses lookups) | 15.038 s, success |
| ACME order-ready | 1.082 s, success |
| ACME finalize | 0.853 s, success |
| Certificate retrieval | 0.538 s, success |
| Broker total (encloses all phases) | **19.573 s, success** |

This confirms an avoidable 15-second external lookup before the already-working
system resolver. It does not establish that DNS caused every earlier long init
interval. Exact-token matching and ACME validation still succeeded normally.

The subsequent real SSH check **failed with a connection reset before auth**,
after a default multi-key `ssh-keyscan` had recorded one host key. Cleanup then
ran, so this attempt cannot be retried on P and is not counted as SSH success.
Metadata shows one pod UID, zero restarts and continuous Ready after 20:20:02
until deletion. Template readiness checks the public banner, not authentication;
probe contention is only a hypothesis, not a diagnosed cause.

Normal destruction exited zero. At 20:23:54 UTC, authenticated lookup was404;
the exact namespace, PVs `pvc-caea7fd3-249a-4c0b-a514-1abb26325dde` and
`pvc-5f846cd9-1895-442e-919f-6b0939b94278`, and matching Longhorn volumes
were absent. Exact metadata/DB observers stopped. Repeat R started at20:23:56
on the same image, with a real SSH-first TOFU check followed by strict pinned
verification planned; it will be retained until verification finishes.

After full current-head CI/review and the DNS evidence, CAP #104 merged as
`bbcaa7b028b651c71842dfdba427e029ca634c98`. Signed release dispatch
`34057766213`, tag `manual-20260906-dev-acme-dns-settings`, is in progress.
The SSH uncertainty is being checked independently; this fix changes no relay
or SSH behavior. No fixed-image DEV speedup is claimed yet.

## Repeat R: baseline confirmation and SSH verification

R completed CLI in **188.505 s**, and API running/verified HTTPS by194.532s.
Bootstrap87.025s, ownership18.390s, managed wait57.222s. Its broker sequence2
independently repeated **15.003s failed external lookup**, then119ms successful
system lookup; broker total20.031s. The two baselines isolate the DNS floor
despite differing total/ownership times.

First real SSH used normal TOFU (`accept-new`, fresh private known-hosts file,
changed keys rejected) and passed without a preceding key scan. A second
connection passed with strict saved-host-key verification. One bounded broad
key-scan followed by another strict connection also passed. Thus the single P
reset did not reproduce; no server-limit or host-key policy change is justified.
TOFU is not an attestation-bound SSH host-key proof.

R was retained until all checks finished, then normal destruction exited zero.
At20:30:45 UTC authenticated lookup returned404; namespace, PVs
`pvc-754188e4-2251-4dc5-98fc-c666b62550a9` and
`pvc-7b9fb763-783e-486b-b6bd-718a7ac4ea3c`, and matching Longhorn volumes
were absent. The original canary still had its original UID, four ready
containers and zero restarts. R's exact metadata observer was stopped.

## Fixed-image rollout

Signed release `34057766213` completed successfully for source `bbcaa7b`.
The downloaded API digest is
`sha256:65f7f3796f04b4fa85ff6729453de65dc8f679a1ad097d94b1e9973d83cb281b`,
migration46. Official image-reference and exact main-workflow keyless signature
verification passed. Source/profile provenance uses the dispatch record and
artifact; optional cosign source annotations are not claimed.

[Ops #155](https://github.com/enclava-labs/enclava-ops-manifests/pull/155)
changed only the DEV API/Job image references, immutable Job name and README.
Existing DNS settings, logging directive, checksums, tenant/appraiser/PaaS pins,
network policy and trust roots stayed unchanged. Environment contracts, complete
DEV render, DEV server dry-run and contained authority/mTLS regressions passed.
All review/inline/issue comments were read; exact-head Devin review found no
issues. CI `34058902416` passed before exact-head merge as `fa4c149`.

Flux applied automatically. API pod `cap-api-769c698f48-72nxw`, UID
`bcbd7979-f813-4753-9dc4-94b74a981071`, is ready with zero restarts on the exact
digest. The new migration Job succeeded on the same digest. PaaS readiness
reports ten checks; the original canary remains unchanged. Normal-auth Q
started at20:49:20 UTC with the same CLI binary as P/R.

## Q: functional pass, no end-to-end speedup established

CLI completed in **199.814s**; API running and verified HTTPS were observed by
**204.164s**. Bootstrap86.034s, ownership18.423s, managed wait67.888s. Real SSH
passed on the first normal TOFU connection, then passed again with strict saved
host-key verification. The app was retained until both checks completed.

One broker request (new API pod, sequence1) showed the settings are honored:

| Nested broker phase | Q duration / outcome |
| --- | --- |
| System lookups 1–3 | 31ms / 18ms / 37ms, error |
| External fallback after each error | 2.001s / 2.002s / 2.001s, error |
| System lookup 4 | 121ms, success; no external fallback |
| DNS visibility, including retries | **21.217s, success** |
| Broker total | **25.910s, success** |

The previous single15.003s external timeout is gone, but early system errors
caused three bounded fallbacks plus three5s propagation sleeps. DNS visibility
was therefore about6.2s longer than P, not faster. Whole CLI was25.4s slower
than P and11.3s slower than R. This is a validated configuration/timeout fix,
**not a demonstrated deployment speedup**. One after-run cannot establish a
latency distribution or prove that resolver preference caused all variation.

The managed window was62.635s, with ten423 write responses and twoKDS429s.
These are separate observations, not additional time to sum onto broker total.
Bootstrap remained near86s; this change does not solve confidential VM startup.

Source follow-up found that the pinned DNS library represents NXDOMAIN/NODATA
as typed errors, and CAP currently turns every lookup error into a fallback.
The short system errors are consistent with negative DNS answers, but existing
timings cannot distinguish those from transport errors. Next: add a fixed,
content-free DNS error category (no names, records, raw errors or span fields)
and measure another fresh deployment. Only if confirmed, consider treating
strict NXDOMAIN/NODATA as an empty answer in the shared resolver adapter, while
retaining transport fallback, bounded retry, exact TXT matching and ACME
validation. Do not widen DNS egress, cache attestation, or lower security gates.

Normal destruction exited zero. At20:54:42 UTC authenticated lookup returned404;
the namespace, exact PVs `pvc-f8b3e017-5436-409c-bb7a-b4d1efd6a2f9` and
`pvc-e132317d-4e03-4401-8b6c-17795adabff2`, and matching Longhorn volumes
were absent. Exact metadata/DB observers were stopped; paired HTTPS observer
completed. Original canary UID, four ready containers and zero restarts remain
unchanged. PREPROD was not accessed or changed.
