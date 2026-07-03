---
sidebar_position: 2
---

# Deploy a Hosted Template

Hosted templates are curated workload definitions exposed by Enclava PaaS. They are useful when Enclava can manage the runtime shape, sidecars, stable endpoint allocation, and config metadata for you.

## Debian SSH over FRP

The supported SSH endpoint template is `debian-ssh-frp`. It deploys a Debian workload with SSH access through the Enclava FRP relay.

```bash
enclava template list
enclava template deploy debian-ssh-frp --name shell \
  --ssh-public-key-file ~/.ssh/id_ed25519.pub
```

PaaS reserves a stable endpoint on the Enclava relay, stores that non-secret endpoint metadata, and delivers SSH authorized keys through the workload config flow. Users do not provide relay credentials.

## Get the SSH command

```bash
enclava template ssh-command --name shell --wait
```

The command has this canonical shape:

```bash
ssh -p 20051 user@relay.enclava.me
```

The exact port is allocated by PaaS. Browser, CLI, and workload output are expected to agree on the stored `stable_ssh_endpoint`; the platform fails closed if the command is missing or non-canonical.

## Template config model

Templates publish metadata for inputs such as labels, descriptions, whether a key is required, whether it is secret, and whether it is platform generated. Plaintext secret values are not stored in PaaS responses.

For the SSH template:

| Value | Owner | Notes |
| --- | --- | --- |
| SSH public keys | User | Delivered to the workload through the short-lived config-token path. |
| Stable SSH endpoint | PaaS | Reserved on the FRP relay and stored as non-secret metadata. |
| FRP relay credentials | PaaS | Injected from platform-controlled relay configuration. |

## Status

```bash
enclava status --app shell
enclava template ssh-command --name shell --wait --json
```

Use JSON output when scripting around deployment status, endpoint readiness, or command handoff.
