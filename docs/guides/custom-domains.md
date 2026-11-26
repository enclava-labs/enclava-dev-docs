---
sidebar_position: 4
---

# Custom domains

Your app gets a platform domain by default (`<app>.<platform-zone>`). With a custom domain you can serve your own hostname — `app.example.com` — on the same confidential deployment. The certificate for it is issued **inside the enclave** via ACME DNS-01: the private key is generated in the TEE and never leaves it. That is the point of the feature — end-to-end TLS with your name, without anyone (including Enclava operators) holding your key.

Each app can have one custom domain. Custom domains are not limited by your plan — the plan limits the number of apps.

> **Two guardrails before you start.**
>
> 1. **Do not front the app with a TLS-terminating proxy or CDN.** Terminating TLS outside the enclave defeats the confidential-computing guarantee: the proxy would hold the private key and see plaintext traffic. A CNAME pointing at a proxy that re-encrypts is out of contract. Point the domain at Enclava and let the enclave terminate TLS.
> 2. **Keep the CNAME published after verification.** The platform writes the ACME DNS-01 challenge at the CNAME target on **every** certificate issuance — first boot and each renewal. If you remove the CNAME, the next issuance fails and the workload does **not** start (the platform hostname's certificate is in the same issuance). Remove the CNAME only after `enclava domains remove`.

## What you publish, and where

You publish three DNS records **in your own zone**, at your own registrar or DNS provider. The `enclava domains add` command prints the exact names and values — use what it prints, not this page (your challenge token and the platform's zone are specific to your app):

| Record | Name | Value |
| --- | --- | --- |
| Ownership TXT | `_enclava-challenge.<your-domain>` | `enclava-domain-verification=<token>` (printed by the CLI) |
| ACME CNAME | `_acme-challenge.<your-domain>` | `<your-domain>.acme.<platform-zone>` (printed by the CLI) |
| Routing record | `<your-domain>` | CNAME to your app's platform domain (printed by the CLI); on an apex domain use your provider's ALIAS/ANAME |

The routing record is what sends visitors to your app: without it the domain is verified and has a certificate, but nothing answers on it. The TXT record proves you control the domain. The CNAME delegates the ACME DNS-01 challenge — when Let's Encrypt (or the configured CA) asks for a challenge record under `_acme-challenge.<your-domain>`, your zone answers "ask `<your-domain>.acme.<platform-zone>`", where the platform publishes the challenge answer. Domains that are already inside the platform's zone do not need the CNAME; the CLI prints that record only when it applies.

## The flow: add → publish → verify → deploy

```bash
enclava domains add app.example.com --app myapp
```

`domains add` prints both records above. Publish them at your DNS provider, then verify:

```bash
enclava domains verify app.example.com --app myapp
```

Verification checks the ownership TXT live, every time it runs — and, where the CNAME applies (domains outside the platform zone, on deployments that issue certificates through DNS-01), the ACME CNAME too. Only after it passes should you deploy (or redeploy) with the domain attached — a domain is not active until verify passes, and the certificate is issued when the workload boots.

If the CNAME is missing or points at the wrong target, `verify` fails with `acme_delegation_missing` and prints the expected name/target pair:

```
acme_delegation_missing (publish CNAME _acme-challenge.app.example.com -> app.example.com.acme.<platform-zone>)
```

Publish (or fix) the CNAME exactly as printed, wait for DNS propagation, and verify again. The same error on a later renewal means the CNAME was removed after verification — see guardrail 2.

### Adding a domain to an app that is already deployed

`verify` routes the hostname straight away and restarts the app to pick up the route. If the app uses password unlock, unlock it again after the restart. The certificate for the new hostname is part of the signed deployment, so it is only issued on the next deploy:

```bash
enclava domains verify app.example.com --app myapp
enclava deploy
```

Until that deploy, the custom hostname reaches the app but is served without a matching certificate.

## After it works

```bash
enclava domains list --app myapp [--json]
enclava domains remove app.example.com --app myapp
```

`list` shows the platform, TEE, and custom domains for the app; `remove` detaches the custom domain. After `remove` — and only then — you may delete the DNS records you published.

Challenge tokens expire 24 hours after `domains add`; if yours expires, run `domains add` again for a fresh pair and publish the new TXT value.
