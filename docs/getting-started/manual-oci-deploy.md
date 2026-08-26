---
sidebar_position: 3
---

# Deploy a Custom OCI Image

Manual OCI deployment uses CAP directly. This path is for teams that need to run their own image instead of a hosted template.

## Prerequisites

- An Enclava account and organization.
- The `enclava` CLI.
- Docker and a container registry. The examples below use GitHub Container Registry (GHCR).
- A `Dockerfile` in the repository root.

## Scaffold the app config

From the repository root:

```bash
enclava init
```

`init` prompts for an app name and port, then writes both `enclava.toml` and `.github/workflows/enclava-deploy.yml` (a build-and-sign workflow). When a `Dockerfile` is present it suggests the first `EXPOSE` port; without one it suggests port 3000. `enclava prepare` writes the same files without prompts on a first run; when either file already exists it prompts before overwriting (and a non-TTY run fails with "not a terminal" — there is no `--yes`/`--force`). For CI: run `prepare` once, commit both files, and don't re-run it over them.

The generated config:

```toml
[app]
name = "my-app"
port = 8080
command = ["/usr/local/bin/app"]

[storage]
paths = ["/data"]
size = "5Gi"
tls_size = "2Gi"

[unlock]
mode = "password"

[resources]
cpu = "1"
memory = "1Gi"

[health]
path = "/health"
interval = 30
timeout = 5
```

Set `command` to the process the image runs and `storage.paths` to the in-container paths that need persistent encrypted storage. Each `storage.paths` entry must be declared as a `VOLUME` in the image.

## Image requirements

CAP runs the container on a read-only rootfs inside a confidential guest. The relevant image contract and optional scaffolding metadata are:

| Requirement | Why |
| --- | --- |
| `EXPOSE <port>` | Optional scaffolding metadata: `init` uses it to suggest `app.port`. Runtime uses `app.port` from the signed config, not `EXPOSE`. |
| `VOLUME ["<path>", …]` for every `storage.paths` entry | `enclava-init` bind-mounts each path. Without a volume declaration the bind fails with `Read-only file system` — visible as `tee_error: enclava_init_failed: … (os error 30)` in `enclava status`. |
| Pin by digest at deploy | `create` can resolve a tag to a digest; `deploy` rejects tags and requires `image@sha256:<digest>`. |

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY server.py .
EXPOSE 8080
VOLUME ["/data"]
CMD ["python3", "/app/server.py"]
```

There is no "no storage" default: with `[storage]` absent, CAP still defaults `paths = ["/data"]`. If the app needs no persistent storage, set `paths = []` explicitly and skip the `VOLUME`.

## Build and sign the image

CAP requires both portable cosign signature material and a bound provenance manifest. The recommended path is keyless signing with GitHub Actions OIDC: GitHub's OIDC provider issues a short-lived Fulcio certificate, cosign signs the digest, Rekor records it, and GitHub publishes build provenance. No signing key to manage.

The starter workflow (written by `init` or `prepare`) builds, pushes, signs, and attests on every push to `main`. Older generated workflows may still pin `cosign-installer@v3`; replace that step with the pinned v4.1.2 commit below. This is the minimum complete flow:

```yaml
name: Build signed image

on:
  push:
    branches: [main]

permissions:
  contents: read
  packages: write
  id-token: write
  attestations: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/setup-buildx-action@v3

      - name: Build and push
        id: build
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

      - name: Install cosign
        # v4.1.2 — immutable pin; installs cosign 3.x
        uses: sigstore/cosign-installer@6f9f17788090df1f26f669e9d70d6ae9567deba6

      - name: Sign image
        run: >-
          cosign sign --yes
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ steps.build.outputs.digest }}

      - name: Attest build provenance
        uses: actions/attest-build-provenance@v2
        with:
          subject-name: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          subject-digest: ${{ steps.build.outputs.digest }}
          push-to-registry: true
