---
sidebar_position: 4
---

# Example Applications

The shortest path to a working mental model is working code. The
[`confidential-app-examples`](https://github.com/enclava-labs/confidential-app-examples)
repository carries small, complete applications — each one readable in a
sitting, each one teaching one thing well:

| Example | Teaches | Storage |
| --- | --- | --- |
| [`hello-tee`](https://github.com/enclava-labs/confidential-app-examples/tree/main/hello-tee) | the whole custom-image lifecycle — build, sign, create, deploy, claim — in about ten minutes | none |
| [`attested-rng`](https://github.com/enclava-labs/confidential-app-examples/tree/main/attested-rng) | client-nonce freshness, a derivation anyone can recompute, and verifying a running app with a trust policy you author | encrypted draw log |

Each example can be deployed two ways: **deploy the pre-built, signed image**
straight into your org (no build step), or **fork and build your own** under
your signer identity. The `attested-rng` README walks the full third-party
verification workflow — `enclava describe`, authoring a trust policy from
independently checked values, and gating CI on `enclava verify`.

:::note What makes these examples trustworthy teaching material
They state their own limits: what attestation proves (environment, code
identity, host-unreadable memory, freshness) and what it never will (app
correctness, randomness quality). A demo that overclaims is worse than no demo.
:::

To integrate attestation signals *into your own application*, continue to
[Attestation in your app](../guides/attestation-in-your-app.md).
