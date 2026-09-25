---
sidebar_position: 3
---

# CLI Reference

The `enclava` CLI deploys and operates your apps on Enclava. Run `enclava <command> --help` for the current flags.

## Account and context

```bash
enclava login [--no-browser] [--org ORG] [--approve-logs]
enclava whoami
enclava logout
```

`login` opens the console in your browser to approve the session. Use `--no-browser` to approve from another device, `--org` to scope the session to one organization, and `--approve-logs` to let the session read app logs. See [Console and CLI login](../guides/console.md).

## App lifecycle

```bash
enclava init [--app-name NAME] [--port PORT]  # generate enclava.toml (prompts when interactive)
enclava prepare [--yes]                       # write enclava.toml + CI signing workflow
enclava create [--image IMAGE] --signer-subject SUBJECT [--signer-issuer URL]
enclava deploy --image IMAGE@DIGEST [--set KEY=VALUE] [--set-file KEY=PATH] [--storage-password-file PATH]
enclava status [--app APP]
enclava logs [--app APP] [-f] [--log-private-key-file PATH]
enclava rollback [--to DEPLOYMENT_ID]
enclava destroy [--app APP] [--force]
```

`deploy` requires a digest-pinned image and local `enclava.toml`. `--storage-password-file` claims ownership on the first deploy (password mode) and unlocks on redeploys. `--set-file` delivers a secret from a file without exposing it in process arguments. `logs` requires a tenant-held log key created with `enclava log-key generate --app <app> --key-id <id>`.

## Config and secrets

```bash
enclava config set FEATURE_FLAG=enabled  # local enclava.toml only; no --app
enclava config get [--app APP]            # lists names, never plaintext values
enclava config unset KEY [--app APP]
```

Inline `config set` values may appear in process listings and shell history. Use
`deploy --set-file KEY=PATH` for sensitive values. Template apps currently have no
`config set` path.

## Templates

```bash
enclava template list
enclava template deploy debian-ssh-frp --name shell --ssh-public-key-file ~/.ssh/id_ed25519.pub
enclava template ssh-command --name shell --wait [--json]
```

`--json` prints machine-readable deployment and endpoint details. See [Deploy a template](../getting-started/hosted-template.md).

## Ownership and recovery

```bash
enclava claim [--app APP] [--password-file PATH]
enclava unlock [--app APP] [--password-file PATH]
enclava recover [--app APP] [--mnemonic-file PATH] [--new-password-file PATH]
enclava change-password [--app APP] [--current-password-file PATH] [--new-password-file PATH]
enclava auto-unlock enable --image IMAGE@DIGEST [--password-file PATH]   # needs local enclava.toml
enclava auto-unlock disable --image IMAGE@DIGEST [--password-file PATH]  # needs local enclava.toml
enclava key status
enclava key backup --out "$HOME/.enclava/my-app-recovery.json" [--new-passphrase-file PATH]
enclava key restore <backup-file> [--force] [--passphrase-file PATH]
```

Password-mode workloads protect state with owner-controlled material. `claim` and `unlock` run automatically when `deploy` is given `--storage-password-file`. Run the standalone commands to enter the password interactively, or pass their `--*-file` flags in scripts. Password prompts are written to stderr, so if you capture output with `2>&1 | tee`, use the file flag instead of the prompt. Back up recovery material right after the first deploy. See [Storage, unlock and recovery](../guides/storage-and-recovery.md).

## Organizations and signer identity

```bash
enclava org
enclava signer set SUBJECT [--issuer URL] [--app APP]
enclava signer rotate SUBJECT [--confirmation-token TOKEN] [--issuer URL]
```

Enclava uses your organization keyring and the pinned signer identity to decide whether the local CLI key can deploy and whether an image was produced by an authorized identity. The signer subject is typically a GitHub Actions workflow reference or an email.
