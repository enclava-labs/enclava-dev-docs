---
sidebar_position: 1
---

# API Surface

Enclava exposes a shared hosted CLI API through PaaS and a CAP API underneath it. Exact schemas should be generated from the OpenAPI contract or CAP API types.

## Shared hosted CLI API

| Endpoint | Purpose |
| --- | --- |
| `/.well-known/enclava` | Discover API mode and CLI login endpoints. |
| `/healthz` | Liveness. |
| `/readyz` | Readiness. |
| `/cli/login` | Browser approval entry for device login. |
| `/auth/device/start` | Start device login. |
| `/auth/device/poll` | Poll device login. |
| `/users/me` | Authenticated CLI principal and active organization. |
| `/auth/api-keys` | Create hosted API keys. |
| `/auth/api-keys/{key_id}` | Revoke hosted API keys. |
| `/platform/deployment-context` | Public deployment signing context. |
| `/templates` | List hosted templates. |
| `/template-instances` | Create hosted template instances. |
| `/apps/{app_name}/ssh-command` | Fetch the rendered stable SSH endpoint command. |

## CAP API responsibilities

CAP API owns app creation, deploy orchestration, deployment history, domains, config, org keyring state, workload artifacts, tenant TEE callbacks, and runtime status. PaaS routes hosted product flows to CAP without exposing CAP service credentials to the browser.
