---
sidebar_position: 1
slug: /
---

# Enclava Developer Documentation

Enclava runs your containers as confidential applications. Your app runs inside a hardware-isolated trusted execution environment (TEE) on AMD SEV-SNP, so the infrastructure can schedule and observe it but cannot read its memory, its secrets, or its stored data.

From your side it works like a regular platform: log in, point the `enclava` CLI at a container image, and deploy. Before your app gets its secrets and storage, Enclava checks that the running code is the image you signed.

<Chips>

- Encrypted in use
- Encrypted at rest
- Attestation verifiable
- AMD SEV-SNP

</Chips>

## What you can deploy

<Cards>

- [Templates](./getting-started/hosted-template.md)

  The fastest path. A template is a ready-made workload that Enclava maintains for you. `debian-ssh-frp` gives you a confidential Debian machine with a stable SSH endpoint; Enclava delivers your SSH key and prints the SSH command.
- [Your own container image](./getting-started/manual-oci-deploy.md)

  Full control. Build and sign an image in CI, pin it by digest, and deploy it with the `enclava` CLI. Enclava verifies the digest and signer before the app starts.

</Cards>

## How a deploy works

<Flow>

1. **You deploy** with the `enclava` CLI or the Enclava console.
2. **Enclava verifies the image**: its digest and the identity that signed it.
3. **A TEE starts** on AMD SEV-SNP, with encrypted, isolated memory.
4. **The TEE proves what is running** through hardware attestation.
5. **Secrets are released**: encrypted storage opens, TLS and secrets are delivered.
6. **Your app starts**, only after every check has passed.

</Flow>

Your app runs as an ordinary container, but it only starts after these confidential-computing checks pass. If any check fails, the app does not start and `enclava status` tells you why.

## Start here

<Cards>

- [Quickstart](./getting-started/quickstart.md)

  Install the CLI, log in, and pick a deploy path.
- [Deploy a template](./getting-started/hosted-template.md)

  A confidential SSH machine in a few commands.
- [Deploy your own image](./getting-started/manual-oci-deploy.md)

  Build, sign, and deploy a container.
- [How Enclava protects your app](./concepts/confidential-computing.md)

  What happens inside the TEE.

</Cards>

## Agent skills

If you use Enclava through a coding agent (Claude Code, Cursor, Codex, pi, …), install the
[agent skills](https://github.com/enclava-labs/enclava-dev-skills): procedures, contracts, and failure
triage the agent loads on demand. Clone the repo into your agent's skills directory and
update it with `git pull`:

```bash
git clone https://github.com/enclava-labs/enclava-dev-skills ~/.pi/agent/skills/enclava-dev-skills
```
