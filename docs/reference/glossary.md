---
sidebar_position: 2
---

# Glossary

**Confidential workload**: An application deployed so runtime secrets and state are released only inside a verified confidential runtime.

**SEV-SNP**: AMD Secure Encrypted Virtualization with Secure Nested Paging, used for hardware-backed guest memory isolation and attestation.

**TEE**: Trusted execution environment, an isolated execution context that can produce attestation evidence.

**Remote attestation**: A protocol for proving what code and configuration is running inside a TEE.

**Deployment record**: Signed document binding the image, app, deploy ID, policy, expected runtime, and who deployed it.

**Org keyring**: Organization-level trust material that defines which deployment keys are authorized.

**`enclava-init`**: The startup check that runs inside your TEE and verifies everything before your app starts.

**Stable SSH endpoint**: The `host:port` Enclava reserves for an SSH template app; it stays the same across restarts.

**`tee_error`**: Failure reason surfaced by `enclava status` when `enclava-init` cannot complete startup. Check it first when a deploy stalls.

**Owner seed**: The random secret generated inside your TEE on the first claim. Your storage keys derive from it; the recovery mnemonic encodes it.
