# Rules

| File | Purpose |
|------|---------|
| [solidsdd.mdc](solidsdd.mdc) | Edit source and Project Rule. Synced to `solidsdd-loop/references/project-rule.mdc` by `scripts/sync-skill-references.sh` |
| Distributed copy | `skills/solidsdd-loop/references/project-rule.mdc` |

## Common customizations

| Setting | Where | Notes |
|---------|-------|-------|
| **Working language** | `## Working language` → `Working language: ja` (or `en`) | Prose under `.solidsdd/` and Gherkin step text; keys/headings/keywords stay English. Details: [../reference-src/working-language.md](../reference-src/working-language.md) |
| Contract paths | `## Contract artifacts` | Override defaults when the repo layout differs |
| Judgment / gates | `## Judgment defaults`, `## Human gates` | Tune thresholds from project feedback |

Primary install path: [docs/install.md](../docs/install.md) (`scripts/install-into-project.sh`).
