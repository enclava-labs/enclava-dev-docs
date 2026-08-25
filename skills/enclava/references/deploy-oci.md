# Journey: deploy a custom OCI image (manual CAP path)

For teams running their own container image. If a hosted template already fits the
workload, that path (`../hosted-template.md`) is much less work.

## Prerequisites

- An Enclava account and org (`enclava login`; `signup` to create).
- The `enclava` CLI on PATH.
- Docker + a registry (examples use GHCR) and a `Dockerfile` in the repo root.

## 1. Scaffold

```bash
enclava init        # interactive: detects Dockerfile + EXPOSE, writes enclava.toml
                    # and .github/workflows/enclava-deploy.yml (build-and-sign CI)
enclava prepare     # non-interactive, idempotent equivalent — use in CI
```

Resulting `enclava.toml` (edit as needed):

```toml
[app]
name = "my-app"
port = 8080
command = ["/usr/local/bin/app"]

[storage]
paths = ["/data"]        # in-container paths needing persistent encrypted storage
size = "5Gi"
tls_size = "2Gi"

[unlock]
mode = "password"        # MUST be password for the first deploy (see spine)

[resources]
cpu = "1"
memory = "1Gi"

[health]
path = "/health"
interval = 30
timeout = 5
```

Omit `storage.paths` entirely if the app needs no persistent storage.

## 2. Meet the image contract

The workload runs on a **read-only rootfs** inside the confidential guest, so the
image side has hard requirements:

| Requirement | Why |
| --- | --- |
| `EXPOSE <port>` | Wired into the app config and the readiness probe. |
| `VOLUME ["<path>", …]` for **every** `storage.paths` entry | `enclava-init` bind-mounts each path into the encrypted volume; without the volume declaration the bind fails with `Read-only file system (os error 30)`, surfaced as `tee_error` in `enclava status`. |
| Digest pinning at deploy | Tags are resolved at `create`; `deploy` requires `image@sha256:<digest>`. |

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY server.py .
EXPOSE 8080
VOLUME ["/data"]
CMD ["python3", "/app/server.py"]
```

## 3. Build and sign (cosign, keyless via GitHub Actions)

CAP admits an image only after verifying its cosign signature. The intended path is
**keyless signing with GitHub OIDC**: GitHub issues a short-lived Fulcio certificate,
cosign signs the digest, Rekor records it. No signing key to manage.

The starter workflow from `init`/`prepare` builds, pushes to GHCR, and signs on push
to `main`. The essentials:

```yaml
permissions:
  id-token: write      # GitHub OIDC → Fulcio certificate for cosign
  packages: write      # push to GHCR
steps:
  - uses: docker/build-push-action@v6
  - uses: sigstore/cosign-installer@v4      # cosign 3.x — REQUIRED.
                                            # 2.x legacy .sig tags fail with
                                            # portable_verification_material_unavailable
  - run: cosign sign --yes ghcr.io/${{ github.repository }}@${{ steps.build.outputs.digest }}
```

The workflow prints a ready-to-run `enclava deploy --image <image>@<digest>` line at
the end. The digest also appears on the GHCR package page, or via
`docker buildx imagetools inspect <image>:<tag>`. If the cluster pulls anonymously,
make the GHCR package public.

**The signer subject** (pin this next) is the GitHub Actions OIDC identity — note that
the **workflow filename is part of it**:

```
https://github.com/<org>/<repo>/.github/workflows/<workflow>.yml@refs/heads/<branch>
```

Confirm it locally before pinning:

```bash
cosign verify \
  --certificate-identity https://github.com/<org>/<repo>/.github/workflows/<workflow>.yml@refs/heads/main \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/<org>/<repo>@sha256:<digest>
```

(Keep the workflow filename stable afterwards — renaming it changes the identity.)

## 4. Create the app (pin identity + image)

```bash
enclava create \
  --image ghcr.io/<org>/<repo>:latest \
  --signer-subject https://github.com/<org>/<repo>/.github/workflows/<workflow>.yml@refs/heads/main
```

`create` registers the app from `enclava.toml`, resolves the tag to a digest, and pins
the signer identity. `--signer-issuer` defaults to the GitHub Actions OIDC issuer —
set it only for a different OIDC provider. If you skip `--signer-subject` here, set it
before deploying with `enclava signer set <subject>` (first set needs no confirmation
token; later changes go through `signer rotate`, which requires a platform-issued
confirmation token).

## 5. Deploy

```bash
enclava deploy \
  --image ghcr.io/<org>/<repo>@sha256:<digest> \
  --storage-password-file ./storage-password
```

- `--storage-password-file` makes the first deploy **claim ownership and unlock
  non-interactively** (create the file with tight permissions; never pass the password
  inline). Without it, `deploy` prompts for the password, or the user runs
  `enclava claim` separately.
- By default the recovery mnemonic is persisted locally so `enclava key backup` covers
  it; `--no-store-mnemonic` opts out (shown-once-only — only for users who truly want
  no local copy).
- Runtime config: `--set KEY=VALUE`, or `--set-file KEY=PATH` to keep a secret out of
  process arguments.

## 6. Verify and back up

```bash
enclava status     # expect: Status: running, TEE: unlocked, Unlock: unlocked
enclava key backup --out enclava-recovery.json   # immediately; store outside the repo
```

If deploys will be unattended (restarts without a human), consider
`enclava auto-unlock enable --image <image>@sha256:<digest>` — but only after the
password-mode first deploy succeeded.

## Common failures on this path

| Symptom | Fix |
| --- | --- |
| `tee_error: … (os error 30)` read-only bind | Missing `VOLUME` for a `storage.paths` entry — add it, redeploy. |
| `portable_verification_material_unavailable` | Signed with cosign 2.x — switch to `cosign-installer@v4` (3.x, DSSE referrers) and re-sign. |
| Deploy rejected on signature/identity | Signer subject doesn't match what signed the image — check workflow filename/branch in the subject, re-run the `cosign verify` above. |
| First deploy in auto mode fails | Expected — current CLIs reject it up front at `create`; older CLIs fail at boot after ~a minute. Either way: `[unlock] mode` must be `password` for the first deploy. |
| `Status: drifted`, later deploys no-op | `enclava destroy --app <name> --force`, then `create` + `deploy` from clean (destroy first — the app name and escrow interact; see the day-2 reference before recreating with the same name). |
