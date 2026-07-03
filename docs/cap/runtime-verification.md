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

Password mode receives the owner password over the local unlock socket, rate-limits failed attempts, derives the owner seed with Argon2id, and supports recovery flows.

Auto-unlock mode fetches wrap material through the local Kata confidential-data-hub resource endpoint. It still runs the same verification path before seed release.

## Readiness handoff

The generated runtime uses:

| Path | Purpose |
| --- | --- |
| `/dev/csi0` | App-data block device. |
| `/dev/csi1` | TLS-state block device. |
| `/run/enclava-unlock/unlock.sock` | Password unlock handoff. |
| `/run/enclava/init-ready` | Readiness signal consumed by `enclava-wait-exec`. |

App and ingress processes should not start before `/run/enclava/init-ready` exists.
