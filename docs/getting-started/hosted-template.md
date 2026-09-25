---
sidebar_position: 2
---

# Deploy a Template

Templates are ready-made workloads maintained by Enclava. Enclava handles the runtime setup, the endpoint, and the platform-side configuration; you only provide your own inputs, such as an SSH key.

## Debian SSH machine

The `debian-ssh-frp` template deploys a confidential Debian machine that you reach over SSH through the Enclava relay.

```bash
enclava template list
enclava template deploy debian-ssh-frp --name shell \
  --ssh-public-key-file ~/.ssh/id_ed25519.pub
```

<Flow>

1. **Enclava checks your inputs** and reserves a stable SSH endpoint on its relay.
2. **The machine starts** inside a TEE and passes its startup checks.
3. **Your SSH key is delivered** by the CLI straight to the TEE.
4. **The SSH command is ready**, once the machine and Enclava agree on the endpoint.

</Flow>

You don't need any relay credentials.

## Get the SSH command

```bash
enclava template ssh-command --name shell --wait
```

The command looks like this:

```bash
ssh -p 20051 user@relay.enclava.me
```

The port is assigned to your machine and stays the same across restarts. The CLI and the console check the command the workload reports against the endpoint Enclava reserved; if they don't match, you get an error instead of a command, so you never connect to an unexpected host.

## What you provide and what Enclava provides

| Value | Provided by | Notes |
| --- | --- | --- |
| SSH public keys | You | Delivered straight to the workload inside the TEE. |
| Stable SSH endpoint | Enclava | Reserved on the relay; not secret. |
| Relay credentials | Enclava | Configured by the platform; you never handle them. |

Secret template inputs are never shown back to you in plaintext by the console or the CLI.

## Status

```bash
enclava status --app shell
enclava template ssh-command --name shell --wait --json
```

Use `--json` when you script around deploy status, endpoint readiness, or the SSH command.
