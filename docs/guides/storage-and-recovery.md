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

Pass the password from a file so deploys can claim and unlock without a prompt:

```bash
enclava deploy --image <image>@sha256:<digest> \
  --storage-password-file "$HOME/.enclava/my-app-storage-password"
```

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
`destroy` always deletes the app's data volumes. The stored, wrapped owner seed is only cleaned up if the app is still running when you destroy it.
:::

If you destroy an app that was already stopped or crashed, that key material survives, and a new app with the same name inherits it. You'll see this as:

- `enclava claim` returns `already_claimed`, and
- every unlock fails as if the password were wrong.

To fix it, run `enclava recover` with the **old** app's mnemonic, which still matches the surviving key material. The new app starts with empty storage either way; only the keys carry over.
