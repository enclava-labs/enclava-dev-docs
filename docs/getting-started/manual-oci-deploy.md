---
sidebar_position: 3
---

# Deploy a Custom OCI Image

Manual OCI deployment uses CAP directly. This path is for teams that need to run their own image instead of a hosted template.

## Build, sign, and pin the image

CAP expects immutable images. Push your image and deploy by digest:

```bash
docker build -t ghcr.io/example/hello-confidential:latest .
docker push ghcr.io/example/hello-confidential:latest
```

Resolve the digest and sign the image with the identity you will configure on the app. For GitHub Actions keyless signing, the signer subject is typically the workflow identity.

## Initialize the app

```bash
enclava login
enclava init
enclava create --signer-subject <cosign-subject>
```

`enclava init` creates `enclava.toml`. `enclava create` registers the app from that config and pins the expected signer identity.

## Deploy

```bash
enclava deploy --image ghcr.io/example/hello-confidential@sha256:<digest>
enclava status
```

The CLI signs a deployment descriptor. CAP validates the descriptor, org keyring, image digest, signer identity, generated policy artifacts, and platform release material before Kubernetes resources are applied.

## Runtime config

Use config commands for workload configuration and secrets:

```bash
enclava config set API_TOKEN=...
enclava config list
```

For values that should come from files, use the CLI's file-based config inputs where available instead of embedding secrets in shell history.

## Recovery

Password-mode apps should export recovery material after initial setup:

```bash
enclava key backup --out enclava-recovery.json
```

Keep recovery files outside the application repo and protect them like production credentials.
