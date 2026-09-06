# Workspace publication — 2026-09-06

## Scope and result

Audited all 14 distinct Git object stores (12 GitHub repositories) discovered
under `/home/user/platform`, including linked worktrees. Fetched each origin and
verified that every pre-existing local branch commit is now reachable through an
origin branch. The newly active `feat/managed-write-status-timings` implementation
is separate ongoing work, not part of this archival snapshot.

Reviewed uncommitted source and documentation was committed and pushed on
`archive/20260906/*` branches. Historical unpublished branch tips were preserved
under the same namespace, without rewriting history or merging their contents.
These are recovery snapshots, not implementation approval or release candidates.
Some contain superseded or unfinished changes, including stopped preprod replicas;
do not promote them wholesale.

Latest completed speed evidence was also pushed to its existing feature branches:

- PaaS `fix/confidential-deploy-speed`: `a7d9079`.
- PaaS `fix/kds-relay-speed`: `88f75cc`.
- Ops `fix/dev-kds-speed`: `657a877`.

The measured DEV result is preserved alongside this report in
[DEV-CONFIDENTIAL-SPEED-2026-09-06.md](DEV-CONFIDENTIAL-SPEED-2026-09-06.md).

## Safety and exclusions

No default or environment branch was advanced, no tags were pushed, and no
environment was accessed or reconciled. Preprod remains untouched. Workflow
filters at archival heads were checked; the strfry snapshot additionally uses
`[skip ci]` because its existing push workflow publishes a mutable image on every
branch. GitHub reported no run for that archival branch after publication.

Added source/docs were inspected and scanned for likely credential signatures;
identified private-key header strings were negative test fixtures, not keys.
This is a scoped publication review, not proof that all historical code is secure.

Excluded from publication: plaintext credentials, private evidence/backups,
generated Python bytecode, and two sensitive PaaS stashes. Of the 17 retained
stashes, 13 reviewed snapshots were separately published as `archive/20260906/stash-*`;
two were already fully content-redundant remotely. Original stash merge parents
were not pushed. One old docs-only snapshot was placed on current main ancestry
to avoid importing 150 unreviewed historical commits. All original stashes remain
local; none was applied or deleted. The workspace root is not a Git repository;
other root-level files and raw test-results were not bulk imported. Only the
reviewed speed summary above was copied into this existing documentation repo.

## Verification method

For each local branch except the explicitly ongoing new implementation, checked
`git rev-list --count <branch> --not --remotes=origin` after fetching origin.
All returned zero. Local default branches may intentionally remain behind or
diverged from their same-named remote: the unique work is preserved on archive
refs, not force-pushed over integration or deployment authority.
