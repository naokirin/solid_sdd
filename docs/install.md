# Installing into a project

**Supported path:** `scripts/install-into-project.sh` installs **skills + mechanical tooling** (lint / run-state / next / host-toolchain, schemas, optional kg) into the consuming project. This is the only supported consumer install.

Agent Skills packages live under `skills/` for the installer to copy; do not use a separate skill-only install channel.

## Prerequisites

- Bash, `git` (for remote install), Python 3 (`venv`)
- Optional: Go (only with `--with-kg`)
- An Agent Skills host: Cursor, Claude Code, Copilot, Codex, or Devin

## Install

### Without cloning this repo

Fetch the installer from GitHub and run it (sparse-fetches the install payload; `--ref` defaults to `main`):

```bash
# at the consuming project
curl -fsSL https://raw.githubusercontent.com/naokirin/solid_sdd/main/scripts/install-into-project.sh | \
  bash -s -- --project-root . --agent cursor

# pin a tag / other ref
curl -fsSL https://raw.githubusercontent.com/naokirin/solid_sdd/main/scripts/install-into-project.sh | \
  bash -s -- --project-root . --agent cursor --ref v0.1.0 --force
```

### From a solid_sdd checkout

```bash
# at the consuming project — install for Cursor (skills → .agents/skills/)
/path/to/solid_sdd/scripts/install-into-project.sh \
  --project-root . \
  --agent cursor

# Cursor + Claude Code (skills land in .agents/skills and .claude/skills)
/path/to/solid_sdd/scripts/install-into-project.sh \
  --project-root . \
  --agent cursor,claude-code \
  --force

# Pin a GitHub ref (sparse fetch; no full clone left behind)
/path/to/solid_sdd/scripts/install-into-project.sh \
  --project-root . \
  --agent copilot \
  --repo naokirin/solid_sdd \
  --ref v0.1.0 \
  --force
```

### What gets installed

| Piece | Default location |
|-------|------------------|
| Vendor tree (scripts, schemas, skill copies, rules) | `.solidsdd/vendor/solid_sdd/` (override with `--vendor-dir`) |
| Install metadata | `.solidsdd/tooling.json` (`vendor_root`, `scripts_dir`, …) |
| Path layout config | `.solidsdd/config.yaml` (created if missing) |
| Skills for agent | see table below |
| Cursor project rule | `.cursor/rules/solidsdd.mdc` (when `--agent` includes `cursor`) |
| Python deps | `<vendor>/.venv` (`jsonschema`, `PyYAML`) |
| Knowledge graph (optional) | `--with-kg` → `tools/solidsdd-kg` + `bin/solidsdd-kg` |

### Agent skill directories (project scope)

| `--agent` | Skills directory |
|-----------|------------------|
| `cursor`, `copilot`, `codex` | `.agents/skills/solidsdd-*` (shared) |
| `claude-code` | `.claude/skills/solidsdd-*` |
| `devin` | `.devin/skills/solidsdd-*` |

Only paths listed in [`scripts/install-manifest.txt`](../scripts/install-manifest.txt) are vendored (not a full repo clone).

### Custom vendor location

```bash
./scripts/install-into-project.sh \
  --project-root /path/to/app \
  --vendor-dir tools/solid_sdd \
  --agent cursor \
  --force
```

Agents and docs should resolve CLIs via `.solidsdd/tooling.json` → `scripts_dir` (default `.solidsdd/vendor/solid_sdd/scripts`).

## Contract layout

Defaults (overridable via `.solidsdd/config.yaml`):

```text
your-project/
  .solidsdd/
    config.yaml
    tooling.json
    vendor/solid_sdd/          # installer output
      scripts/
      schemas/
      skills/
      rules/
  .agents/skills/solidsdd-*/   # or .claude/skills / .devin/skills
  .cursor/rules/solidsdd.mdc   # Cursor
  openapi/ contracts/ …
```

## Smoke check

