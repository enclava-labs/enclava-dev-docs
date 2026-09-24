---
sidebar_position: 1
---

# Production Checklist

This checklist is for operators running a self-hosted CAP deployment.

## CAP API

- Use durable PostgreSQL.
- Provide Ed25519 API signing material through `API_SIGNING_KEY_PATH` or `API_SIGNING_KEY_PKCS8_BASE64`.
- Provide session HMAC material through `SESSION_HMAC_KEY_PATH` or `SESSION_HMAC_KEY_BASE64`.
- In release builds, configure `API_KEY_HMAC_PEPPER` or `API_KEY_HMAC_PEPPER_BASE64`.
- Set `TRUSTEE_POLICY_READ_AVAILABLE=true` for the supported signed-policy and in-TEE verification path.
- Use a signed platform release or exact matching environment values.
- Configure Trustee/KBS, policy signing, workload artifact, and attestation callback URLs.
- Use digest-pinned platform sidecar images.

## Kubernetes

- Configure the confidential runtime class expected by CAP.
- Scope CAP service account permissions to tenant resources it owns.
- Add network policies for PostgreSQL, Trustee/KBS, policy signing, registry metadata, DNS, and tenant TEE callbacks.
- Decide whether CAP-managed DNS and KBS policy management are required.
- Replace placeholder Kubernetes secrets with your secret-management system.
