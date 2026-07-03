---
sidebar_position: 1
slug: /
---

# Enclava Developer Documentation

Enclava lets you deploy OCI applications as confidential workloads. The hosted PaaS gives teams a console, login, billing, hosted templates, and CLI approval flows. CAP is the open-source control plane underneath: CLI, API, Kubernetes manifest engine, and in-TEE runtime sidecar.

Use these docs when you want to run applications where infrastructure operators can schedule and observe the service, but cannot read runtime secrets, mounted state, or customer configuration released inside the trusted execution environment.

## What you can deploy

**Hosted templates** are the fastest path. Enclava PaaS currently exposes the `debian-ssh-frp` template for a persistent SSH endpoint backed by a confidential workload. The platform reserves a stable `host:port`, delivers your SSH public key through the workload config path, and renders the canonical SSH command.

**Custom OCI images** use CAP directly. You build and sign an image, pin it by digest, create an Enclava app, and deploy through the `enclava` CLI. CAP verifies image identity and deployment descriptors before rendering Kubernetes resources for the confidential runtime.

## Product boundaries

| Layer | What it owns |
| --- | --- |
| Enclava PaaS | Hosted console, ZITADEL login, CLI device approval, org views, billing, hosted API keys, support/admin flows, and hosted template orchestration. |
| CAP API | Authenticated app, deployment, domain, config, keyring, workload artifact, and deploy orchestration APIs. |
| CAP CLI | User-facing `enclava` commands for login, app setup, deploys, hosted templates, config, ownership, recovery, and status. |
| CAP engine | Kubernetes manifest rendering, policy artifacts, apply/watch/cleanup, and runtime validation. |
| `enclava-init` | In-TEE startup sidecar that verifies policy, opens encrypted state, prepares TLS material, and releases readiness only after checks pass. |

## How a deploy works

```text
developer
  -> Enclava CLI or hosted console
  -> Enclava PaaS, for hosted product flows
  -> CAP API
  -> CAP engine
  -> Kubernetes confidential runtime
  -> enclava-init inside the Kata guest
  -> application container
```

The application runs as an ordinary container from the developer's point of view, but startup is guarded by confidential-computing checks. CAP binds the image digest, signer identity, org keyring, generated policy, and runtime attestation material together before secrets or state become available.

## Start here

- [Quickstart](./getting-started/quickstart.md) explains the recommended path.
- [Hosted template deployment](./getting-started/hosted-template.md) shows the `debian-ssh-frp` flow.
- [Manual OCI deployment](./getting-started/manual-oci-deploy.md) shows the lower-level CAP flow.
- [Confidential computing concepts](./concepts/confidential-computing.md) explains the primitives behind the platform.
