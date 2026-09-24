---
sidebar_position: 4
---

# Runtime Verification

A successful Kubernetes rollout is not enough to release secrets. Seeds, mounted state, and TLS material become available only after `enclava-init` passes the checks below.

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

The recovery mnemonic is a BIP39 encoding of the owner seed, not a copy of the password.
It is saved to the protected local keystore at claim time and never printed.
`enclava recover --app <app> --mnemonic-file <file> --new-password-file <file>`
reconstructs the seed and wraps it under a new password. Two rules apply:

- **Recovery requires a freshly booted, locked TEE.** Against a long-running pod it
  returns `recovery_requires_locked_init_verifier`. Delete the pod so the StatefulSet
  recreates it, then retry.
- **`destroy` clears the KBS escrow only if the pod is alive.** The in-guest proxy
  deletes the escrow on teardown, best-effort. If the app was already dead when you
  destroyed it, the escrow survives, and a new app with the same name inherits it.
  Claim then returns `already_claimed`, and every unlock fails as a silent wrong
  password (`state=locked`, `error=null`). You can spot this case by a `seed-encrypted`
  KBS fetch a few seconds after pod start, before any claim. To fix it, recover with
  the old app's mnemonic, which still matches the surviving envelope.

`destroy` deletes data volumes (PVCs) whether or not the pod is healthy. Only the key
material can survive, so a recreated app starts with empty storage unlocked by the old keys.

## Readiness handoff

The generated runtime uses:

| Path | Purpose |
| --- | --- |
| `/dev/csi0` | App-data block device. |
| `/dev/csi1` | TLS-state block device. |
| `/run/enclava-unlock/unlock.sock` | Password unlock handoff. |
| `/run/enclava/init-ready` | Readiness signal consumed by `enclava-wait-exec`. |

`enclava-wait-exec` keeps app and ingress processes from starting until `/run/enclava/init-ready` exists.
