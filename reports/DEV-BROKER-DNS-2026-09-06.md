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
