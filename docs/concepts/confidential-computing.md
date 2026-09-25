---
sidebar_position: 1
---

# How Enclava Protects Your App

Encryption usually protects data at rest and in transit. Confidential computing also protects it while it's in use, by running your app in hardware-isolated memory that the host can't read.

<TeeDiagram />

## Trusted execution environments

A trusted execution environment (TEE) is an isolated execution context enforced by the CPU. Enclava runs every app in a lightweight virtual machine protected by AMD SEV-SNP: its memory is encrypted and isolated from the host.

Enclava can schedule, restart, and observe your app, but the host can't read its memory, and it can't change how the app starts without the change being detected.

## Remote attestation

Remote attestation answers the question "what code and configuration is actually running?" The TEE produces hardware-signed evidence about itself, which is checked against what you deployed.

In Enclava, attestation is what decides whether your app's storage keys, TLS certificates, and secrets are released to it.

## Checks before your app starts

A container that has started isn't trusted by default. Before your app gets its secrets or storage, Enclava checks that the following all match:

| Check | Why it matters |
| --- | --- |
| Image digest | Nobody can swap in different code behind a mutable tag. |
| Image signer | Only the identity you registered (for example your CI workflow) can publish deployable code. |
| Deployment record | The app, deploy, image, and expected runtime are signed together at deploy time. |
| Organization keyring | Only deployment keys your organization authorized can deploy. |
| Runtime policy | Limits what the TEE may do and what may be released to it. |
| Attestation | The hardware proves the TEE started the way the deployment record says it should. |

These checks run inside your TEE. If any of them fails, the app does not start and no secrets, storage, or TLS material are released. `enclava status` shows the reason as `tee_error`.

## Startup order

<Flow>

1. **The TEE starts** and runs Enclava's startup check, `enclava-init`.
2. **Everything is verified**: every check in the table above.
3. **Storage and TLS open**: your encrypted storage is unlocked and TLS is prepared.
4. **Your app container starts.**

</Flow>

Your app never runs in a state where the checks haven't passed.

## What confidential computing doesn't solve

Confidential computing is not a replacement for application security. It doesn't fix bugs in your app or stop your app from disclosing data on purpose. You still need access control, audit logs, dependency hygiene, and least-privilege networking. See the [security checklist](../guides/security-checklist.md).
