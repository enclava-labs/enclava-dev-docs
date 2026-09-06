# Environment Release Isolation: Incident, Remediation, and Learnings

**Report date:** 2026-08-13

**Change window:** 2026-08-12

**Systems:** Enclava Infra, CAP, Enclava PaaS, Enclava Ops Manifests, dev, preprod, and coco-dev

## Executive summary

Deploying changes intended for one Enclava environment could affect another because environment identity, desired topology, and release version were not fully separated. Flux sources followed shared or temporary branches, the repository root aggregated environment resources, and runtime applications could apply database migrations during ordinary startup. A preprod rollout also exposed a separate fail-closed admission behavior: healthy replacement pods were intentionally excluded from public Services until they received a runtime admission label.

We implemented a release-isolation model across four repositories:

- `master`/`main` remains an integration branch and is not an environment release target.
- Kubernetes environments have dedicated release branches: `dev` and `preprod`.
- Each environment has a dedicated Kustomize entry point: `clusters/enclava-work` and `clusters/preprod`.
- CAP and PaaS images are built and signed after application changes merge.
- Environment promotion records exact image digests, exact migration versions, and new immutable migration Job names.
- Migration Jobs apply schema changes; API and worker processes verify the complete migration ledger and do not mutate it during normal production startup.
- CI rejects changes that cross an environment boundary.
- Preprod stays suspended between reviewed reconciliations and keeps public traffic fail-closed until runtime admission succeeds.

All six remediation PRs were merged. At the end of the change window, dev and preprod were healthy, reconciled from their dedicated branches, ran the promoted signed images, and had exact CAP 46 / PaaS 69 migration ledgers with zero failed rows.

There are two important qualifications:

1. The normal preprod real-SNP admission canary could not run because its private release environment was unavailable on the runner. The gate failed closed. Service was restored using runtime-only pod admission after exact Flux, image, database, Job, ownership, readiness, and EndpointSlice checks. No admission label was restored to a Deployment template.
2. A 2026-08-13 re-audit found that dev had subsequently been repointed from `dev` to `agent/dev-signing-readiness`. It remains healthy and is not on `master`, but this bypasses the intended reviewed environment-promotion lane. The architecture is implemented; cluster-side enforcement against later manual drift is not yet complete.

## Scope

The work covered:

- `enclava-infra`: authoritative Flux source branch, path, and suspension configuration.
- `cap`: migration ownership and complete-ledger verification.
- `enclava-paas`: migration ownership, complete-ledger verification, and safe production defaults.
- `enclava-ops-manifests`: environment branches, environment entry points, promotion contracts, CI scope checks, and preprod contained rollout.
- Live dev and preprod cutover and verification.

The work did not originally cover coco-dev. Coco-dev is a shared Docker Compose integration stack rather than a Flux-managed Kubernetes environment. Its omission is documented below as a remaining architecture gap.

## What was failing

### 1. A shared integration ref could drive more than one environment

The primary architectural problem was that an integration branch could also be a live deployment source. A merge intended to make code available for review or later promotion could therefore become an environment change without a separate release decision.

This violated the required operating model:

> Anyone may merge into the integration branch, but an environment changes only when a release is explicitly promoted to that environment.

### 2. Repository path and release version were conflated

Folders and branches solve different problems:

- A folder answers **what topology belongs to this environment?**
- A branch answers **which reviewed version of that topology is this environment running?**

A folder-only model can separate manifests, but if both clusters follow the same branch, a single commit can still advance both folders at once. A branch-only model can freeze versions independently, but without environment-specific entry points it can still reconcile an overly broad aggregate.

The correct model uses both:

| Environment | Release branch | Kustomize path |
| --- | --- | --- |
| Dev | `dev` | `./clusters/enclava-work` |
| Preprod | `preprod` | `./clusters/preprod` |

### 3. Runtime processes could own schema mutation

CAP and PaaS previously allowed application startup to apply migrations. That creates several failure modes:

- Multiple replicas can race for migration ownership.
- A new application image can change schema before the rollout is proven healthy.
- Rolling back the application does not necessarily roll back the database.
- Deploying an image to one environment can produce a schema state different from its reviewed GitOps release.

Migration ownership needed to move to one immutable, observable release Job.

### 4. Migration verification checked too little state

Checking only the highest successful migration version is insufficient. A ledger may report the expected maximum while still containing:

- a failed row;
- a missing earlier migration;
- a reordered or unexpected migration;
- a checksum that no longer matches the embedded migration source.

The verifier now checks the full ordered SQLx ledger, including version, success state, and checksum, against the migrations embedded in the running binary.

