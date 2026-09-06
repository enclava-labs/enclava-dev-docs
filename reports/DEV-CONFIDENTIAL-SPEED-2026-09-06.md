# Confidential deployment-speed improvements — 2026-09-06

## Status

Implementation and local regression testing complete. Independent change-scoped
security audit: seven declared mitigations verified, no open implementation gaps.
[PaaS PR89](https://github.com/enclava-labs/enclava-paas/pull/89) merged at06:23:21 UTC,
source `e8928dc82edfcd8a674ad6f201809cceead43056`, tree-identical to reviewed/tested
head `0231cc5d757504e0452129b8c541ccb29f8bcbfe`.
DEV promotion and a real-user benchmark passed. CLI time202.832s versus232.763s
previously (12.9% reduction). SSH/HTTPS and subsequent CAP/PaaS healthy identity
checks passed; disposable app/storage cleanup and preserved-canary checks passed.
Preprod has not been accessed or changed. This does not close every remaining
latency issue or establish full production-ceremony readiness.

Initial PR head2530df0 passed all CI. Review5124417618 prompted a shared URL-guard
fix in0231cc5: canonical IPv4/IPv6/mapped loopback and localhost. forms now reject.
56 config/managed tests, fmt and clippy passed; independent narrow re-audit passed.
Other review suggestions were explicitly assessed on the PR. Exact revised-head CI
passed. Fresh encrypted DEV backup/isolated four-database restore passed at
`dev-postgres-Z20HAqfy/restore-qvv9sMWw` (private; per-DB logical snapshots, not a
coordinated full recovery point).

Signed release run34016360444 passed, tag `manual-20260906-dev-confidential1`.
Index `sha256:d013f62d792117204f8d67cb14ea2a7f604312d903f3304df7c2537936fffd1c`
verifies against exact workflow/main/dispatch/source/release annotations. Native
SPDX2.3 document read from signed index:89 packages. linux/amd64 child
`sha256:ab8bf3da338292783554f70a509fef2c0a5e0a59b1f93deec416adbf1119aa64`.
Migration remains102.

[DEV ops PR150](https://github.com/enclava-labs/enclava-ops-manifests/pull/150)
merged at06:41:31 UTC as `71aba95411e5e38f5a0a612b0ddde09434017b48`, tree-identical
to final head `5dd45c4df7553f4a4ab68afc81a165af8e0c4c96`; exact-head CI passed.
All current review/inline/issue comments assessed. Eleven-resource server dry run passed, with no other
rendered resource changes except replacement of two immutable PaaS Jobs.
Initial CI caught an obsolete optional host-nginx check: runner nginx lacked
ssl_certificate_cache. Test-only commit5dd45c4 removes that redundant check;
mandatory nginx -t and full TLS/rotation/leakage tests still use the pinned image.
Fresh local runtime rerun passed. Independent Devin CLI review approved the
manifest/runtime changes; no deployment manifest changed after dry run.
DEV Flux applied that revision. Both PaaS API replicas and worker imageIDs match
the signed index; both new Jobs completed; relay imageID matches its pin and
certificate Ready is true. Public readyz10/10 passed. API/worker/relay pod UIDs
and zero restart counts remained unchanged throughout the benchmark.

## Changes and confidentiality boundaries

- Successful worker iterations now subtract work time from the configured interval.
  Fresh health probes, authority/fencing, batching, shutdown and failure backoff stay.
  This targets the 40.009s of worker sleep observed during run E's delivery window.
- General PaaS KDS transport now requires HTTPS in every environment, with optional
  public CA roots scoped to that client. Invalid TLS and redirects fail closed.
- DEV relay adds authenticated TLS8443, native rotating certificate loading, a
  bounded RAM collateral cache and removal of incoming headers/body before AMD.
- Relay diagnostics export only nine fixed timing/status fields. Request URIs,
  hardware IDs, headers, bodies, caller addresses and secrets are not logged.
- Every attestation remains fresh and independently verifies pinned AMD roots,
  validity, signed report and nonce/TLS/receipt binding. No verdict/session cache.

Local tests cover valid and invalid TLS, certificate rotation without restart,
malformed traffic/log sentinels, no stale response on upstream failure, query-sensitive
cache identity, tmpfs and absence of private header/body material in cache. Full
Rust/DB/CLI/stable-SSH and frontend tests pass. The original stable-SSH local file
permission failure was corrected and rerun with a fresh DB, not ignored.

## Limits

This is not an absolute confidentiality guarantee, whole-platform audit or completed
production ceremony. Trusted relay/node operators can see public collateral lookup
metadata in memory; existing legacy HTTP consumers are unchanged. Root-CA rollover
coordination is not introduced. Relay Ready uses TCP8080, so live TLS8443 must be
verified separately by the actual attested PaaS delivery path.

## Baseline and acceptance

Run E: CLI232.763s; managed wait119.289s; first claim to delivered112.322s;
KDS40.805s (including cancelled sessions); worker sleep40.009s; health23.188s.
These nested/overlapping durations must not be added. Earlier run D:365.160s.

The run used fresh `speed-dev-0905f`, existing normal aljaz@ceru.si authentication,
strict timing filters, real SSH and HTTPS, then normal CLI deletion and exact storage
cleanup. Preserve `ssh-dev-relay-canary-0`, UID
`90f0d6c1-fab7-44ef-9cec-942ea1058efd`, four ready containers and zero restarts.
Read-only preflight at06:01:28 UTC passed and preserved canary identity was unchanged.

## Live result — F

Started06:43:32.178065 UTC. CLI monotonic202832.426582ms, exit0;
wrapper204188.164561ms includes polling tail and is not the benchmark duration.
Managed event `e03a8ff0-a2bc-4e63-8af5-e95461f665d3` was first claimed06:45:25.782224
and delivered06:46:48.012448. No other active managed-config event was observed
before enqueue; one new worker process was followed throughout.

| Measurement | E | F |
| --- | ---: | ---: |
| CLI total | 232.763s | 202.832s |
| Bootstrap wait | 86.100s | 89.051s |
| Managed-config wait | 119.289s | 86.353s |
| First claim → delivered | 112.322s | 82.230s |
| KDS fetch including retries/cancellations | 40.805s | 9.187s |
| Worker sleep in delivery window | 40.009s /8 waits | 14.768s /15 waits |
| Worker health refresh in delivery window | 23.188s /8 refreshes | 44.407s /15 refreshes |
| Outbox passes in window | 9 | 16 |
| Sandbox scheduled → ready to start containers | 47s | 47s |

Nested timings overlap: never sum table rows. This single run is not an SLO or
causal isolation of each change. KDS behavior and the number of failed early TEE
writes differed, so the29.930s total gain cannot all be attributed to worker cadence.
The cadence change itself is visible: median successful inter-tick sleep1.000s,
maximum1.475s, instead of an unconditional5s. More health refreshes explain why
health's aggregate grew; none were skipped. The current worker instance had zero
consecutive failures, and557 DB samples (max gap0.501489s) saw no Lock waits.
Historical worker_heartbeat rows must not be mistaken for live worker failures.

Actual PaaS-to-relay TLS8443 produced24 bounded records: two429 MISS, one200 MISS,
21 subsequent200 HIT. Cold upstream connect times0.319–0.328s, response times
0.423–0.456s. HIT request time rounded to0.000s (not a claim of literally zero
latency). PaaS recorded22 successful fresh attestation sessions,22 successful
collateral responses and two429s; no cancelled KDS sessions this time. Retry sleep
was7.002s, nested within fetch. F does not explain E's earlier no-response stalls.

All13 successful TEE writes totaled0.202s, with fresh authority fencing and CAP
metadata sync. Before that, nine stage0 writes returned HTTP errors at06:45:34.272
through06:46:12.691; the first successful write was06:46:17.784 (attempt10).
That43.511s first-rejection-to-success window is now a concrete remaining target.
Existing timing categories retain only `http_status`, not the numeric response or
reason: do not label these401/409/readiness/ownership failures without evidence.

Real SSH on relay.enclava.me:31008 returned Linux/user; HTTPS healthz returned200.
SSH used a new private known_hosts file and strict checking after first keyscan;
this is TOFU, not attestation-bound host-key proof. API polling before CLI exit
observed83 HTTP200, one initial404 and two transport-status0 samples, but no
`running` sample. Later capture at06:48:41 verified both CAP and PaaS healthy/running
and successful tunnel proxying. Thus202.832s is CLI completion, not measured time
to every control-plane readiness signal. No customer pod logs were collected.

Normal CLI destroy exited0. At06:50:48 the app returned authenticated404 and its
exact namespace, two captured PVs and corresponding Longhorn volumes were absent.
This intentionally deletes the disposable workload/data; encrypted pre-rollout
platform backup is retained privately, but is not a backup of this later test app.
The preserved canary retained UID90f0d6c1-fab7-44ef-9cec-942ea1058efd, four ready
containers and zero restarts. Only this run's two DB observers/log streams stopped;
their expected termination exit codes are not application failures.

## Next actions, in priority order

1. Add a bounded numeric HTTP-status field to the managed-write measurement and
   a fixed rejection-reason enum if the protocol provides one safely; never log
   response bodies, tokens or config values. Trace the first-write gate before
   changing any retry/auth behavior. Reproduce with normal auth and fresh attestation.
2. Separate payment-health scheduling from delivery only with explicit preservation
   of observation timestamps, quote freshness, lease/fence and payment-receive gates.
   44.407s was spent in15 refreshes (27.138s sync/list,16.409s readiness); do not simply
   cache a healthy verdict or advance integration_checked_at using stale evidence.
3. Keep observers until public `running` and pod readiness, not merely CLI exit,
   to measure status convergence. Sandbox startup remains47s; investigate metadata
   phases without pod-log access, attestation shortcuts or weakening TEE policy.

Evidence prefix: DEV-CONFIDENTIAL-F-* (DB, worker, strict timing streams, API,
analyses, startup metadata and retirement capture). Before/after pod and preserved
canary snapshots are DEV-CONFIDENTIAL-{PODS,RELAY,CANARY}-*. Signed release proof
is under release-20260906-dev-confidential/paas/.
