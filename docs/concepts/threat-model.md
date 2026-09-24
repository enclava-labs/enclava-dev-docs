---
sidebar_position: 2
---

# Threat Model

Enclava is designed for workloads that need stronger protection from infrastructure-level access than standard containers provide.

## In scope

Enclava is built to prevent the following:

- A cloud, cluster, or platform operator reading workload memory.
- A compromised host obtaining app secrets by observing the pod.
- Code substitution at deploy time through mutable image tags.
- Release of runtime config or storage unlock material before policy and attestation checks pass.
- Exposure of CAP credentials, billing provider keys, ZITADEL secrets, relay config, or Bitcoin processor secrets to the browser in hosted PaaS flows.

## Out of scope

- Bugs in application code that intentionally or accidentally leak data.
- Malicious code signed by an authorized signer.
- A user who exports secrets from inside the workload.
- Denial of service by the underlying infrastructure.
- Incorrect production operator configuration outside CAP's startup and release-build safety gates.

## Design posture

CAP release builds reject debug bypass flags and insecure TEE modes. Platform and workload images must be pinned by digest. The in-TEE sidecar fails startup before seed release if descriptor, keyring, policy, or attestation checks do not match.

The hosted PaaS adds a product boundary: browser clients use same-origin PaaS APIs. The PaaS server talks to ZITADEL, Lago, CAP, relay systems, and payment infrastructure without exposing those service credentials to the browser.
