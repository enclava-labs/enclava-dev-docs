# Next deployment-speed investigation — 2026-09-06

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
`manual-20260906-dev-write-status1`. At this checkpoint it is still running:
no new digest has been promoted and no new live speed improvement is claimed.

## What the next run must distinguish

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
finalization also currently write one combined heartbeat snapshot consumed by
internal health, metrics and checkout readiness. A direct background-task move
would introduce competing snapshot writers and wallet contention.

A future split therefore needs explicit ownership of independently timestamped
health observations, unchanged consumer freshness/failure checks, lifecycle and
cancellation tests, and a tested contention policy. A try-lock only avoids
waiting to acquire an already-busy fence; it does not prevent a probe that already
holds the fence from delaying a later payment. No new table, background SDK
session, persistent wallet cache or scheduling change has been implemented.

## Next execution gates

1. Complete and verify the signed workflow-dispatch release, exact source binding,
   release profile, image index and SPDX evidence.
2. Promote only DEV through a reviewed ops PR based on `dev`, changing all PaaS
   image references and both immutable Job names. Prepared worktree:
   `/home/user/platform/wts/dev-write-status`; no manifest changes yet.
3. Run fresh normal-auth `speed-dev-0905g`. Use the versioned PaaS timing filter
   and analyzer. Check pipeline exit status: streaming output can be partial on
   failure. Keep metadata observation until public running and pod readiness,
   not merely CLI exit. Never collect customer pod logs.
4. Attribute early-write status and startup timing, then select the smallest
   causal optimization. Test actual SSH/HTTPS and normal deletion; verify exact
   disposable namespace/storage removal and preservation of the existing canary.

DEV normal-auth preflight and encrypted backup/isolated four-database restore
passed before this checkpoint. The backup is per-database logical snapshots,
not a coordinated full recovery point. No preprod environment access or changes.
This change-scoped verification is not an absolute confidentiality guarantee or
a declaration of full production readiness.

## Follow-up: simpler monitoring and fresh-app priorities

[PaaS PR91](https://github.com/enclava-labs/enclava-paas/pull/91), head
`92662a0`, implements startup-plus-30-second completion-relative monitoring in
the existing loop. No background task/table/session/cache was added. Skipped
checks preserve JSON and time; fresh observations use the existing PostgreSQL
heartbeat-start timestamp. Transaction checks, locks and two-minute freshness
predicates remain unchanged. Source is committed/pushed. Final-head CI/review and
DEV measurement remain pending; local DB, consumer, clippy and formatting checks
pass, with exact coverage recorded in the PR. PR90 release build34021138045 has
since completed successfully, but no new image was promoted during this follow-up.

A read-only check of the preserved DEV canary confirmed app and ingress readiness
initial delays of180 seconds and an init CPU limit of250m. The canary UID remains
`90f0d6c1-fab7-44ef-9cec-942ea1058efd`, all four containers ready, zero restarts.
These settings match CAP source defaults. Earlier identical readiness predicates
are a concrete next candidate, but no180-second user-latency saving is established:
measure first external HTTPS/SSH separately from declared rollout readiness.

Next fresh-app candidates: measure init phase/throttling before raising its bounded
CPU allowance; split47-second sandbox startup into volume attachment, runtime boot
and image pull/unpack; prefetch only verified immutable public artifacts into the
actual runtime cache if pulls are material. Never reuse tenant keys, decrypted
volumes, private-image plaintext or attested sessions. No CAP setting was changed.
