# architecture-dependency-inversion (evaluation sample)

Minimal Structurizr DSL Architecture Model illustrating **dependency
inversion** as a structural design decision — not a runnable project
(no `src/`), same spirit as [`examples/memory-formal`](../memory-formal/).

```text
Before:  Inventory -> PostgresInventoryStore
After:   Inventory -> InventoryRepositoryPort <- PostgresInventoryStore
```

## Changes

| Change | What it shows |
|--------|----------------|
| [`establish-inventory-persistence`](.solidsdd/changes/establish-inventory-persistence/) | Baseline: Inventory (domain) depends directly on a concrete PostgresInventoryStore (infrastructure) |
| [`invert-inventory-persistence-dependency`](.solidsdd/changes/invert-inventory-persistence-dependency/) | Introduces `inventory_repository_port`; the direct edge is removed and replaced by `inventory -> port` and `postgres_store -> port`; a `forbid_dependency: postgres_store -> inventory` constraint prevents the direct coupling from being reintroduced |

`.solidsdd/architecture/workspace.dsl` accumulates both changes (each
element/relationship is tagged `change:<change_id>`); `git diff` between
the two changes' states shows the actual before/after transformation, not
just prose. Each change's `architecture-plan.json` is a **generated
projection** (`scripts/solidsdd-architecture/project.py`), not
hand-authored. See [docs/architecture.md](../../docs/architecture.md) and
[reference-src/structurizr-dsl.md](../../reference-src/structurizr-dsl.md).

## Why this is a separate sample

`examples/inventory-reservation` already has a real, growing Architecture
Model (see its README's "Architecture design" section for the Boundary
Split and New Module examples). Dependency inversion needs a clean
synthetic "before" state to invert, so it's kept here as its own minimal
sample rather than retrofitted onto inventory-reservation's history.

## Verify

```bash
# from repo root
scripts/solidsdd-architecture.sh validate --project-root examples/architecture-dependency-inversion
scripts/solidsdd-lint.sh --project-root examples/architecture-dependency-inversion --change-id establish-inventory-persistence
scripts/solidsdd-lint.sh --project-root examples/architecture-dependency-inversion --change-id invert-inventory-persistence-dependency
```
