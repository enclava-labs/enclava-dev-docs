---
name: enclava-verify
description: Independently verify (appraise) a running Enclava app's trust properties from outside, or verify a saved proof bundle as historical evidence. Use when the user wants to verify/audit/attest an enclava origin or deployment, check a proof bundle, build or review a trust policy, ask "is this app really running in a TEE / is this the code I expect", or do third-party due diligence on an enclava-hosted service.
compatibility: enclava CLI v0.1.x (verify, describe)
---

# Independent verification with `enclava verify`

Verification answers an auditor's question: *should I trust this running origin?* It
fetches fresh cryptographic evidence from the target and appraises it against a
**policy you obtained independently of the target**. It is deliberately separate from
operating an app (that's the `enclava` skill).

## The two commands

```bash
enclava describe <https-origin-or-bundle-path> [--policy-skeleton PATH] [--save-bundle PATH] [--json]
enclava verify <https-origin> --policy trust-policy.json [--save-bundle PATH] [--json]
enclava verify --bundle saved-bundle.bin --policy trust-policy.json [--json]   # historical evidence
```

- **`describe`** observes what a target *contains* — no appraisal, no judgment. Safe
  to run against anything.
- **`verify`** appraises: every check in the policy must pass. `--json` emits the
  canonical result schema (for CI); `--save-bundle` captures the exact live bytes as
  historical evidence (the bundle format is content-addressed media type
  `application/vnd.enclava.proof-bundle.v1`).

## What a live verification does

The CLI fetches `GET <origin>/.well-known/confidential/proof-bundle?nonce=<nonce>`
with a fresh 32-byte random nonce. The TEE-side service returns a proof bundle whose
attestation report is **bound to that nonce** — a replayed or prefabricated bundle
can't match it. The bundle then gets checked against the policy: report signature via
the AMD VCEK, endorsement chain up to the pinned ARK, launch measurement, TCB levels,
guest policy, TLS leaf binding to the origin, image digest and cosign signature
policy, platform release, runtime class and sidecar digests, deployment identity,
descriptor measurement, revocation freshness.

Key properties worth explaining to users:

- **Freshness by nonce**: each live verification is a new challenge; old evidence
  can't be served again. A saved `--bundle` is *historical* evidence of a past state,
  clearly distinct.
- **Measurement, not correctness**: a passing verification proves *which* code and
  configuration booted — not that the code is bug-free or honest. A measured bug is
  still a bug.
- **Fail-closed**: if the chain can't be completed (bad signature, stale revocation,
  missing endorsement), verification fails rather than downgrades. That is the
  trustworthy behavior.

## Authoring a trust policy (TOFU done carefully)

There is no global list of "good" measurements — you pin what *you* expect. The
workflow:

1. `enclava describe <origin> --policy-skeleton draft.json` — emits a
   `enclava-trust-policy-v1` skeleton from observed values (trust-on-first-use).
2. **Edit the draft before trusting it.** The skeleton is derived from what the target
   just showed you, so a compromised target could have shaped it. Especially review:
   `amd.allowed_measurements`, the sigstore block (identities/issuers you'll accept as
   image signers), `amd.trusted_ark_sha256` (compare against AMD's published ARK),
   and `target.image_digests` (compare against the digest you built/expect).
3. Record the final policy **via a channel the target cannot influence** (e.g. checked
   into *your* repo) — then verify with it.
4. Iterate: `enclava verify <origin> --policy p.json --json` reports each check;
   adjust pins that are legitimately expected to change (new firmware TCB → new
   measurement) consciously, never by blanket-copying observed values.

A pinned policy typically encodes: allowed launch measurements, minimum TCB levels,
guest policy value, trusted ARK hash, allowed origins, image digests, runtime class,
platform sidecar digests, platform release versions, org/application IDs, trusted
keyring and policy-signing keys, and the sigstore identities. Copy from a known-good
example rather than authoring from scratch when possible.

## Practical guidance

- Verify from a machine/network *you* control — the nonce protects freshness, but the
  TLS connection to the origin should also be genuinely yours.
- Some environments serve Let's Encrypt **staging** certs on tenant app origins (a
  platform toggle); browsers/CLIs with strict roots will flag them. If verification
  fails only at TLS-leaf chain-of-trust, check which LE environment the origin uses
  before concluding anything worse.
- For CI or repeat audits: `verify --json` and gate the step on the result (a failed
  appraisal must fail the check); keep the policy + saved bundles under version
  control as your evidence trail.
- `describe` first, always, when facing an unknown target — it tells you what there is
  to pin before you pin anything.
