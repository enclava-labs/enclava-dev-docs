---
sidebar_position: 3
---

# CLI Reference

The `enclava` CLI deploys and operates your apps on Enclava. Run `enclava <command> --help` for the current flags.

## Account and context

```bash
enclava login [--no-browser] [--org ORG] [--approve-logs] [--replace-session]
enclava whoami
enclava logout
```

`login` opens the console in your browser to approve the session. Use `--no-browser` to approve from another device, `--org` to scope the session to one organization, `--approve-logs` to let the session read app logs, and `--replace-session` to replace an already-saved session without the confirmation prompt. See [Console and CLI login](../guides/console.md).

## App lifecycle

```bash
enclava init [--app-name NAME] [--port PORT]  # generate enclava.toml (prompts when interactive)
enclava prepare [--yes]                       # write enclava.toml + CI signing workflow
enclava create [--image IMAGE] --signer-subject SUBJECT [--signer-issuer URL]
enclava deploy --image IMAGE@DIGEST [--set KEY=VALUE] [--set-file KEY=PATH] [--storage-password-file PATH]
enclava status [--app APP] [--json]
enclava logs [--app APP] [-f] [--log-private-key-file PATH]
enclava rollback [--to DEPLOYMENT_ID]
enclava destroy [--app APP] [--force] [--abandon-teardown]
```

`deploy` requires a digest-pinned image and local `enclava.toml`. `--storage-password-file` claims ownership on the first deploy (password mode) and unlocks on redeploys — unattended runs included: the one-time recovery mnemonic is saved to the protected local keystore instead of being shown (run `enclava key backup` right after the first deploy — see [Storage, unlock and recovery](../guides/storage-and-recovery.md)). `--set-file` delivers a secret from a file without exposing it in process arguments. `logs` requires a tenant-held log key created with `enclava log-key generate --app <app> --key-id <id>`. `--json` prints machine-readable output. `destroy` verifies the confidential workload teardown completed; `--abandon-teardown` finishes the destroy anyway when it cannot (records a waiver — same-name recreation is then refused `stale_owner_seed` until an operator erases the stale seed and clears the waiver).

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
enclava key setup --backup-out "$HOME/.enclava/org-signing-backup.json" [--passphrase-file PATH] [--new-passphrase-file PATH]  # create the org signing authority; required before a fresh org's first create
enclava key backup --out "$HOME/.enclava/my-app-recovery.json" [--new-passphrase-file PATH]
enclava key restore <backup-file> [--force] [--passphrase-file PATH]
```

Password-mode workloads protect state with owner-controlled material. `claim` and `unlock` run automatically when `deploy` is given `--storage-password-file`. Run the standalone commands to enter the password interactively, or pass their `--*-file` flags to run unattended — a first `claim` included: the one-time recovery mnemonic is written to the protected local keystore and never printed, so run `enclava key backup` right after. Password prompts are written to stderr, so if you capture output with `2>&1 | tee`, use the file flag instead of the prompt. Back up recovery material right after the first deploy. See [Storage, unlock and recovery](../guides/storage-and-recovery.md).

## Which commands need a terminal

Every interactive input has a flag alternative, and a command that would prompt in a
non-interactive session refuses with the exact flag it needs instead of blocking.

| Command | Interactive by default | Unattended path |
| --- | --- | --- |
| `init` | prompts for app name and port | `--app-name`/`--port`, or a non-interactive session (deterministic defaults) |
| `prepare` | confirms before overwriting existing files | `--yes` |
| `login` | browser approval of the device flow | `--no-browser` prints the URL and code; the approval itself stays a human step. `--replace-session` skips the "replace existing session?" confirmation (or run `enclava logout` first) |
| `key setup` | passphrase prompt | `--passphrase-file`/`--new-passphrase-file` (the `--backup-out` file is owner material — a person should choose where it goes) |
| first `deploy` / `claim` | prompts for the storage password | `--storage-password-file`/`--password-file`. The one-time recovery mnemonic is saved to the protected local keystore and never printed — run `enclava key backup` after |
| `unlock` / `recover` / `change-password` | password prompts | `--password-file`; `recover --mnemonic-file --new-password-file`; `change-password --current-password-file --new-password-file` |
| `rollback` | confirms the target deployment | `--to DEPLOYMENT_ID` |
| `destroy` | double confirmation (yes/no, then type the app name) | `--force` — deliberate, see below |

## Automation and agents

- **`--no-input` (or env `ENCLAVA_NO_INPUT=1`) makes every command behave as if
  there is no terminal**: prompts with safe defaults take them (`init`), everything
  else fails naming the flag that replaces the prompt — nothing ever stops waiting
  for input. Any value except a falsey one (empty, `0`, `f`, `false`, `n`, `no`,
  `off`) disables prompts.
- **Secrets come from files** (`--password-file`, `--storage-password-file`,
  `--set-file`, …), never from process arguments.
- **`enclava status --json`** for programmatic reads: a stable shape where `null`
  means "not verified", never a value that reads like a verified result.
- **Treat `destroy --force` as a deliberate destructive act.** `destroy` deletes the
  app's data volumes; the default double confirmation exists to stop accidents.
  Automation should pass `--force` only when a person explicitly asked for the
  deletion.

## Organizations and signer identity

```bash
enclava org
enclava signer set SUBJECT [--issuer URL] [--app APP]
enclava signer rotate SUBJECT [--confirmation-token TOKEN] [--issuer URL]
```

Enclava uses your organization keyring and the pinned signer identity to decide whether the local CLI key can deploy and whether an image was produced by an authorized identity. The signer subject is typically a GitHub Actions workflow reference or an email.
