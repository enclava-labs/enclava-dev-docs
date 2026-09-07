# DEV container-start attribution — 2026-09-07

## Result

Four historical normal-auth deployments consistently spent **40–43 seconds
inside container starts**, concentrated in tools, app and init. This is the
larger optimization target, ahead of the few seconds of avoidable DNS fallback.
No runtime speedup is claimed yet.

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
