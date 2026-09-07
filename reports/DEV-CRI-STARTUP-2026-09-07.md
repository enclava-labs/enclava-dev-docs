# DEV container-start attribution — 2026-09-07

## Result

Four historical normal-auth deployments consistently spent **40–43 seconds
inside container starts**, concentrated in tools, app and init. This is the
larger optimization target, ahead of the few seconds of avoidable DNS fallback.
No runtime speedup is claimed yet.

The source changes are merged and signed release builds succeeded. The
optimization is **not yet enabled**: the compatible CAP reader is live on DEV,
but signer promotion and the fresh U comparison/persistence checks remain pending.

| CRI operation, seconds | P | R | Q | S |
| --- | ---: | ---: | ---: | ---: |
| RunPodSandbox | 11.028 | 10.889 | 10.963 | 11.199 |
| Start tools | 19.890 | 19.862 | 20.751 | 18.947 |
| Start web | 9.810 | 12.367 | 10.789 | 9.973 |
| Start proxy | 0.247 | 0.246 | 0.254 | 0.251 |
| Start ingress | 0.191 | 0.190 | 0.175 | 0.179 |
| Start init | 12.498 | 10.258 | 10.377 | 10.751 |

Every CreateContainer call took under 0.082s. In S, tools StartContainer
success preceded web CreateContainer by 2.373s. The earlier Kubernetes
scheduling→sandbox-ready condition interval (46–47s) is **not VM boot time**:
S RunPodSandbox completed at05:07:57.879, while the condition changed at05:08:17,
after tools startup. S scheduled at05:07:31 and RunPodSandbox began at05:07:46.680,
leaving about15.7s before that runtime call, including volume preparation.
Do not add condition intervals to their nested CRI operations.

### Baseline T, before optimization promotion

| CLI measurement | Seconds |
| --- | ---: |
| Observed total | 162.167546 |
| Emitted total | 161.020818 |
| Bootstrap wait | 79.987682 |
| Deploy request | 18.678269 |
| Ownership | 0.917058 |
| Managed-config wait | 49.437461 |

T's CRI durations were sandbox10.784s, tools20.380s, web9.387s,
proxy0.249s, ingress0.181s and init9.923s, reproducing the earlier startup
pattern. These nested measurements must not be added to CLI total time.
Normal-auth SSH passed both first-use TOFU and a repeat with strict saved-host-key
verification. T is retained healthy with pod UID
`94defae1-7c2d-4395-8fe9-303396bd1742`. This is an unoptimized baseline, not a
speedup measurement.

## Evidence and scope

`tools/dev-cri-timing.py` projects existing host journal JSON into timestamps,
fixed phase/boundary labels and five allowlisted container names. It binds
the exact disposable pod UID to sandbox ID, then container IDs, in memory.
It never exports IDs, raw messages/errors, images, specs, environment,
attestation evidence or tenant data. No debug logging, guest exec or workload
logs were enabled. Its runnable `--self-test` passed. Each historical P/R/Q/S
stream yielded22 records, zero malformed records, and one complete set of
paired lifecycle operations.

Private evidence: `speed-{p,r,q,s}-observers/cri.jsonl` under the existing private
rehearsal directory. Historical functional results and cleanup qualifications,
including P's unverified SSH outcome, remain in the preceding reports.

