---
sidebar_position: 2
---

# Security Checklist

## Image and release hygiene

- Deploy workload images by digest, not mutable tags.
- Configure the expected cosign signer subject and issuer.
- Pin platform sidecar images by digest.
- Verify signed platform release material before promotion.
- Do not enable debug bypass flags in production.

## Runtime and policy

- Keep `TRUSTEE_POLICY_READ_AVAILABLE=true` for production deploys.
- Use HTTPS Trustee/KBS URLs.
- Protect Trustee callback bearer tokens.
- Scope registry pull credentials with repository allowlists where possible.
- Keep generated policy artifacts and descriptor verification enabled.

## Recovery material

- Create recovery backups for password-mode apps.
- Store recovery files outside source repositories.
- Restrict access to recovery material to operators who can administer the confidential workload.
