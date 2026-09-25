---
sidebar_position: 3
---

# Security Checklist

Enclava protects your app from the infrastructure. These steps are on your side.

## Images and signing

- Deploy images by digest (`image@sha256:…`), never by tag.
- Sign images in CI with keyless cosign and register that exact workflow as the app's signer subject.
- Keep the signing workflow on a protected branch: whoever can change it can publish deployable code.
- Rotate the signer with `enclava signer rotate` when the workflow path or repository changes.

## Secrets and config

- Deliver secrets with `enclava deploy --set-file KEY=PATH`, not inline `KEY=VALUE` arguments that end up in shell history and process listings.
- Don't bake secrets into the image.

## Storage and recovery

- Use a strong storage password and keep it in a password manager or a protected file.
- Run `enclava key backup` right after the first deploy.
- Store recovery files outside source repositories, and limit access to the people who administer the app.

## Your application

- Confidential computing doesn't fix application bugs. Keep access control, audit logging, and dependency updates in place.
- Only expose the ports and endpoints your app needs.
