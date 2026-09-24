---
sidebar_position: 1
---

# Enclava PaaS Overview

Enclava PaaS is the hosted product layer for confidential application deployment. It is intentionally separate from CAP so hosted UX, billing, onboarding, support, and company-specific operations do not have to ship in the self-hostable control plane.

## What PaaS owns

- Hosted account login through ZITADEL OIDC.
- HTTP-only server-side sessions.
- Organization dashboard, app detail pages, keyring views, and deployment history.
- CLI device-code approval at `/cli/login`.
- Hosted API key create and revoke flows.
- Hosted templates, including `debian-ssh-frp`.
- Billing, plan limits, invoices, and Bitcoin payment state.
- Support and admin workflows.

## What PaaS does not own

PaaS does not replace CAP's core runtime. CAP remains the source of truth for API contracts, CLI flows, engine rendering, signed deployment descriptors, and in-TEE verification.

## Hosted architecture

```text
browser
  -> same-origin PaaS Rust backend-for-frontend
    -> ZITADEL
    -> Lago
    -> Bitcoin processor
    -> CAP
```

The browser talks only to the PaaS backend. It never calls CAP, Lago, ZITADEL admin APIs, relay systems, or payment infrastructure directly, and service credentials stay on the server.
