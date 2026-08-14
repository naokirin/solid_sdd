# solidsdd-architecture (Architecture Model tooling)

Deterministic parser/validator/projector for the Architecture Model
(`.solidsdd/architecture/workspace.dsl`, a Structurizr DSL subset, +
`.solidsdd/architecture/invariants.yaml`). No Java/JVM required — this is a
lightweight parser for the subset solid_sdd needs, not a Structurizr CLI
wrapper. See [structurizr-dsl.md](../../reference-src/structurizr-dsl.md).

## Usage

From a consuming project root (directory that contains `.solidsdd/`):

```bash
scripts/solidsdd-architecture.sh validate [--project-root .] [--pretty]
scripts/solidsdd-architecture.sh project --change-id ID [--project-root .] [--out PATH] [--pretty]
```

Requires Python 3 + [`PyYAML`](https://pypi.org/project/PyYAML/) +
[`jsonschema`](https://pypi.org/project/jsonschema/) (same as
`solidsdd-lint`).

## Modules

| File | Role |
|------|------|
| `dsl.py` | Recursive-descent parser for the DSL subset → `Element`/`Relationship`/`View` |
| `validate.py` | Syntax, model consistency, referenced-element existence, relationship/view validity, plus `invariants.yaml`-driven forbidden-dependency / no-cycles / ownership-conflict / boundary-leakage checks |
| `project.py` | Derives `architecture-plan.json` (unchanged schema) from the model, filtered by `change:<change_id>` tags — a generated projection, never hand-authored |
| `cli.py` | `validate` / `project` subcommands, dispatched by `scripts/solidsdd-architecture.sh` |

## Output

`validate`: same finding shape as `solidsdd-lint` —
`{"severity", "category", "location", "detail"}` — and is folded directly
into `scripts/solidsdd-lint/lint.py`'s findings when
`.solidsdd/architecture/workspace.dsl` exists (no-op otherwise).

`project`: `ArchitecturePlan` JSON conforming to
`schemas/architecture-plan.schema.json`.

## Limitations (v1)

Additive-only projection (no deletion/rename tracking — note those in
`architecture-reasoning.md`); prose `invariants[]` are not mechanically
checked, only `constraints[]`.
