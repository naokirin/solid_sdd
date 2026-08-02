# Installing into a project

solid_sdd skills are **self-contained**. Adapter summaries, schemas, and the execution model ship in each skill’s `references/`, so installing with `gh skill` is enough to run the MVP.

## Prerequisites

- GitHub CLI **v2.90.0+** (`gh skill` command)
- An Agent Skills host such as [Cursor](https://cursor.com/) (`--agent cursor`, etc.)
- MVP: **OpenAPI 3.x + OCL → contract tests** (TypeScript / Vitest evaluation sample)

`gh skill` is a preview feature and may change.

## Recommended: install with `gh skill`

Public repo: [naokirin/solid_sdd](https://github.com/naokirin/solid_sdd). Install from the default branch (or after `gh skill publish`):

```bash
# at the consuming project root
gh skill install naokirin/solid_sdd --all --agent cursor --scope project
```

Per-skill example:

```bash
gh skill install naokirin/solid_sdd solidsdd-loop --agent cursor --scope project
gh skill preview naokirin/solid_sdd solidsdd-loop   # preview before install
```

Pinning:

```bash
gh skill install naokirin/solid_sdd --all --agent cursor --scope project --pin v0.1.0
```

### Install location

For Cursor project scope, skills usually land under **`.agents/skills/solidsdd-*`** (shared with Copilot and others). That may differ from the older `.cursor/skills/`. Confirm the real path with `gh skill list`.

### Project rule (optional but recommended)

`gh skill` does not install Project Rules automatically. Once after install:

```bash
# path after install varies by environment
cp .agents/skills/solidsdd-loop/references/project-rule.mdc .cursor/rules/solidsdd.mdc
```

If the path differs, find `solidsdd-loop/references/project-rule.mdc` via `gh skill list` or file search and copy it.

## Local verification (clone)

```bash
gh skill install --from-local /path/to/solid_sdd --all --agent cursor --scope project
gh skill publish --dry-run /path/to/solid_sdd   # validate before tagging a release
```

## Contract layout for consuming projects

Defaults skills expect (overridable in rules):

```text
your-project/
  openapi/
    openapi.yaml
  contracts/
    *.ocl
  tests/
    contracts/
      *.test.ts
  .agents/skills/solidsdd-*/   # placed by gh skill
  .cursor/rules/solidsdd.mdc   # copied as above (recommended)
```

You can install without creating these yet. `solidsdd-context` → `solidsdd-judge` (or `solidsdd-loop` / `solidsdd-run`) is expected to detect and generate what is missing.

## Smoke check

1. `gh skill list` shows `solidsdd-*`
2. Ask the agent to run `solidsdd-context`, `solidsdd-loop` (one slice), or `solidsdd-run` (multiple acceptance criteria)
3. Confirm skills read under `references/`
4. (Optional) End-to-end check with this repo’s [examples/arithmetic-api](../examples/arithmetic-api)

For automatic execution:

- **One property-level Gherkin Scenario** (or equivalent single checkable slice) already known → `solidsdd-loop`
- **Multiple / larger requirements** → `solidsdd-run` (brief → decompose to property-level Scenarios → loop per item → integration verify)

The parent must launch subagent-required skills (other than context) via Task (see each skill’s `references/execution-model.md`).

## Maintainers: distribution prep

After changing skill bodies:

```bash
gh skill publish --dry-run
# from https://github.com/naokirin/solid_sdd with auth:
# gh skill publish --tag v0.1.0
```

- Repo topic should include `agent-skills` (guided at publish time)
- Each `SKILL.md` already includes `license: MIT`
- `adapters/`, `schemas/`, `docs/`, `rules/`, and `reference-src/` are edit sources. **Distributed truth is `skills/*/references/`**
- After editing sources, always sync:

```bash
scripts/sync-skill-references.sh
scripts/sync-skill-references.sh --check   # detect drift
```

Edits via AI agents auto-sync:

- Cursor: `.cursor/hooks.json` (`afterFileEdit`)
- Claude Code: `.claude/settings.json` (`PostToolUse` / `Edit|Write|MultiEdit`)

On commit, `scripts/git-hooks/pre-commit` runs `--check` and fails with the command to run if out of sync. Once:

```bash
scripts/install-git-hooks.sh
```

## Updates

```bash
gh skill update --all
# or
gh skill update solidsdd-loop
```

If you customized `project-rule.mdc` locally, be careful when overwriting the copy.

## Adoption checklist

### Required (ChangeBrief + OpenAPI + OCL + Gherkin intake)

- [ ] `gh skill install naokirin/solid_sdd --all --agent cursor` succeeded (or `--from-local`)
- [ ] `gh skill list` shows `solidsdd-*` (run / loop / context / **brief** / decompose / judge / **critique** / apply-api / apply-dbc / derive-tests / implement / verify, plus formal skills)
- [ ] (Recommended) Copied `project-rule.mdc` into Project Rules
- [ ] Shared contract layout policy ([project-template.md](project-template.md)), including `.solidsdd/change-brief.json` and `requirements/**/*.feature`
- [ ] Smoke of `solidsdd-context`, `solidsdd-loop`, or `solidsdd-run` passes (`solidsdd-critique` launched via Task right after producers; Brief then WorkPlan with property-level Gherkin Scenarios)
- [ ] Contract tests run via the project’s `npm test` / `bundle exec rspec` / etc.

### Optional (by stack)

- [ ] GraphQL: `graphql/schema.graphql` and `adapter_hint: graphql`
- [ ] Ruby: `spec/contracts` + ruby-rspec generation target
- [ ] Formal: JDK 17+, `tla2tools` fetch steps, team agreement on **human_gate** ([phase3-gate-dryrun.md](phase3-gate-dryrun.md))

### Coexistence

- [ ] Read role split with NL SDD tools ([coexistence.md](coexistence.md))

## Related docs

- [adapters.md](adapters.md) — roles of OpenAPI / GraphQL / OCL / formal
- [execution-model.md](execution-model.md) — execution model (also bundled in skills)
- [architecture.md](architecture.md) — overall structure
- [phase4.md](phase4.md) — operations and ecosystem
- [../skills/README.md](../skills/README.md) — skill index