### 5. Preprod public traffic is intentionally fail-closed

Preprod public Services select only runtime pods carrying:

```text
rollout.enclava.dev/public-admission=verified
```

The label is intentionally not part of a Deployment template. Replacement pods are healthy internally but receive no public endpoints until an exact-release trust proof admits those specific pod UIDs.

During the incident, a direct `master` hotfix added the label to Deployment templates to restore service. That made the endpoints return, but it bypassed the admission design. The remediation removed the template labels and restored runtime-only admission.

### 6. Preprod was not guaranteed to remain contained

The initial infra change selected the correct `preprod` branch and path but still declared `suspend: false`. That conflicted with the contained-rollout contract. It was corrected before merge so authoritative infra now keeps preprod suspended except during an explicit reviewed reconcile.

## Root-cause model

| Layer | Root cause | User-visible effect | Remediation |
| --- | --- | --- | --- |
| Release control | Integration branch also acted as deployment source | A merge could alter a live environment | Dedicated `dev` and `preprod` release branches |
| Manifest scope | Broad/root reconciliation and insufficient path boundaries | Unrelated environment resources could be included | Dedicated cluster entry points and CI scope validation |
| Database lifecycle | API/worker startup could apply migrations | Replica races and schema/application mismatch | Immutable migration Jobs; runtime verification only |
| Verification | Maximum-version check ignored dirty/checksum state | Corrupt or divergent ledgers could appear valid | Exact full-ledger comparison |
| Preprod exposure | Runtime admission behavior was not accounted for during pod replacement | Healthy pods but zero public endpoints and HTTP 503 | Controlled runtime admission of exact pod UIDs |
| Infra defaults | Preprod was configured unsuspended | Future Ansible runs could reconcile without the contained rollout | Authoritative `suspend: true` |
| Enforcement | Live Flux objects can still be manually repointed | Later drift can bypass the reviewed lane | Add admission/policy and drift monitoring |

## Final architecture

```text
application change
        |
        v
CAP main / PaaS main
        |
        | post-merge signed build
        v
signed digest + migration metadata
        |
        | explicit environment promotion PR
        +------------------------------+
        |                              |
        v                              v
ops branch: dev                 ops branch: preprod
path: clusters/enclava-work     path: clusters/preprod
        |                              |
        v                              v
dev Flux                       preprod contained rollout
continuous reconcile           suspended -> exact reconcile -> suspended
                                       |
                                       v
                              runtime-only public admission
```

### Integration and release branches

The integration branch contains the combined code and configuration history. It is not an environment.

The release branches are environment pointers:

- Merging to integration makes a change eligible for promotion.
- Updating `dev` changes only dev.
- Updating `preprod` changes only preprod.
- The two environments can run different commits and image digests indefinitely.
- Rollback is an environment-branch operation, not an integration-branch rewrite.

### Environment folders

Environment entry points bound Flux to the intended topology:

- `clusters/enclava-work/kustomization.yaml`
- `clusters/preprod/kustomization.yaml`

The repository root remains a legacy aggregate. It must not be used by Flux. The root still includes preprod resources, so preventing path regression to `.` remains an important policy requirement.

### Image and database release unit

A CAP or PaaS release is treated as a tuple:

```text
source commit
+ signed image digest
+ embedded migration version
+ immutable migration Job name
+ runtime verification mode
```

The environment manifest must agree on every value. For example, the migration Job name includes the digest prefix and migration version. Changing the image requires a new Job name, preventing Kubernetes from treating an old completed Job as proof for a new image.

### Migration ownership

The release sequence is:

1. Run the immutable migration Job with the database-owner credential.
2. Wait for the exact Job to complete.
3. Verify the database ledger matches the image's embedded migrations.
4. Start API and worker processes with `DATABASE_MIGRATION_MODE=verify`.
5. Fail readiness/startup if the full ledger is not exact.

PaaS also defaults to verification when `APP_ENV=production` even if the explicit migration-mode variable is absent. Local development retains the existing apply behavior unless it opts into verification.

### Preprod contained rollout

Preprod differs from dev intentionally:

- Flux begins suspended.
- Public CAP/PaaS Services begin locked.
- The release is reconciled at an exact reviewed commit.
- Exact Jobs, images, image IDs, ledgers, ownership, and readiness are proven.
- Flux returns to unpinned `preprod` branch tracking but stays suspended.
- Runtime admission labels only the exact proven API pod UIDs.
- Deployment templates remain permanently free of the admission label.

## Changes delivered

