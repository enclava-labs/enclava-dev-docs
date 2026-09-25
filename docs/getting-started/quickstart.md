---
sidebar_position: 1
---

# Quickstart

Install the `enclava` CLI, log in with your Enclava account, and deploy either a template or your own container image.

<Flow>

1. **Install the CLI**: from a release artifact or from source.
2. **Log in**: approve the CLI session in your browser.
3. **Deploy**: a ready-made template or your own signed image.
4. **Check it's running**: `enclava status` confirms the app passed its checks.

</Flow>

## Prerequisites

- An Enclava account and organization.
- The `enclava` CLI (see below).
- For the SSH template, an SSH public key such as `~/.ssh/id_ed25519.pub`.

## Install the CLI

Use a release artifact when one is available. To build the current CLI from source on Debian or Ubuntu (including WSL), you need Rust 1.85 or newer:

```bash
sudo apt-get update
sudo apt-get install -y pkg-config libssl-dev
export ENCLAVA_PLATFORM_RELEASE_ROOT_PUBKEY_HEX=5b9437adeaffbe8f41b13d96ed49d2f51cd6c266cd8ecc284b0552ec4912b8dd
cargo install --git https://github.com/enclava-labs/cap --locked enclava-cli
```

`ENCLAVA_PLATFORM_RELEASE_ROOT_PUBKEY_HEX` is a public verification key, not a secret. It pins the release signing key the CLI trusts, so the CLI only accepts genuine Enclava platform releases.

## Log in

```bash
enclava login
enclava whoami
```

`login` opens your browser so you can approve the CLI session in the Enclava console. After approval, the CLI stores its credentials locally. `whoami` shows your account and active organization.

## Choose a deploy path

Deploy a template when one already matches what you need:

```bash
enclava template list
enclava template deploy debian-ssh-frp --name shell \
  --ssh-public-key-file ~/.ssh/id_ed25519.pub
enclava template ssh-command --name shell --wait
```

Deploy your own container image when you need to run your own code:

```bash
enclava init
enclava create --signer-subject <cosign-subject>
enclava deploy --image <registry>/<image>@sha256:<digest>
enclava status
```

Your own image must be pinned by digest and signed by the identity you register with `--signer-subject`. Templates handle that for you. [Deploy your own image](./manual-oci-deploy.md) walks through the full flow.

## Check the deploy

For the SSH template, get the SSH command and check the app status:

```bash
enclava template ssh-command --name shell --wait
enclava status --app shell
```

For your own image, check the rollout and read the logs:

```bash
enclava status
enclava logs
```

If your app uses password-protected storage, the first deploy claims ownership and later restarts need an unlock. See [Storage, unlock and recovery](../guides/storage-and-recovery.md).
