# Enclava Agent Skills

Agent-facing skills for the Enclava platform. The [developer docs](https://docs.enclava.dev)
(`docs/` in this repo) explain *what* things are, for humans reading end to end. These
skills encode *how to operate* — procedures, contracts, and failure triage — in the open `SKILL.md` format (a folder with a YAML-frontmattered `SKILL.md`;
understood by Claude Code, Cursor, Codex, pi, and other coding agents) that coding
agents load on demand. If you deploy or manage enclava apps through an agent (Claude Code, Cursor,
Codex, pi, …), install these so the agent gets the platform's real operational
contract instead of guessing.

## Skills

| Skill | Use when |
| --- | --- |
| [`enclava/`](./enclava/) | Deploying, operating, or troubleshooting apps: manual OCI deploys, hosted templates, status/logs/config, unlock/recovery, rollback/destroy. One spine + three journey references. |
| [`enclava-verify/`](./enclava-verify/) | Independently appraising a running origin or saved proof bundle, authoring trust policies. |
| [`enclava-concepts/`](./enclava-concepts/) | Understanding the platform: TEEs, attestation, encrypted storage, who can read what, honest limits. |

## Install

Skills are plain directories with a `SKILL.md`; any agent that supports the format can
load them. For the common agents:

```bash
# Claude Code — personal skills
git clone https://github.com/enclava-labs/enclava-dev-docs /tmp/enclava-docs
cp -r /tmp/enclava-docs/skills/* ~/.claude/skills/

# pi / generic agents.md-style skill loaders
cp -r /tmp/enclava-docs/skills/* ~/.agents/skills/

# Or keep a checkout and symlink, so a `git pull` updates them:
ln -s /tmp/enclava-docs/skills/enclava ~/.claude/skills/enclava
```

For agent managers with per-project skill directories, copy the skill folders into
that project's skill directory the same way.

## Conventions

- **Accuracy over prose.** Every command, flag, and failure signature here is checked
  against the `enclava` CLI and the developer docs. When the CLI changes, these must
  be swept: run `enclava <cmd> --help` against each command named in a skill and fix
  drift as part of the release.
- **Compatibility.** Skills target the CLI version noted in each skill's frontmatter.
  `enclava --help` output is the tiebreaker for any discrepancy.
- **Docs stay canonical for concepts** (`docs/concepts/`, `docs/reference/glossary.md`);
  skills carry the procedural layer and restating of command-level facts, and link out
  for depth.
- **No secrets in skills.** Skills instruct agents to keep passwords and recovery
  mnemonics out of logs, history, and unrequested files — treat that discipline as
  part of the platform's trust model, and preserve it in any edit.
- **Tenant-grade only.** Everything here works through the `enclava` CLI and public
  surfaces; no operator/cluster-internal procedures belong in these files.

## Contributing

Fixes welcome via PR. Claims must be verifiable against `enclava <cmd> --help`, the
behavior of the current CLI, or the developer docs — cite which in the PR description.
New failure signatures should come from a reproduced incident, not speculation.
