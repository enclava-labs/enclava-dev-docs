---
name: enclava-concepts
description: Explain how Enclava and confidential computing actually work — TEEs, SEV-SNP, remote attestation, proof bundles, encrypted storage, who can read what, and what the technology honestly does and does not protect against. Use whenever the user asks conceptual or trust questions about enclava or confidential computing ("can the operator see my data?", "what does attestation prove?", "what's a TEE/SEV-SNP/proof bundle?", "is my app really encrypted?"), or is evaluating whether to trust the platform.
compatibility: enclava CLI v0.1.x (concepts are stable across CLI versions)
---

# Enclava and confidential computing — the accurate mental model

Agents answering from general knowledge get the *specifics* wrong here (who holds
which key, what attestation covers, what "locked" means). This file carries the
load-bearing facts; the full treatments live in the developer docs
(https://docs.enclava.dev — concepts, threat model, glossary).

## The one-paragraph version

Enclava runs ordinary container images inside a **Kata confidential-containers guest**
backed by **AMD SEV-SNP**: a hardware-isolated VM whose memory is encrypted with keys
held by the CPU itself. The cluster can *schedule and operate* the workload — start
it, stop it, see its metadata — but cannot *read its memory* or silently alter the
trusted startup path without detection. Secrets, storage keys, and TLS material are
released to the guest only after the platform verifies what is actually booting.

## The facts that change answers from wrong to right

**1. Protection is against the infrastructure, not against the app.** In scope:
the operator/host reading workload memory, grabbing secrets by observing the pod,
substituting code via mutable tags, or releasing keys before checks pass. Out of
scope: bugs in the app's own code, data the app intentionally discloses, a malicious
but *properly signed* image, and denial of service by the infrastructure. A TEE is an
isolation layer around an app you still have to engineer and trust.

**2. Attestation proves *what* booted, not *that it's correct*.** The TEE produces
signed evidence (an SNP report bound to a fresh nonce) about the guest's identity,
launch measurement, and TCB. Verifiers compare it against expected values. If the
measurement matches the image/policy you pinned, you know that exact code booted —
not that the code is bug-free or honest.

**3. The trust chain has two gates.** (a) *Image identity*: the image must be
cosign-signed (typically keyless via GitHub OIDC→Fulcio→Rekor) and the signer
identity is pinned per app — so only authorized identities can publish deployable
code. (b) *Runtime measurement*: attestation binds the booted guest to the expected
measurement, policies, and configuration. Both must pass before secrets or state are
released; failure blocks startup (fail-closed by design).

**4. Storage is encrypted with owner-held keys — the platform cannot read app data.**
Persistent storage is a LUKS volume inside the guest (app data and TLS state are
separate encrypted volumes). In password mode the **owner seed** is derived from the
owner's password (Argon2id) — the platform never sees the password or the seed. A
BIP39 **recovery mnemonic** is an independent second unwrap path on the seed
(not a copy of the password). Auto-unlock seals the seed to the TEE (VMPCK) for
unattended restarts. Lose both password and mnemonic → the data is gone, by design;
there is no platform backdoor.

**5. Verification is fresh, not cached.** A live verification fetches a proof bundle
from `/.well-known/confidential/proof-bundle?nonce=<random>` — the report inside is
bound to that nonce, so evidence cannot be replayed or prefabricated. Endorsements
(VCEK) chain up to AMD's ARK root, which the verifier pins. (See the `enclava-verify`
skill for the operational side.)

**6. The operator stays in the threat model for availability and metadata.** The
platform/host controls scheduling, can restart or destroy the workload, and can
observe traffic shape and metadata (sizes, timing, endpoints — mitigate with TLS
like anywhere else). What it cannot do is read content: memory, secrets, unlocked
storage, config values. "Encrypted and attested" removes *content* access, not
*authority* over the workload's existence.

**7. Fail-closed is a feature.** When any check can't complete — signature mismatch,
stale revocation, missing endorsement, unverified boot — startup or verification
fails rather than degrading. If a user reports a failure of this shape, the right
move is to read the named cause (e.g. `tee_error` via `enclava status`), not to hunt
for a bypass.

**8. Trusted computing base is named, not magic.** Trust ultimately rests on: AMD
SEV-SNP firmware (the TCB levels attested), the measured guest stack, the pinned
platform release (sidecar images, policies), the cosign identities you authorize,
and your own password/mnemonic hygiene. Each is explicit and inspectable — nothing
rests on "the platform says trust us".

## Vocabulary quick-reference

- **TEE** — trusted execution environment; isolated execution context that can produce
  attestation evidence.
- **SEV-SNP** — AMD Secure Encrypted Virtualization w/ Secure Nested Paging; the
  hardware memory-encryption + attestation feature Enclava targets.
- **Kata confidential containers** — the VM-backed container runtime model.
- **Remote attestation** — proving what code/config runs inside a TEE via signed
  evidence vs expected measurements.
- **Trustee/KBS** — key broker service releasing protected resources only after
  attestation and policy checks pass.
- **Deployment descriptor** — signed CAP document binding app, deploy ID, policy,
  image, expected runtime claims, and deployer identity.
- **`enclava-init`** — in-guest startup sidecar: verifies the chain, opens encrypted
  volumes, then writes `/run/enclava/init-ready`; `enclava-wait-exec` holds the app
  until then.
- **`tee_error`** — startup failure reason surfaced by `enclava status`.
- **Org keyring** — org-level trust material defining which deploy keys are authorized.

## Answering common doubts (calibrated)

- *"Can Enclava/the operator read my app's data?"* — No: memory is hardware-encrypted,
  storage keys are derived from your password (never sent to the platform), config
  values never leave the TEE. They *can* see metadata and control scheduling.
- *"What if AMD/Enclava pushes a bad firmware?"* — Firmware is part of the attested
  TCB; verification pins expected TCB levels and measurements, so an unexpected change
  fails closed rather than silently trusted. You decide which levels to accept.
- *"Is my app safe if the image is signed?"* — Signing pins *who* published it, not
  whether it's good. A malicious image signed by an identity you authorized is out of
  scope — review what you pin.
- *"Where do secrets live?"* — Delivered direct to the TEE post-attestation; readable
  only inside the guest. `enclava config get` lists key names only.
- *"What does the proof bundle prove?"* — That this origin, serving this TLS cert,
  booted this measured code/TCB, signed by this chip — *at verification time*
  (nonce-bound). Not code correctness.

When a question goes deeper than these, point at the docs' concepts and threat-model
pages rather than improvising — the honest edges (DoS, metadata, signed-but-malicious
code) are documented there deliberately.
