---
sidebar_position: 1
---

# Console and CLI Login

The Enclava console at [app.enclava.dev](https://app.enclava.dev/) and the `enclava` CLI work on the same account and organizations. Use the console to manage your organization, billing, and apps; use the CLI to deploy and operate apps.

## Console pages

| Page | What it's for |
| --- | --- |
| `/login` | Log in or create an account. |
| `/cli/login` | Approve a CLI login. |
| `/dashboard` | Organization overview, usage, and recent deployments. |
| `/orgs/<org>/keyring` | The organization keyring: which deployment keys may deploy. |
| `/orgs/<org>/billing` | Billing, credits, invoices, and Bitcoin payments. |
| `/apps/<name>` | App details and deployment history. |

## Logging in from the CLI

```bash
enclava login
```

`login` starts a device login: it opens the console's `/cli/login` page in your browser, where you approve the session. After approval the CLI stores its credentials locally.

| Flag | Use it to |
| --- | --- |
| `--no-browser` | Approve from another device, for example when logging in over SSH. |
| `--org ORG` | Scope the session to one organization. |
| `--approve-logs` | Allow this CLI session to read your app logs. |

Check who you are logged in as with `enclava whoami`, and end the session with `enclava logout`.

## Sessions and credentials

Your console session is kept server-side in an HTTP-only cookie, so page scripts can't read it. The CLI keeps its own credentials on your machine. Enclava's own service credentials are never sent to your browser or your CLI.
