---
sidebar_position: 2
---

# CLI and Console

The hosted console and CLI share the same PaaS boundary. Browser users manage organizations, billing, apps, and support workflows in the console. CLI users authenticate through a browser approval flow and then use the `enclava` command for deploys and status.

## Console routes

| Path | Purpose |
| --- | --- |
| `/login` | Account login and account creation entry. |
| `/cli/login` | CLI device-code approval. |
| `/dashboard` | Organization overview, KPIs, and recent deployments. |
| `/orgs/[slug]/keyring` | Organization keyring viewer. |
| `/orgs/[slug]/billing` | Billing, credits, invoices, and Bitcoin payment state. |
| `/apps/[name]` | App detail and deployment history. |

## CLI API discovery

The shared hosted CLI API exposes discovery and health endpoints:

| Endpoint | Purpose |
| --- | --- |
| `/.well-known/enclava` | Discover API mode and CLI login endpoints. |
| `/healthz` | Liveness. |
| `/readyz` | Readiness and integration status. |
| `/auth/device/start` | Start CLI device login. |
| `/auth/device/poll` | Poll device-login state. |
| `/users/me` | Return authenticated CLI principal. |
| `/platform/deployment-context` | Return public material needed for signed deployment descriptors. |

## Auth model

Hosted CLI login stores local credentials for the active API base URL. Browser sessions stay server-side with HTTP-only cookies. Hosted service credentials remain in the PaaS backend.