DEV worker versions: containerd1.7.30, k0s1.35.2+k0s.0, Kata3.28.0 source
`660e3bb6535b141c84430acb25b159857278d596`. The exact lifecycle message formats
come from [containerd's instrumented CRI service](https://github.com/containerd/containerd/blob/v1.7.30/pkg/cri/instrument/instrumented_service.go).

## Strongest source-backed hypothesis

Live DEV qemu-snp configuration has `emptydir_mode = "block-encrypted"`.
[Pinned Kata createEphemeralDisks](https://github.com/kata-containers/kata-containers/blob/660e3bb6535b141c84430acb25b159857278d596/src/runtime/virtcontainers/container.go)
creates an encrypted block volume for each newly encountered disk-backed
emptyDir; subsequent containers reuse it. CAP's first-use layout is:

- Tools: helper binary volume and log spool — two new disks.
- Web: decrypted app-storage mountpoint — one new disk.
- Proxy/ingress: reuse existing volumes.
- Init: decrypted TLS-storage mountpoint — one new disk, plus existing raw PVCs.

This matches the repeated roughly20/10/0/0/10s pattern. Read-only existence
checks on the preserved original canary confirmed four corresponding disk.img
files; no file contents were accessed. The setup subphases have not individually
been timed, so attributing every second specifically to encryption/KDF would
overstate the evidence.

Candidate: use guest-memory emptyDirs for the small helper volume and the two
mountpoint holders, retaining encrypted disk backing for logs and all actual
persistent data. Three avoided disk initializations suggest **roughly30s of
potential savings**, not a measured result or a guaranteed end-to-end gain.

## Safety requirements before promotion

- Preserve init-last. Historical CAP commit `be460db344a2a703aeba524c1673cfab47dc8e33`
  documented Kata EINVAL when later containers were created after LUKS mounts
  existed. Current init opens LUKS before waiting for workload sentinels.
- Preserve raw Block PVCs, KDF defaults, ownership, fresh attestation, signed
  policy enforcement, mount handoff and ready gating. Do not disable encrypted
  emptyDirs globally or put real app/TLS persistence on tmpfs.
- [Pinned Kata handleEphemeralStorage](https://github.com/kata-containers/kata-containers/blob/660e3bb6535b141c84430acb25b159857278d596/src/runtime/virtcontainers/kata_agent.go)
  maps memory emptyDirs to guest-local tmpfs, but forwards only the group option,
  not a per-volume size limit. A manifest sizeLimit must not be described as an
  enforced guest bound. Review memory/swap and mount behavior before claiming
  confidentiality or capacity guarantees.
- Test rendered manifests and existing policy/mount regressions, obtain PR
  review, then test a signed release with a fresh normal-auth DEV deployment,
  attested config delivery, verified HTTPS, first real SSH and strict repeat.
  Retain failed canaries; cleanup only after verified success.
- No PREPROD access/change, guest diagnostics or shared runtime tuning.

Actual Devin SWE-1.7 source tracing and Pi GLM-5.3 bounded reasoning review
were used; neither is a substitute for the planned live comparison.

## Implementation and coordinated policy change

[CAP #106](https://github.com/enclava-labs/cap/pull/106) implements the three
nonlegacy Memory volumes; [policy-templates #4](https://github.com/enclava-labs/policy-templates/pull/4)
mirrors them in the independent policy-generation manifest. Changing CAP alone
would mismatch strict generated storage policy. No policy normalization or
authorization relaxation is included. Both test suites now assert init-last.

Local CAP engine suite:296 passed,14 existing ignored; volume suite15 passed.
Restoring the old declarations makes exactly the two new Memory tests fail;
restoring the candidate returns green. Engine all-target clippy, formatting and
diff checks pass. Signing-service suite:59 library+7 binary tests passed;
all-target clippy and formatting pass. Actual Pi GLM-5.3 independent review
completed and found no proven changed-line defect; another attempt timed out
and is not approval. The reviewer correctly required the companion signer
change, init-last assertions, real generated-policy acceptance and storage
persistence/managed-config/TLS handoff checks.

The current digest-pinned init image's helper is12,463,272 bytes, measured in a
local read-only, network-disabled container with no tenant state. It fits the
declared16Mi helper volume. This is not evidence of guest limit enforcement.

Do not use signer-first rollout: the historical-policy compatibility fix below
requires the CAP reader first. Both components must be active before the fresh
optimized test. Engine drift checks are advisory, not automatic
StatefulSet reapplication. Preserve the original canary, which remains the same
UID with four ready containers and zero restarts. Coordinated DEV rollout and
live before-after validation remain pending; no PREPROD changes.

### Historical-policy compatibility: review finding and fix

CAP review comment3947382081 identified a real defect in the initial candidate:
retries, reclaimed `watching` jobs and rollback reuse stored signed policy text
while rendering with current engine code. An unconditional Memory switch would
break those historical policies even with both new services deployed.

The revised signer emits the exact first line
`# enclava-cap-volume-layout: guest-memory-v1` plus LF **before** hashing and
signing policy bytes. CAP selects Memory only from that exact prefix in the
verified stored generated policy. Historical/unmarked/missing policy, unsupported
markers, leading whitespace/BOM, CRLF and embedded lookalikes keep the old disk
layout. The CAP fallback and legacy path remain unchanged. No new request field,
host annotation or relaxed policy grants this selection.

The customer descriptor binds the expected policy hash; artifact signatures bind
that same hash. CAP validates stored authority before reconstructing retry or
rollback and hash-checks exact policy text before generating volumes. New tests
cover full-StatefulSet replay with old/new/no policy, marker tampering, strict
prefix matching and legacy behavior. CAP engine300 passed,14 existing ignored;
volume tests19 passed. Signer60 library+7 binary tests passed, including marker
emission and rejection after marker insertion even if unsigned hashes are
recomputed. Formatting, clippy and diff checks passed.

**Revised promotion order:** CAP compatibility reader first, signer emitter
second. This replaces the initial simultaneous-promotion assumption. Once new
marked artifacts exist, do not downgrade CAP below the compatible reader:
historical *application* rollback works, but an old *CAP binary* cannot render
the new layout. Signer-only rollback can stop new issuance while retaining the
compatible CAP reader. Both source PRs are now merged; fresh DEV/persistence
measurements are still required.

### Merged sources and release-build status

- CAP #106 merged at `230673207c0061834e654b238c226c4a4969ca9d`.
  [Signed release build 34096102055](https://github.com/enclava-labs/cap/actions/runs/34096102055)
  and [release CI 34096104261](https://github.com/enclava-labs/cap/actions/runs/34096104261)
  succeeded.
- Policy-templates #4 merged at `c7616753254e71812364bb49538a9ac37930ab63`.
  Signed tag `v0.1.0-dev-bootstrap-memory` has a successful
  [release build 34095716072](https://github.com/enclava-labs/policy-templates/actions/runs/34095716072).

[Ops #157](https://github.com/enclava-labs/enclava-ops-manifests/pull/157) merged
at `f85a5a9eaef696ef834f8ef2d148249787eaa0c9`. DEV CAP reader imageID matches
`sha256:7dffd3b0273e5d9af26b93c83c8ef2c35d5bc680dc931a892c9a9f056b078e58`;
the migration46 Job succeeded and Deployment is ready. Original canary and T
retain their exact pod UIDs, four ready containers and zero restarts. T verified
HTTPS200 and strict saved-host-key authenticated SSH pass after promotion.
PaaS readyz reports ten checks. Signer-only
[ops #158](https://github.com/enclava-labs/enclava-ops-manifests/pull/158) awaits
review/CI; fresh U and persistence verification remain pending. No speedup is claimed.
