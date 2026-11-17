---
sidebar_position: 2
---

# Attestation in Your App

Your workload runs next to an **attestation-proxy** sidecar — the attested
component that verified the guest at boot. Applications can read its state to
surface *what the TEE believes* inside their own UI or API responses. This
guide covers the endpoints, the one architectural rule, and the honesty rule.

## The one architectural rule

The sidecar listens on `http://127.0.0.1:8081` **inside the guest only** — it
is not reachable from the internet, and it must stay that way. Fetch it
**server-side** and render what you need:

```python
import json, urllib.request

def sidecar(path, timeout=2.0):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:8081{path}", timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {e}"}   # degrade gracefully
```

Run locally (no sidecar) or during boot, every call can fail — render
`unavailable`, never crash. [`hello-tee`](https://github.com/enclava-labs/confidential-app-examples/tree/main/hello-tee)
is a complete working example of this pattern.

## What to read

| Endpoint | Returns | Notes |
| --- | --- | --- |
| `GET /v1/attestation/info` | attestation type, runtime class, signed policy (url + sha256), AMD endorsement chain, trust model | mode-independent; the "what am I running in" card |
| `GET /status` | `claims_verified`, ownership `state` (`locked`/`unlocked`), mode, error | 404s in auto-unlock mode and before init reports ready — degrade, don't crash |
| `GET /v1/attestation?nonce=…&domain=…&leaf_spki_sha256=…` | nonce-bound attestation evidence for in-app verification | nonce is base64 32B; binds evidence to your domain and TLS leaf |
| `GET /health` | liveness | |

The reserved prefix `/.well-known/confidential/*` on the app origin is routed
by the platform to the sidecar — your application cannot (and should not)
serve anything under it. That is where the proof endpoint lives:

```
GET /.well-known/confidential/proof-bundle?nonce=<base64url-32B>
```

## The honesty rule: claims vs proof

Anything your app renders — attestation cards included — is a **claim**: the
workload produced it, and a workload (or an impostor on an ordinary host) can
print anything. The **proof** is that reserved endpoint: it answers every
nonce with fresh AMD SEV-SNP evidence bound to the TLS channel, and
third parties appraise it with:

```bash
enclava verify https://<your-app-origin> --policy trust-policy.json
```

…against a policy the *verifier* holds. Put the verify command on your page,
link your published policy, and say which is which. The
[`attested-rng`](https://github.com/enclava-labs/confidential-app-examples/tree/main/attested-rng)
example demonstrates the full pattern, including pointing users at how to
check it.

## Freshness inputs: follow the platform's nonce discipline

If your app accepts a freshness input (a nonce, a challenge), use the same
rules the platform's endpoints enforce — they exist because loose nonce
handling silently breaks freshness proofs:

- exactly **one** parameter (duplicates rejected, not last-wins)
- base64url, decoding to **exactly 32 bytes** (padding tolerated)

Folding the client's nonce into the thing you return is what makes responses
replay-evident; `attested-rng`'s draw transcript is a worked example.

## TLS note

Some environments issue app-origin certificates from the Let's Encrypt
**staging** directory (a platform toggle, not an app fault); browsers will
warn. If `enclava verify` fails only at the TLS chain, check which LE
environment the origin uses before concluding anything worse.
