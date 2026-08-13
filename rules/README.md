# Rules

| File | Purpose |
|------|---------|
| [solidsdd.mdc](solidsdd.mdc) | Edit source and Project Rule. Synced to `solidsdd-loop/references/project-rule.mdc` by `scripts/sync-skill-references.sh` |
| Distributed copy | `skills/solidsdd-loop/references/project-rule.mdc` |

## What's in the rule (and what isn't)

`solidsdd.mdc` is deliberately thin: it identifies the project as a solid_sdd project and routes to the right skill (`solidsdd-run` / `solidsdd-loop` / `solidsdd-grill` / `solidsdd-report`). Because it's `alwaysApply: true`, it loads on **every** turn regardless of relevance — so procedure that only matters once a skill is actually invoked belongs in that skill's `SKILL.md` / `references/` (loaded on demand), not here. Duplicating it here would also drift out of sync with the skill copies over time.

## Common customizations

| Setting | Where | Notes |
|---------|-------|-------|
| **Working language** | `.solidsdd/config.yaml` → `working_language: "ja"` (or `"en"`) — shared by every agent's rule, not written in the rule text | Prose under `.solidsdd/` and Gherkin step text; keys/headings/keywords stay English. Details: [../reference-src/working-language.md](../reference-src/working-language.md) |
| Contract paths | `.solidsdd/config.yaml` → `paths.*` | Override defaults when the repo layout differs; full defaults table: [../reference-src/contract-layout.md](../reference-src/contract-layout.md) |
| Judgment / density defaults | [../reference-src/judgment-axes.md](../reference-src/judgment-axes.md) (synced into `solidsdd-judge` / `solidsdd-critique`) | Tune thresholds from project feedback, then re-run `scripts/sync-skill-references.sh` |
| Human gates | [../reference-src/human-gates.md](../reference-src/human-gates.md) (synced into every phase skill) | Tune gate triggers from project feedback, then re-run `scripts/sync-skill-references.sh` |

Primary install path: [docs/install.md](../docs/install.md) (`scripts/install-into-project.sh`).
