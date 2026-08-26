---
sidebar_position: 4
---

# Runtime Verification

Runtime verification is the CAP path that prevents a Kubernetes rollout from becoming a secret-release event by itself.

## Verification chain

When policy-read mode is enabled, `enclava-init` verifies:

1. `cc_init_data` hash committed by the deployment descriptor.
2. Descriptor signature and descriptor core hash.
3. Organization keyring membership and deploy authority.
4. Generated agent policy hash.
5. Signed policy artifact and rendered Trustee policy.
6. Runtime identity and artifact bindings.

Any mismatch fails startup before seeds, mounted state, or TLS material are released.

## Storage modes

At the first password-mode claim, the in-guest proxy generates a random 32-byte owner seed. Argon2id plus HKDF derive a password wrapping key; that key encrypts the seed stored through KBS, while the volume keys derive from the owner seed itself. Password attempts arrive over the local unlock socket and are rate-limited.

Auto-unlock stores a separate encrypted seed envelope and fetches it through the local Kata confidential-data-hub resource endpoint only after KBS attestation and policy checks. It still runs the same verification path before using the seed. Auto-unlock therefore assumes an owner seed established by a prior password-mode claim; current `enclava create` rejects auto mode before a first deploy. Use password mode first, then `enclava auto-unlock enable --image <image@digest>` to create the KBS-attestation-gated wrap for restarts. This is not VMPCK or other TEE hardware sealing.

## Recovery and stale escrow

The recovery mnemonic (BIP39, shown once at claim) is an independent representation
of the owner seed — it is not a copy of the password.
`enclava recover --app <app> --mnemonic-file <file> --new-password-file <file>`
reconstructs that seed and wraps it under a new password. Two operational rules:

- **Recovery requires a freshly-booted *locked* TEE.** Against a long-running pod it
  returns `recovery_requires_locked_init_verifier` — restart the pod (delete it; the
  StatefulSet recreates it) and retry.
- **`destroy` only clears the KBS escrow if the pod is alive.** The in-guest proxy
  deletes the escrow on teardown, best-effort. If the app was already dead when you
  destroyed it, the escrow survives — and a newly created app with the same name
  **inherits it**: claim returns `already_claimed`, and every unlock lands as a silent
  wrong-password (`state=locked`, `error=null`). The failure signature is a
  `seed-encrypted` KBS fetch seconds after pod start, before any claim. Fix: recover
  with the *old* app's mnemonic, which still matches the surviving envelope.

Data volumes (PVCs) are deleted by destroy regardless of pod health — only the key
material survives, so a recreated app starts with empty storage unlocked by old keys.

## Readiness handoff

The generated runtime uses:

| Path | Purpose |
| --- | --- |
| `/dev/csi0` | App-data block device. |
| `/dev/csi1` | TLS-state block device. |
| `/run/enclava-unlock/unlock.sock` | Password unlock handoff. |
| `/run/enclava/init-ready` | Readiness signal consumed by `enclava-wait-exec`. |

App and ingress processes should not start before `/run/enclava/init-ready` exists.
