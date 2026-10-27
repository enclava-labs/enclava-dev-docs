---
sidebar_position: 2
---

# Storage, Unlock and Recovery

Your app's persistent storage is encrypted, and the keys only exist inside your TEE. This page covers how that storage is unlocked, how to recover it, and what happens when you destroy an app.

## Unlock modes

`[unlock] mode` in `enclava.toml` controls how the encrypted volume is opened:

| Mode | Behavior |
| --- | --- |
| `password` (default) | On the first deploy you claim the app with a password. Every restart needs an unlock with the same password. |
| `auto` | The app unlocks itself on restart, but only after the TEE has passed attestation. Requires an existing password-mode claim. |

### Password mode

On the first claim, the TEE generates a random 32-byte owner seed. Your storage keys are derived from that seed, and the seed is stored wrapped under a key derived from your password (Argon2id plus HKDF). Enclava never sees the password or the seed. Password attempts are rate-limited.

Pass the password from a file so deploys can claim and unlock without a password prompt:

```bash
enclava deploy --image <image>@sha256:<digest> \
  --storage-password-file "$HOME/.enclava/my-app-storage-password"
```

The file flag makes the whole flow unattended, first claim included: the one-time recovery mnemonic is written to the protected local keystore (never shown) instead of being delivered to a terminal. Run `enclava key backup` right after the first deploy so the recovery material has a durable copy. Unlocks and redeploys run unattended with the file flags (a redeploy whose app's TEE ownership state cannot be read fails closed).

Or claim and unlock by hand:

```bash
enclava claim --app my-app
enclava unlock --app my-app
enclava change-password --app my-app
```

Password prompts go to stderr. If you capture output with `2>&1 | tee`, use the `--password-file` flags instead of the prompt.

### Auto-unlock

Auto-unlock stores a second wrapped copy of the owner seed that is only released to your app after the TEE passes attestation and policy checks. The app then restarts without anyone entering a password.

Because it wraps the existing seed, auto-unlock needs a password-mode claim first; `enclava create` rejects `auto` mode for a new app. Deploy in password mode, then enable it:

```bash
enclava auto-unlock enable --image <image>@sha256:<digest>
enclava auto-unlock disable --image <image>@sha256:<digest>
```

Auto-unlock is gated by attestation, not by TEE hardware sealing.

## Back up your recovery key

:::warning Do this right after the first deploy
Without a recovery backup, a lost storage password means your app's data can't be opened again.
:::

Export recovery material and keep it outside your repository:

```bash
enclava key backup --out "$HOME/.enclava/my-app-recovery.json"
enclava key status
enclava key restore <backup-file>
```

The recovery mnemonic is a BIP39 encoding of the owner seed, not a copy of your password. The CLI saves it to its protected local keystore at claim time and never prints it.

## Recover after a lost password

```bash
enclava recover --app my-app --mnemonic-file <file> --new-password-file <file>
```

`recover` rebuilds the owner seed from the mnemonic and wraps it under the new password.

:::note
Recovery only works against a freshly started app that is still locked. Against an app that has been running for a while it returns `recovery_requires_locked_init_verifier`.
:::

## Destroying an app

```bash
enclava destroy --app my-app
```

:::danger Destroy deletes your data
`destroy` deletes the app's data volumes. It also verifies that the confidential
workload teardown completed — the step that erases the wrapped owner seed from
the platform key store.
:::

If the workload teardown cannot complete (for example the workload is crashed or
unreachable), the destroy **does not finish**: the app stays in the deleting
state and stays wired, and the destroy remains retryable — run it again once the
workload is reachable.

If recovery is ruled out, finish the destroy with an explicit waiver:

```bash
enclava destroy --app my-app --force --abandon-teardown
```

If the teardown could not complete, the previous owner seed may remain in the
platform key store, and recreating an app with the **same name** is refused
(message as reported by the `enclava` CLI — the platform API's raw text is
phrased differently but carries the same remediation):

```
409 stale_owner_seed (a previous instance's teardown is incomplete: ask the
platform operator to erase the stale owner seed in KBS and clear the recorded
waiver, or choose a different app name)
```

The remedies are the two the message names: an operator erases the stale seed
and clears the recorded waiver, or you pick a different app name. If the
workload was already gone (or its teardown had completed), no waiver is recorded
and recreation is unaffected.
