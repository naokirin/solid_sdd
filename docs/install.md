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

# Set Working language explicitly (skips the interactive prompt)
/path/to/solid_sdd/scripts/install-into-project.sh \
  --project-root . \
  --agent claude-code \
  --language ja \
  --force
```

### What gets installed

| Piece | Default location |
|-------|------------------|
| Vendor tree (scripts, schemas, skill copies, rules) | `.solidsdd/vendor/solid_sdd/` (override with `--vendor-dir`) |
| Install metadata | `.solidsdd/tooling.json` (`vendor_root`, `scripts_dir`, …) |
| Path layout config | `.solidsdd/config.yaml` (created if missing; also holds `working_language`) |
| Skills for agent | see table below |
| Project rule per agent | see table below (skip with `--skip-rule`) |
| Python deps | `<vendor>/.venv` (`jsonschema`, `PyYAML`) |
| Knowledge graph (optional) | `--with-kg` → `tools/solidsdd-kg` + `bin/solidsdd-kg` |

### Project rule / Working language

The installer writes the solid_sdd project rule (contract artifact paths, judgment defaults, …) for every `--agent` you pass, in that agent's own convention:

| `--agent` | Rule file | How it's written |
|-----------|-----------|-------------------|
| `cursor` | `.cursor/rules/solidsdd.mdc` | Whole file (solid_sdd-only; overwritten each install) |
| `devin` | `.devin/rules/solidsdd.md` | Whole file (solid_sdd-only; overwritten each install) |
| `claude-code` | `CLAUDE.md` | Marked block upserted — your existing content is preserved |
| `codex` | `AGENTS.md` | Marked block upserted — your existing content is preserved |
| `copilot` | `.github/copilot-instructions.md` | Marked block upserted — your existing content is preserved |

For `claude-code` / `codex` / `copilot`, the rule body is inserted between `<!-- solid_sdd:begin -->` / `<!-- solid_sdd:end -->` markers; re-running the installer replaces only that block, leaving the rest of the file untouched. Don't hand-edit inside the markers — edit `rules/solidsdd.mdc` in a solid_sdd checkout and re-run the installer instead.

**Every one of those rule files reads `working_language` from `.solidsdd/config.yaml` — the value itself is never written into the rule text.** That's deliberate: with N agents installed, changing the language would otherwise mean editing N files. Instead there's one place to change: `.solidsdd/config.yaml`.

`working_language` is resolved as: `--language TAG` (e.g. `--language ja`) → interactive prompt (asked once, via `/dev/tty`, so it works even under `curl | bash`) → default `en`. A **non-interactive** run without `--language` (no TTY, e.g. CI) leaves an already-configured `working_language` untouched — it only defaults to `en` on a brand-new `.solidsdd/config.yaml`, so re-running the installer in CI can never silently reset your language choice. Pass `--skip-rule` to skip rule / language install entirely.

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
  .devin/rules/solidsdd.md     # Devin
  CLAUDE.md                    # Claude Code (solid_sdd:begin/end block)
  AGENTS.md                    # Codex (solid_sdd:begin/end block)
  .github/copilot-instructions.md  # Copilot (solid_sdd:begin/end block)
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

`.cursor/rules/solidsdd.mdc` and `.devin/rules/solidsdd.md` are solid_sdd-only files and are fully overwritten on re-install — back them up first if you hand-edited them. `CLAUDE.md` / `AGENTS.md` / `.github/copilot-instructions.md` only have their `solid_sdd:begin`/`solid_sdd:end` block replaced; content outside the markers is left alone. `working_language` in `.solidsdd/config.yaml` is never touched by a non-interactive re-install unless you pass `--language`, so re-installing is always safe for that setting.

## Adoption checklist

### Required

- [ ] `install-into-project.sh` succeeded for your agent(s)
- [ ] `.solidsdd/tooling.json` present; lint/run-state scripts resolve under `scripts_dir`
- [ ] Agent lists `solidsdd-*` (run / loop / context / intake / brief / decompose / judge / critique / apply-* / derive-tests / implement / verify, plus formal)
- [ ] Project rule installed for your agent(s) (see table above); `.solidsdd/config.yaml` → `working_language` set as intended (`--language` flag, prompt answer, or edited by hand)
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