1. `.solidsdd/tooling.json` exists and `scripts_dir` points at vendored scripts
2. Agent host lists `solidsdd-*` skills
3. Run:
   ```bash
   .solidsdd/vendor/solid_sdd/scripts/solidsdd-host-toolchain.sh --project-root .
   .solidsdd/vendor/solid_sdd/scripts/solidsdd-lint.sh --project-root . --pretty   # needs an active change
   ```
4. Ask the agent to run `solidsdd-context`, then a small `solidsdd-loop` / `solidsdd-run`
5. (Optional) `--with-kg` then `…/scripts/solidsdd-kg.sh build --root .`

### Breaking note (ChangeBrief)

`in_scope` / `out_of_scope` / `success_criteria` are **`{ "id", "text" }` objects**. WorkPlan items require `covers`; Scenarios should carry matching `@R1` / `@SC1` tags. See [hardening-plan.md](hardening-plan.md).

For automatic execution:

- **One property-level Gherkin Scenario** → `solidsdd-loop`
- **Multiple / larger requirements** → `solidsdd-run`

The parent must launch subagent-required skills (other than context) via Task (see `references/execution-model.md`).

## Maintainers: distribution prep

After changing skill bodies / adapters:

```bash
scripts/sync-skill-references.sh
scripts/sync-skill-references.sh --check
scripts/check-skill-frontmatter.sh
```

Consumers install with `install-into-project.sh` (curl from GitHub, local checkout, or `--repo` / `--ref`). Keep `scripts/install-manifest.txt` in sync with what the installer must ship.

- `adapters/`, `schemas/`, `docs/`, `rules/`, and `reference-src/` are edit sources. **Distributed skill truth is `skills/*/references/`**
- Installer payload is **`scripts/install-manifest.txt`**

Edits via AI agents auto-sync:

- Cursor: `.cursor/hooks.json` (`afterFileEdit`)
- Claude Code: `.claude/settings.json` (`PostToolUse` / `Edit|Write|MultiEdit`)

```bash
scripts/install-git-hooks.sh   # once (pre-commit drift check)
```

## Updates

Re-run the installer with `--force` (same `--agent` / `--vendor-dir` / `--ref` as needed):

```bash
curl -fsSL https://raw.githubusercontent.com/naokirin/solid_sdd/main/scripts/install-into-project.sh | \
  bash -s -- --project-root . --agent cursor --force

# or from a checkout
/path/to/solid_sdd/scripts/install-into-project.sh \
  --project-root . --agent cursor --force
```

If you customized `.cursor/rules/solidsdd.mdc`, back it up before `--force` (rule file is overwritten for Cursor).

## Adoption checklist

### Required

- [ ] `install-into-project.sh` succeeded for your agent(s)
- [ ] `.solidsdd/tooling.json` present; lint/run-state scripts resolve under `scripts_dir`
- [ ] Agent lists `solidsdd-*` (run / loop / context / intake / brief / decompose / judge / critique / apply-* / derive-tests / implement / verify, plus formal)
- [ ] (Cursor) `.cursor/rules/solidsdd.mdc` installed; set **Working language** (`en` or `ja`)
- [ ] Shared contract layout ([project-template.md](project-template.md)), including `.solidsdd/config.yaml` paths
- [ ] Smoke of `solidsdd-context` + `solidsdd-loop` or `solidsdd-run` (critique via Task; lint runs when vendored scripts are available)
- [ ] Contract tests via the project’s `npm test` / `bundle exec rspec` / etc.

### Optional

- [ ] `--with-kg` and knowledge consult/harvest path
- [ ] GraphQL / Ruby / Formal stacks as needed

### Coexistence

- [ ] Role split with NL SDD tools ([coexistence.md](coexistence.md))

## Related docs

- [adapters.md](adapters.md) — OpenAPI / GraphQL / OCL / formal
- [execution-model.md](execution-model.md)
- [architecture.md](architecture.md)
- [phase4.md](phase4.md)
- [../skills/README.md](../skills/README.md)
