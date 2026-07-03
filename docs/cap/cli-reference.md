---
sidebar_position: 3
---

# CAP CLI Reference

The `enclava` CLI is the primary user interface for CAP and hosted PaaS deploy flows.

## Account and context

```bash
enclava login
enclava whoami
enclava logout
```

## App lifecycle

```bash
enclava init
enclava create --signer-subject <cosign-subject>
enclava deploy --image <registry>/<image>@sha256:<digest>
enclava status
enclava logs
enclava rollback
enclava destroy
```

`deploy` requires a digest-pinned image. For password-mode apps, ownership and unlock commands may be needed depending on the app state.

## Config and secrets

```bash
enclava config set KEY=value
enclava config list
```

Use config commands to deliver application settings through CAP rather than baking secrets into images.

## Hosted templates

```bash
enclava template list
enclava template deploy debian-ssh-frp --name shell \
  --ssh-public-key-file ~/.ssh/id_ed25519.pub
enclava template ssh-command --name shell --wait
```

`--json` is available on template deployment and SSH command inspection for automation.

## Ownership and recovery

```bash
enclava claim
enclava unlock
enclava recover
enclava change-password
enclava key backup --out enclava-recovery.json
```

Password-mode workloads protect state with owner-controlled material. Back up recovery material immediately after setup and store it separately from application code.

## Organizations and signer identity

```bash
enclava org
enclava signer
enclava key
```

CAP uses org keyrings and signer identity to decide whether the local CLI key can deploy and whether an image was produced by an authorized identity.
