---
sidebar_position: 1
---

# CAP Overview

CAP is the open-source Enclava control plane for running OCI images as confidential workloads on Kubernetes.

It contains:

| Component | Purpose |
| --- | --- |
| `enclava` CLI | Login, app setup, deploys, config, hosted templates, ownership, recovery, and status. |
| CAP API | Axum service for auth, apps, deployments, domains, workload artifacts, and orchestration. |
| CAP engine | Kubernetes manifest rendering, apply/watch/cleanup, and validation logic. |
| `enclava-init` | In-TEE sidecar for verification, encrypted state, TLS state, and readiness. |
| `enclava-wait-exec` | Wrapper that blocks app and ingress processes until `enclava-init` is ready. |
| Common crates | Shared descriptors, validation, image references, encoding, and crypto helpers. |

CAP is the right layer to study if you need to understand deployment descriptors, policy generation, runtime verification, or self-hosted control-plane operations.

## Normal manual flow

```bash
enclava login
enclava init
enclava create --signer-subject <cosign-subject>
enclava deploy --image <registry>/<image>@sha256:<digest>
enclava status
enclava key backup --out enclava-recovery.json
```

The image must be digest-pinned. The signer subject should match the identity that signs the image, such as a GitHub Actions keyless cosign subject.

## Hosted-template flow

CAP CLI also includes hosted template commands used by Enclava-hosted API mode:

```bash
enclava template list
enclava template deploy debian-ssh-frp --name shell \
  --ssh-public-key-file ~/.ssh/id_ed25519.pub
enclava template ssh-command --name shell --wait
```
