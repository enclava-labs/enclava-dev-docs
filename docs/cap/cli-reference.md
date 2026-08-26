---
sidebar_position: 3
---

# CAP CLI Reference

The `enclava` CLI drives CAP and the hosted PaaS flows. Use `enclava <command> --help` to discover current flags; for executable or security-sensitive behavior, observed behavior and the current implementation are authoritative.

## Account and context

```bash
enclava login [--api-url URL] [--no-browser] [--org ORG] [--approve-logs]
enclava whoami
enclava logout
```

`login` defaults to the hosted browser device flow. Use `--api-url` to target a standalone CAP instance, `--no-browser` for headless approval, or `--org` to scope the session. `--approve-logs` grants the CLI session hosted workload-log access. Direct `signup`, `login --nostr`, and `login --email` use standalone CAP endpoints; hosted PaaS authentication uses the browser/device flow.

## App lifecycle

```bash
enclava init                                       # generate enclava.toml (interactive)
enclava prepare                                    # write enclava.toml + CI signing workflow
enclava create [--image IMAGE] --signer-subject SUBJECT [--signer-issuer URL]
enclava deploy --image IMAGE@DIGEST [--set KEY=VALUE] [--set-file KEY=PATH] [--storage-password-file PATH]
enclava status [--app APP]
enclava logs [--app APP] [-f] [--log-private-key-file PATH]
enclava rollback [--to DEPLOYMENT_ID]
enclava destroy [--app APP] [--force]
```

`deploy` requires a digest-pinned image and local `enclava.toml`. `--storage-password-file` claims ownership on first deploy (password mode) and unlocks during a manual OCI redeploy. `--set-file` delivers a secret from a file without exposing it in process arguments. `logs` requires a tenant-held log key created with `enclava log-key generate --app <app> --key-id <id>`.

## Config and secrets

```bash
enclava config set FEATURE_FLAG=enabled  # local enclava.toml only; no --app
enclava config get [--app APP]            # lists names, never plaintext values
enclava config unset KEY [--app APP]
```

Inline `config set` values may appear in process listings and shell history. Use
`deploy --set-file KEY=PATH` for sensitive values on manual OCI apps; hosted apps
currently have no `config set` path.

## Hosted templates

```bash
enclava template list
enclava template deploy debian-ssh-frp --name shell --ssh-public-key-file ~/.ssh/id_ed25519.pub
enclava template ssh-command --name shell --wait [--json]
```

`--json` prints machine-readable deployment and endpoint details. See [Hosted templates](../paas/hosted-templates.md).

## Ownership and recovery

```bash
enclava claim [--app APP]
enclava unlock [--app APP]
enclava recover [--app APP] [--mnemonic-file PATH] [--new-password-file PATH]
enclava change-password [--app APP]
enclava auto-unlock enable --image IMAGE@DIGEST   # manual OCI app; local enclava.toml
enclava auto-unlock disable --image IMAGE@DIGEST  # manual OCI app; local enclava.toml
enclava key status
enclava key backup --out "$HOME/.enclava/my-app-recovery.json"
enclava key restore <backup-file> [--force]
```

Password-mode workloads protect state with owner-controlled material. `claim` and `unlock` run automatically when `deploy` is given `--storage-password-file`; the standalone commands cover the interactive path. Back up recovery material right after the first deploy.

## Organizations and signer identity

```bash
enclava org
enclava signer set SUBJECT [--issuer URL] [--app APP]
enclava signer rotate SUBJECT [--confirmation-token TOKEN] [--issuer URL]
```

CAP uses org keyrings and the pinned signer identity to decide whether the local CLI key can deploy and whether an image was produced by an authorized identity. The signer subject is typically a GitHub Actions workflow reference or an email.
