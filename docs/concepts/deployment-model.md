---
sidebar_position: 3
---

# Deployment Model

Enclava separates the product experience from the confidential workload control plane.

## Hosted mode

```text
browser or CLI
  -> Enclava PaaS
  -> CAP API
  -> Kubernetes confidential runtime
```

Hosted mode is the default for most users. It gives you account login, organizations, billing, hosted API keys, CLI device approval, and hosted templates.

## CAP mode

```text
enclava CLI
  -> CAP API
  -> CAP engine
  -> Kubernetes confidential runtime
```

CAP mode is the lower-level control plane path. It is useful for developing runtime features, integrating with your own platform services, or operating a self-hosted control plane.

## Runtime path

Inside the deployed pod, Enclava uses sidecars and a readiness handoff:

- `enclava-init` runs inside the Kata guest.
- It verifies the deployment trust chain and opens encrypted state.
- It prepares TLS state where configured.
- It writes `/run/enclava/init-ready`.
- `enclava-wait-exec` blocks app and ingress processes until the ready file exists.

This means the app container starts only after the confidential startup path has completed.