| Repository / PR | Merge commit | Main result |
| --- | --- | --- |
| [enclava-infra #27](https://github.com/enclava-labs/enclava-infra/pull/27) | `e8129353fb593e435939165ead8c5a03457662eb` | Flux defaults select `dev`/`preprod`, use environment paths, and keep preprod suspended. |
| [CAP #86](https://github.com/enclava-labs/cap/pull/86) | `5d17ebc0b9aa6ca252b39400f50a448061fc7c00` | Runtime migration verification, exact ledger/checksum checks, explicit deploy verification mode, and dependency audit fix. |
| [PaaS #58](https://github.com/enclava-labs/enclava-paas/pull/58) | `3b79dc62645011805df1edbbf90bad3aca776c2e` | Exact ledger verification and production-safe default to verify mode. |
| [Ops #95](https://github.com/enclava-labs/enclava-ops-manifests/pull/95) | `f438801bd1a8140ea574badac8dc173bedaf65cf` | Preprod release branch, exact signed image promotion, environment entry point, and rollout contract. |
| [Ops #96](https://github.com/enclava-labs/enclava-ops-manifests/pull/96) | `928d089c9c8ada6b9c2297d41aac53131be81155` | Integration-only master behavior, environment scope checks, and removal of emergency template admission labels. |
| [Ops #97](https://github.com/enclava-labs/enclava-ops-manifests/pull/97) | `77f26bcdb8952c8f0febe5b38810a5d2eb3f2ff3` | Dev release branch and exact signed image promotion. |

Every PR was opened as a non-draft PR and received an `@codex review` request. Actionable review findings were addressed before merge.

## Review findings that materially improved the design

### CAP

- Verification originally used only the maximum successful migration version.
- It was expanded to reject failed rows, missing/unexpected versions, and checksum mismatches.
- The standalone API deployment was explicitly set to verification mode.
- `webbrowser` was upgraded from 1.2.1 to 1.2.2 to resolve `RUSTSEC-2026-0257`.

### PaaS

- Verification was expanded from maximum version to the exact migration ledger.
- Because the production image set `APP_ENV=production` but did not guarantee an explicit migration-mode variable in every consumer, production now defaults to `verify`.
- Explicit mode still wins, preserving deliberate migration commands and local workflows.

### Infra

- A final audit caught `suspend: false` for preprod.
- The authoritative default was changed to `suspend: true` and covered by a regression test.

## Deployment and recovery sequence

The merge and deployment order mattered:

1. Merge CAP and PaaS application changes.
2. Wait for post-merge signed image workflows.
3. Download and verify release artifacts.
4. Promote exact digests and migration metadata to both environment PRs.
5. Run environment-scope checks, Kustomize renders, release-contract tests, rollout tests, and server-side Kubernetes dry-runs.
6. Merge the `dev` and `preprod` release PRs.
7. Switch dev to its environment branch and path; verify convergence.
8. Suspend and lock preprod.
9. Remove the emergency admission label from live Deployment templates.
10. Reconcile the exact preprod commit once and return Flux to suspended branch tracking.
11. Attempt the reviewed admission flow.
12. When the private real-SNP canary input was unavailable, retain the fail-closed state and perform runtime-only admission after exact control-plane verification.
13. Merge the integration PR only after neither environment followed `master`.

This dependency-aware order prevented the integration merge that removed emergency labels from taking preprod down while preprod still followed `master`.

## Verification performed

### Application and repository checks

- CAP focused migration-ledger tests.
- CAP image workflow contract tests.
- CAP `cargo clippy` with warnings denied.
- CAP dependency audit.
- PaaS database tests, including production/local migration-mode defaults.
- PaaS `cargo clippy` with warnings denied.
- PaaS image workflow contract tests.
- Infra full Python test suite: 26 tests passed.
- Ops environment isolation tests.
- Ops exact release-contract verifier for dev and preprod.
- Ops signed platform-release verification.
- Ops full contained-rollout regression suite.
- Kustomize rendering for both environment entry points.
- Server-side Kubernetes dry-run for CAP and PaaS manifests.
- GitHub Actions and review-thread audit before merge.

### Completion snapshot on 2026-08-12

| Check | Dev | Preprod |
| --- | --- | --- |
| Flux branch | `dev` | `preprod` |
| Flux path | `./clusters/enclava-work` | `./clusters/preprod` |
| Flux Ready | Yes | Yes |
| Suspension | Continuous | Suspended between releases |
| CAP image | `de3540dd...f357` | `de3540dd...f357` |
| PaaS image | `a20b1b0e...c957` | `a20b1b0e...c957` |
| CAP ledger | `46`, zero failed | `46`, zero failed |
| PaaS ledger | `69`, zero failed | `69`, zero failed |
| Runtime migration mode | `verify` | `verify` |
| CAP/PaaS/identity public checks | HTTP 200 | HTTP 200 |

## Current-state re-audit on 2026-08-13

The re-audit distinguishes the delivered architecture from subsequent live changes.

### Preprod

Preprod remains aligned with the intended model:

- Flux branch: `preprod`
- Applied revision: `preprod@sha1:f438801bd1a8140ea574badac8dc173bedaf65cf`
- Path: `./clusters/preprod`
- Suspended: yes
- Ready: yes
- CAP ledger: 46, zero failed
- PaaS ledger: 69, zero failed
- CAP/PaaS Deployment templates: admission label absent
- CAP, PaaS, and identity endpoints: HTTP 200

### Dev

Dev is healthy but has drifted from the intended release lane:

- Flux branch: `agent/dev-signing-readiness`
- Applied revision: `agent/dev-signing-readiness@sha1:54f19b50b651c6e3a39162f86dccab78dbd9afef`
- Path: `./clusters/enclava-work`
- Suspended: no
- Ready: yes
- CAP ledger: 46, zero failed
- PaaS ledger: 69, zero failed
- CAP, PaaS, and identity endpoints: HTTP 200

This does not violate the literal rule “not on master,” but it violates the stronger architectural rule “an environment changes only through its environment release branch.” A manual patch or another automation can still repoint the live Flux source.

### Enforcement implication

Git configuration expresses desired state but does not by itself prevent privileged live mutations. The next control should reject or alert on any live Flux source branch outside an environment allowlist:

```text
dev     -> branch must equal dev
preprod -> branch must equal preprod
```

## Coco-dev assessment

Coco-dev is operational but not release-isolated.

It is a Docker Compose stack at `/home/user/platform/enclava-paas` on the `coco-dev` host, exposed at:

- PaaS: `http://100.65.73.114:8080`
- CAP: `http://100.65.73.114:4000`
- ZITADEL: `http://100.65.73.114:8081`

The 2026-08-13 audit found:

- PaaS, CAP, and ZITADEL health endpoints returned HTTP 200.
- PaaS checkout was on `main` with 122 dirty files.
- CAP checkout was on `main` with one dirty file.
- CAP/PaaS images were local, unlabeled, and unversioned.
- PaaS API and worker migration mode was unset under `APP_ENV=local`.
- PaaS database was at migration 68 with zero failed rows.
- CAP database was at migration 45 with zero failed rows.
- The promoted Kubernetes release expected CAP 46 and PaaS 69.

Coco-dev therefore proves fast integration behavior, but it does not prove release reproducibility or the GitOps isolation model.

### Recommended coco-dev release lane

The minimum consistent design is:

1. Create a `coco-dev` release branch or an equivalent immutable release manifest.
2. Consume digest-pinned CAP and PaaS images rather than building a dirty checkout.
3. Record exact CAP/PaaS source commits and migration versions.
4. Run one-shot migration containers before API/worker startup.
5. Set API and worker runtime migration mode to `verify`.
6. Verify Compose service health, exact image IDs, and exact database ledgers.
7. Keep local source-build mode available as a disposable developer workflow, but do not call it an environment promotion.

## Key learnings

### Architecture

1. **An integration branch is not an environment.** Merge availability and deployment authorization must be separate events.
2. **Branches and folders are complementary.** Branches isolate release time/version; folders isolate topology and reconciliation scope.
3. **Release identity is a tuple, not a tag.** Image digest, migration version, immutable Job, source revision, and runtime mode must agree.
4. **Database mutation needs one owner.** An observable Job is safer than every replica independently deciding whether to migrate.
5. **Verification must compare complete state.** A maximum version is not proof of an exact SQLx ledger.
6. **Desired state needs live enforcement.** Privileged operators can patch Flux away from Git-defined intent unless policy or monitoring rejects drift.

### GitOps and operations

1. **Merge order is a safety mechanism.** Environment branches had to be ready before master stopped carrying the emergency workaround.
2. **Fail-closed systems can look broken while behaving correctly.** Healthy pods with no public endpoints were awaiting admission, not failing readiness.
3. **Emergency fixes must not become templates.** A runtime admission label in a Deployment template permanently bypasses the trust gate.
4. **Preprod suspension is part of the release protocol.** Correct branch/path with `suspend: false` was still unsafe.
5. **The repository root remains hazardous.** Even if current Flux paths are narrow, a future path regression to `.` can revive aggregate behavior.
6. **Scope validation belongs in CI.** Human review alone is not reliable protection against cross-environment file changes.

### Testing and review

1. **Review comments found real architecture gaps.** Full-ledger verification and production-safe defaults were not cosmetic changes.
2. **Post-merge artifacts must be used.** A PR image or locally built image is not the signed main-branch release.
3. **Server-side dry-run catches cluster-schema issues without reconciling.** It was useful before either environment branch moved.
4. **Public HTTP checks are necessary but insufficient.** Flux revision, image ID, database ledger, Deployment ownership, and admission state must also be verified.
5. **A green endpoint does not prove the desired release lane.** The 2026-08-13 dev drift is healthy but architecturally noncompliant.

### Process

1. **Audit every repository in a cross-repo release.** Infra, application defaults, migration behavior, and GitOps configuration all contributed.
2. **Do not declare all environments fixed if one deployment system was omitted.** Coco-dev should have been explicitly included or explicitly excluded from the original scope.
3. **Private verification inputs are production dependencies.** The real-SNP admission canary cannot be considered available unless its clean source checkout and private release environment are provisioned on the runner.
4. **Recovery should preserve the safety invariant.** Runtime-only admission restored service without reintroducing a template-level bypass.

## Remaining risks and recommended actions

### Priority 0: restore dev to its approved release lane

- Determine why dev was repointed to `agent/dev-signing-readiness`.
- Promote the intended commit to `dev` through a reviewed PR.
- Change the live Flux source back to `dev`.
- Re-run exact image, ledger, and endpoint verification.

### Priority 0: enforce Flux source policy

- Add a cluster policy or controller check that rejects non-allowlisted source branches and paths.
- Alert when live branch/path differs from the environment contract.
- Treat `master`, `main`, `agent/*`, and arbitrary commit pins as invalid steady state for live environments.
- Allow temporary exact commit pins only inside the preprod rollout controller and require their removal before completion.

### Priority 1: provision the complete preprod admission gate

- Provide `PAAS_RELEASE_ROOT` as a clean checkout at the signed image revision.
- Provide the private `STABLE_SSH_RELEASE_ENV` on the trusted rollout runner.
- Test the full `preprod-contained-rollout.sh admit` flow before the next image promotion.
- Retain fail-closed behavior when either input is missing.

### Priority 1: isolate coco-dev

- Establish the `coco-dev` promotion contract described above.
- Separate “developer source build” from “shared environment release.”
- Upgrade CAP/PaaS ledgers using explicit migration containers.

### Priority 1: prevent root-path reconciliation

- Add an infra/CI assertion that live environment paths may only be `./clusters/enclava-work` or `./clusters/preprod`.
- Consider deleting or making the legacy root aggregate non-deployable once no supported workflow consumes it.

### Priority 2: improve release observability

- Publish environment branch, applied commit, image digests, migration versions, suspension state, and last promotion time as one dashboard/status artifact.
- Record who or what changed a Flux source branch.
- Alert on runtime/template admission-label violations.

## Definition of done for future environment promotions

A promotion is complete only when all of the following are true:

- The application change is merged.
- Post-merge signed artifacts completed successfully.
- The environment branch records exact digests and migrations.
- The environment scope checker passes.
- Kustomize renders the environment entry point.
- Server-side dry-run succeeds.
- The immutable migration Jobs completed.
- The exact database ledgers have no failed or mismatched rows.
- API and worker runtime mode is `verify`.
- Flux follows only the approved environment branch and path.
- Flux Ready/applied revision equals the environment release commit.
- All Deployments have observed their current generation and have exact ready replicas.
- Running image IDs match the promoted digests.
- Public and internal health checks pass.
- Preprod is suspended after reconciliation.
- Preprod public admission is runtime-only and bound to the proven pod UIDs.
- No unrelated environment changed.

## Final assessment

The original cross-environment failure mode was addressed at the correct architectural boundaries rather than with another deployment convention:

- release authorization moved to environment branches;
- topology moved to environment entry points;
- schema mutation moved to immutable Jobs;
- runtime processes became exact verifiers;
- CI gained environment-scope enforcement;
- preprod retained fail-closed admission and suspension.

The system is substantially safer, and preprod remains aligned with the intended model. The strongest remaining lesson is that configuration alone is not enforcement: dev has already demonstrated that a privileged live patch can bypass the reviewed branch lane while remaining healthy. Closing that policy gap—and bringing coco-dev under an equivalent immutable promotion model—is the next necessary step.