```

The generated workflow ends by printing a ready-to-run `enclava deploy --image <image>@<digest>` command with the digest filled in. You can also read the digest from the GHCR package page or with `docker buildx imagetools inspect ghcr.io/<org>/<repo>:<tag>`. If the cluster pulls anonymously, set the GHCR package to public.

To confirm the exact identity to pin, verify locally:

```bash
cosign verify \
  --certificate-identity https://github.com/<org>/<repo>/.github/workflows/<workflow>.yml@refs/heads/main \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/<org>/<repo>@sha256:<digest>
```

## Create the app

```bash
enclava create \
  --image ghcr.io/<org>/<repo>:latest \
  --signer-subject https://github.com/<org>/<repo>/.github/workflows/<workflow>.yml@refs/heads/main
```

`create` registers the app, resolves the tag to a digest, and pins the signer identity. `--signer-issuer` defaults to the GitHub Actions OIDC issuer; set it only for a different OIDC provider. The signer subject must match the identity that signed the image — the workflow file path (`enclava-deploy.yml`, the name `init` and `prepare` write).

## Deploy

```bash
enclava deploy \
  --image ghcr.io/<org>/<repo>@sha256:<digest> \
  --storage-password-file "$HOME/.enclava/my-app-storage-password"
```

With `--storage-password-file`, the first deploy waits for the TEE bootstrap endpoint and claims ownership directly; restarts unlock with the same password. No separate `enclava claim` is needed on this path. Without it, `deploy` prompts for the password interactively (or run `enclava claim` first).

## Verify

```bash
enclava status
```

A healthy deploy shows `Status: running`, `TEE: unlocked`, `Unlock: unlocked`. On failure, `status` surfaces the `tee_error` from `enclava-init` — the first thing to read when a deploy stalls.

## Config and secrets

Deliver runtime configuration through CAP rather than baking it into the image:

```bash
enclava config set FEATURE_FLAG=enabled
enclava config get
```

`config set` accepts only inline `KEY=VALUE` arguments, which may enter local process listings and shell history; do not use it for sensitive plaintext. For sensitive values, redeploy with `deploy --set-file KEY=/secure/path/token`. Values travel directly from the CLI to the attested TEE; the control plane does not persist or return their plaintext, and `config get` lists names only.

## Recovery

Export recovery material immediately after the first deploy:

```bash
enclava key backup --out "$HOME/.enclava/my-app-recovery.json"
```

Keep the backup outside the repository. `enclava recover --mnemonic-file …` can re-derive ownership from it after a lost password or a move to a fresh cluster.

## Storage modes

`[unlock] mode` controls how the encrypted app-data volume is opened:

| Mode | Behavior |
| --- | --- |
| `password` (default) | At claim, the TEE generates a random owner seed. Argon2id plus HKDF derive a password key that wraps the seed; volume keys derive from the seed. |
| `auto` | KBS releases a separately wrapped seed envelope only to an attested guest, allowing unattended restarts. This is KBS-attestation-gated wrapping, not TEE hardware sealing. Current `create` rejects auto mode before the first deploy because no owner seed exists yet. |

Use password mode for the first deploy, then enable the KBS-gated wrap for restarts:

```bash
enclava auto-unlock enable --image ghcr.io/<org>/<repo>@sha256:<digest>
```

## Troubleshooting

- **`tee_error: … Read-only file system (os error 30)`** — a `storage.paths` entry is not a `VOLUME` in the image. Add the `VOLUME` and redeploy.
- **`portable_verification_material_unavailable`** — CAP could not assemble portable signature/provenance material. A cosign 2.x legacy `.sig` object without portable DSSE is one common cause, but registry/referrer errors, missing provenance, malformed bundles, and size limits share this code; inspect both signature and provenance objects.
- **First deploy in auto mode is rejected** — set `[unlock] mode = "password"` for the first deploy.
- **A failed deploy does not roll on a follow-up `deploy`** — a deploy that fails partway can leave the app with `Status: drifted`. The reliable recovery is `enclava destroy --app <name> --force`, then `create` + `deploy` from clean.
- **Browser rejects the app cert (`ERR_CERT_AUTHORITY_INVALID`)** — some environments serve a Let's Encrypt staging cert (a platform troubleshooting toggle). Browse with `curl -sk`, or use an environment on production LE.
