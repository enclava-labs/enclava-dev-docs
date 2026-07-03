---
sidebar_position: 2
---

# CAP Architecture

CAP turns a signed deployment request into confidential Kubernetes resources and in-TEE runtime state.

```text
CLI
  -> CAP API
    -> PostgreSQL
    -> platform release verification
    -> registry metadata and cosign checks
    -> Trustee/KBS and policy signing services
    -> CAP engine
      -> Kubernetes resources
        -> Kata confidential container guest
          -> enclava-init
          -> app container
```

## API service

The API is a stateless HTTP service backed by PostgreSQL. At startup it loads signing and session material, runs migrations, verifies platform release material when policy-read mode is enabled, and configures integrations such as DNS, Trustee/KBS, policy signing, registry access, and tenant TEE clients.

## Engine

The engine renders Kubernetes manifests for the tenant workload. It is responsible for the sidecars, runtime class, generated policies, storage and TLS state wiring, ingress, and apply/watch behavior.

## Platform release

The CLI and API load a signed platform release. Release verification checks the envelope signature, digest-pinned platform sidecars, Trustee KBS URL, genpolicy version, policy template hash, and expected runtime class. Explicit environment overrides must match signed release values when the release supplies them.

## In-TEE sidecar

`enclava-init` runs inside the guest. It verifies the runtime trust chain, opens encrypted app and TLS volumes, fetches workload artifacts and policy material, and only then signals readiness.
