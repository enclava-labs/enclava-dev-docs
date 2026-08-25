---
name: enclava
description: Deploy, operate, and troubleshoot apps on Enclava (confidential workloads on Kubernetes with AMD SEV-SNP). Use this skill whenever the user mentions enclava, deploying an OCI image or hosted template to enclava, `enclava` CLI commands, app status/logs/config, unlock/locked storage, recovery mnemonics, auto-unlock, rollback/destroy, signer identity, or a failed/stuck enclava deploy — even if they don't say "enclava" explicitly but are clearly working against this platform.
compatibility: enclava CLI v0.1.x
---

# Running apps on Enclava

Enclava runs container images as **confidential workloads**: a Kata VM-backed guest
(AMD SEV-SNP) where the host can schedule and operate the workload but cannot read its
memory or silently alter its trusted startup path. Secrets and encrypted state are
released *inside* the guest only after image-signature, policy, and attestation checks
pass. Everything a user does goes through the `enclava` CLI (or the hosted console).

Run `enclava <command> --help` for the authoritative flag list — it wins over any
example in this skill if they ever disagree.

## The model in five facts

1. **Apps are created from `enclava.toml`** (`enclava init` scaffolds it) and deployed
   with **digest-pinned images** (`image@sha256:<digest>`). Mutable tags are rejected.
2. **Images must be cosign-signed**, and the signer identity is pinned per app
   (`--signer-subject` at create, or `enclava signer set` later). Keyless GitHub
   Actions signing is the intended path.
3. **Persistent storage is encrypted** (LUKS inside the guest). In password mode the
   owner holds a password and a BIP39 recovery mnemonic; the platform cannot read the
   volume.
4. **`enclava status` is the source of truth** — it reports runtime status, TEE unlock
   state, and `tee_error` (the in-guest startup failure reason) without needing cluster
   access. Read it before theorizing.
5. **Fail-closed is correct behavior.** When verification can't complete, startup
   blocks or the deploy fails rather than proceeding unverified. Explain this; never
   improvise workarounds around a verification failure.

## Secret-handling discipline (always)

- Storage passwords and recovery mnemonics are **owner secrets**. Never echo them into
  logs, shell history, or files beyond what the user asked for. Prefer
  `--storage-password-file` on a tight-permissions file over inline arguments.
- The mnemonic is shown **once** at claim time. By default the CLI persists it locally
  so `enclava key backup` covers it; the user should export a backup right after the
  first deploy (`enclava key backup --out enclava-recovery.json`).
- If the user has lost both the password and the mnemonic, the data is unrecoverable —
  by design. Say so plainly.

## Unlock state machine (core of the platform)

Password mode (the default):

- **First deploy** waits for the TEE bootstrap endpoint, then the owner **claims**
  ownership: set a password, receive the BIP39 mnemonic (shown once). With
  `deploy --storage-password-file PATH` this happens automatically and non-interactively.
- **Every restart** boots to `locked`; the owner unlocks with the password
  (`enclava unlock`, interactive) or the deploy command with the same
  `--storage-password-file`.
- **`enclava recover --mnemonic-file M --new-password-file P`** re-wraps the seed under
  a new password after a lost password. It requires a **freshly booted, locked TEE** —
  against a long-running pod it fails `recovery_requires_locked_init_verifier`; restart
  the workload first. After a successful recover, storage is already unlocked — a
  follow-up `enclava unlock` reporting "not locked" is expected.
- **`enclava change-password`** re-wraps under a new password (needs the old one).

Auto-unlock (for unattended restarts):

- A **first deploy must be password mode** — auto mode has no owner seed yet to seal
  and fails at boot. Deploy password-first, then:
  `enclava auto-unlock enable --image <image>@sha256:<digest>` (seals the owner seed
  with VMPCK; binds the digest into a signed redeploy descriptor).
  `enclava auto-unlock disable --image <image>@sha256:<digest>` reverts to
  password-on-restart.

Known hard failure — **stale escrow**: if an app is destroyed while its pod was already
dead, the key escrow survives; recreating an app with the **same name** inherits it —
claim returns `already_claimed` and every unlock silently lands wrong-password
(`TEE: locked`, no error). The fix is recovering with the *old* app's mnemonic, which
still matches the surviving envelope.

## Command map (verified surface)

| Area | Commands |
| --- | --- |
| Auth | `login [--api-url] [--no-browser] [--org] [--approve-logs] [--nostr] [--email]`, `signup`, `whoami`, `logout` |
| Scaffold | `init` (interactive, needs a Dockerfile), `prepare` (non-interactive, CI-friendly) |
| Deploy | `create [--image] [--signer-subject] [--signer-issuer]`, `deploy --image IMG@DIGEST [--set K=V] [--set-file K=PATH] [--storage-password-file PATH]` |
| Observe | `status [--app]`, `logs [--app] [-f] [--log-private-key-file PATH]`, `log-key generate/list/select/revoke` |
| Config | `config set K=V…`, `config get` (names only — values never leave the TEE), `config unset K` |
| Templates | `template list`, `template deploy [slug] --name N [--ssh-public-key-file PATH]`, `template ssh-command --name N --wait [--json]` |
| Ownership | `claim`, `unlock`, `recover`, `change-password`, `auto-unlock enable/disable` |
| Lifecycle | `rollback [--to ID]`, `destroy [--app] [--force]` |
| Identity | `signer set/rotate`, `org create/switch/invite/members/keyring`, `key status/backup/restore/setup/rotate-owner` |
| Domains | `domains add/verify/list/remove` |

Most commands accept `--app` and default to `app.name` from `enclava.toml` in the
current directory.

## Pick the journey

Read exactly one reference (they carry the detail; this file is the shared spine):

- **Deploying your own container image** → read `references/deploy-oci.md`
- **Deploying a hosted template (fastest path, e.g. a confidential SSH box)** → read `references/hosted-template.md`
- **App already exists — logs, config, domains, unlock/recovery, rollback, destroy, or anything failed/stuck** → read `references/day-2.md`

For *understanding* the platform (what a TEE proves, who can read what, threat model),
the `enclava-concepts` skill is the right tool. For *independently verifying* a running
app's trust properties, use `enclava-verify`.

## Triage quick table

| Symptom | Meaning / first move |
| --- | --- |
| Deploy stalls; `status` shows `tee_error: … Read-only file system (os error 30)` | A `storage.paths` entry isn't a `VOLUME` in the image → add `VOLUME`, redeploy. |
| First deploy in auto mode fails | Expected — must deploy password-mode first. |
| `portable_verification_material_unavailable` | Image signed with cosign 2.x legacy `.sig` — re-sign with cosign 3.x (`sigstore/cosign-installer@v4`). |
| `status` shows `Status: drifted` after a failed deploy | Follow-up deploys won't roll — `destroy --app <name> --force`, then `create` + `deploy` clean. |
| Claim returns `already_claimed` on a *new* app | Stale escrow (see above) — recover with the old mnemonic. |
| `destroy` returns `app mutation already in progress` (409) | An in-flight deployment holds the mutation lease — wait for it to finish (check `status`), then retry. |
| Browser rejects the app cert (`ERR_CERT_AUTHORITY_INVALID`) | Some environments serve a Let's Encrypt staging cert — a platform toggle, not an app fault. |
| Unlock "did not complete" right after a deploy | The background unlock may still be running — trust `enclava status` over the CLI exit message. |

## Going deeper

Concepts, architecture, and full reference live in the Enclava developer docs
(https://docs.enclava.dev — also in this repo under `docs/`). Prefer them for *what*
something is; prefer this skill for *how* to operate it.
