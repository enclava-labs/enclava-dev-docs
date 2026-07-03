---
sidebar_position: 2
---

# Threat Model

Enclava is designed for workloads that need stronger protection from infrastructure-level access than standard containers provide.

## In scope

- A cloud, cluster, or platform operator should not be able to read workload memory.
- A compromised host should not be able to obtain app secrets just by observing the pod.
- Mutable image tags should not allow code substitution at deploy time.
- Runtime config and storage unlock material should be released only after expected policy and attestation checks pass.
- Hosted PaaS browser flows should keep CAP credentials, billing provider keys, ZITADEL secrets, relay config, and Bitcoin processor secrets server-side.

## Out of scope

- Bugs in application code that intentionally or accidentally leak data.
- Malicious code signed by an authorized signer.
- A user who exports secrets from inside the workload.
- Denial of service by the underlying infrastructure.
- Incorrect production operator configuration outside CAP's startup and release-build safety gates.

## Design posture

CAP release builds reject debug bypass flags and insecure TEE modes. Platform images and workload images are expected to be digest-pinned. The in-TEE sidecar fails startup before seed release if descriptor, keyring, policy, or attestation checks do not match.

The hosted PaaS adds a product boundary: browser clients use same-origin PaaS APIs. The PaaS server talks to ZITADEL, Lago, CAP, relay systems, and payment infrastructure without exposing those service credentials to the browser.
