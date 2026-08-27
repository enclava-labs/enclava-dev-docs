---
sidebar_position: 1
---

# Quickstart

The fastest path is to use the hosted CLI flow against Enclava PaaS. This gives you browser login, organization context, and access to hosted templates without operating CAP yourself.

## Prerequisites

- An Enclava account and organization.
- The `enclava` CLI from the CAP project or a release artifact.
- Rust 1.85 or newer when building the CLI from source.
- For SSH templates, an SSH public key such as `~/.ssh/id_ed25519.pub`.

## Install the CLI

Use a release artifact when one is available. To build the current CLI from source on Debian or Ubuntu (including WSL):

```bash
sudo apt-get update
sudo apt-get install -y pkg-config libssl-dev
export ENCLAVA_PLATFORM_RELEASE_ROOT_PUBKEY_HEX=5b9437adeaffbe8f41b13d96ed49d2f51cd6c266cd8ecc284b0552ec4912b8dd
cargo install --git https://github.com/enclava-labs/cap --locked enclava-cli
```

`ENCLAVA_PLATFORM_RELEASE_ROOT_PUBKEY_HEX` is a public verification key, not a secret. It pins the platform-release signing root accepted by the CLI.

## Log in

```bash
enclava login
enclava whoami
```

The CLI supports hosted device login. The hosted console approval route is `/cli/login`; after approval, the CLI stores credentials locally and talks to the shared hosted API surface.

## Choose a deploy path

Use a hosted template when the template already matches your workload:

```bash
enclava template list
enclava template deploy debian-ssh-frp --name shell \
  --ssh-public-key-file ~/.ssh/id_ed25519.pub
enclava template ssh-command --name shell --wait
```

Use manual OCI deployment when you need to deploy your own container image:

```bash
enclava init
enclava create --signer-subject <cosign-subject>
enclava deploy --image <registry>/<image>@sha256:<digest>
enclava status
```

Manual deployments require a digest-pinned image and a signer identity that matches the image signature policy. Hosted templates hide most of that detail behind a supported template contract.

## What to verify after deploy

For hosted SSH templates, verify that the platform and workload agree on the stable endpoint:

```bash
enclava template ssh-command --name shell --wait
enclava status --app shell
```

For manual apps, verify rollout and runtime state:

```bash
enclava status
enclava logs
```

If the app uses password-mode storage, the first deploy may require an ownership claim and later restarts may require unlock. See [CAP CLI reference](../cap/cli-reference.md).
