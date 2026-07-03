---
sidebar_position: 2
---

# Glossary

**CAP**: Enclava's open-source control plane for confidential application deployment.

**Confidential workload**: An application deployed so runtime secrets and state are released only inside a verified confidential runtime.

**Kata confidential containers**: The Kubernetes runtime model Enclava targets for VM-backed container isolation.

**SEV-SNP**: AMD Secure Encrypted Virtualization with Secure Nested Paging, used for hardware-backed guest memory isolation and attestation.

**TEE**: Trusted execution environment, an isolated execution context that can produce attestation evidence.

**Remote attestation**: A protocol for proving what code and configuration is running inside a TEE.

**Trustee/KBS**: Key broker service used to release protected resources after attestation and policy checks.

**Deployment descriptor**: Signed CAP document binding image, app, deploy ID, policy, expected runtime claims, and deployer identity.

**Org keyring**: Organization-level trust material that defines which deployment keys are authorized.

**Platform release**: Signed release envelope containing platform image, policy, and runtime constants consumed by CAP API and CLI.

**`enclava-init`**: Runtime sidecar that runs inside the guest and verifies the trust chain before releasing readiness.

**Stable SSH endpoint**: PaaS-reserved `host:port` contract for hosted SSH templates.
