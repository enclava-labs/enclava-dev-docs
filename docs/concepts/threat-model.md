---
sidebar_position: 2
---

# Threat Model

Enclava is built for apps that need stronger protection from the infrastructure they run on than standard containers give.

## What Enclava protects against

- The cloud provider, host, or Enclava operators reading your app's memory.
- A compromised host getting your app's secrets by inspecting the running workload.
- Code being swapped at deploy time through a mutable image tag.
- Your config, secrets, or storage keys being released before the checks described in [How Enclava protects your app](./confidential-computing.md) pass.

## What it does not protect against

- Bugs in your application code that leak data, on purpose or by accident.
- Malicious code signed by an identity you authorized.
- Someone with legitimate access exporting secrets from inside your app.
- The infrastructure refusing to run your app (denial of service).

## How it fails

Enclava fails closed. If the image, its signer, the deployment record, your organization keyring, the runtime policy, or the attestation don't match, your app does not start and nothing secret is released to it.

In the console and the CLI, secrets you provide are never shown back in plaintext, and Enclava's own service credentials never reach your browser or your machine.
