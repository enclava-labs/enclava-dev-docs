---
sidebar_position: 1
---

# Confidential Computing

Confidential computing protects data while it is being processed. Traditional encryption protects data at rest and in transit; confidential computing adds hardware-backed isolation for data in use.

## Trusted execution environments

A trusted execution environment, or TEE, is an isolated execution context backed by CPU and platform security features. Enclava targets Kata confidential containers with AMD SEV-SNP. In this model, the workload runs in a lightweight VM-backed guest whose memory is encrypted and isolated from the host.

The practical goal is simple: the cluster can schedule and operate the workload, but the host should not be able to read tenant memory or silently change the trusted startup path without detection.

## Remote attestation

Remote attestation lets a client or control plane ask, "What code and configuration is actually running?" A TEE produces signed evidence about the guest and selected runtime data. Verifiers compare that evidence with expected measurements, policies, and deployment identity.

In Enclava, attestation material is part of the chain that decides whether runtime state, TLS material, and secrets are released to the workload.

## Policy-bound startup

CAP does not treat Kubernetes rollout as enough. A successful confidential deploy also binds together:

| Binding | Why it matters |
| --- | --- |
| Image digest | Prevents mutable tag substitution. |
| Image signer identity | Restricts who can publish deployable code. |
| Deployment descriptor | Captures the app, deploy ID, policy, image, and expected runtime claims. |
| Org keyring | Defines which local deployment keys are allowed to deploy. |
| Generated agent policy | Restricts what the guest agent and KBS can release. |
| Runtime attestation | Proves the guest startup context before secrets are released. |

## What confidential computing does not solve

Confidential computing is not a replacement for application security. It does not automatically fix bugs in your app, prevent intentional data disclosure by the app, or remove the need for access control, audit logs, dependency hygiene, and least-privilege networking.

Treat it as a strong isolation and verification layer around a well-engineered application.
