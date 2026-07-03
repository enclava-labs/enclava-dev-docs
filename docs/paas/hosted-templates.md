---
sidebar_position: 3
---

# Hosted Templates

Hosted templates package common confidential workload shapes behind a stable interface. PaaS controls the template catalog and injects platform-managed config that users should not handle directly.

## Template lifecycle

```text
CLI template deploy
  -> PaaS validates user inputs
  -> PaaS reserves platform resources
  -> PaaS creates CAP app/deploy records
  -> Workload starts in confidential runtime
  -> CLI delivers short-lived config directly to the workload TEE endpoint
  -> PaaS and workload expose ready status
```

## `debian-ssh-frp`

The `debian-ssh-frp` template provides a confidential Debian SSH endpoint. PaaS allocates the stable endpoint on the Enclava FRP relay and returns the canonical command once the workload is ready.

```bash
enclava template deploy debian-ssh-frp --name shell \
  --ssh-public-key-file ~/.ssh/id_ed25519.pub
enclava template ssh-command --name shell --wait
```

## Fail-closed endpoint contract

PaaS stores the expected stable endpoint in template metadata. Browser and CLI clients read that stored endpoint and compare it with workload output. If the workload returns a malformed command, a different host, a padded value, or an unexpected username, the route rejects it instead of showing a possibly unsafe command.

## Production requirements

For production, operators must configure:

- A signed, digest-pinned `DEBIAN_SSH_FRP_IMAGE`.
- FRP relay configuration through `FRP_RELAY_*`.
- Readiness reporting with `frp_relay_configured=true`.
- Release checks that validate image references and endpoint consistency.
