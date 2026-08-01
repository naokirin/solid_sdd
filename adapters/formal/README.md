# Formal specification adapter (Phase 3 design)

編集用ソース。同期は formal スキル追加後に `scripts/sync-skill-references.sh` へ配線する。

## Role

Express **safety / liveness / concurrency** properties that API contracts and OCL→tests do not cheaply cover. Formal specs are **optional** and narrow-scope. Prefer OpenAPI/GraphQL + OCL unless [docs/phase3.md](../../docs/phase3.md) apply conditions hold.

## Artifact layout (default)

| Artifact | Path |
|----------|------|
| TLA+ modules | `formal/**/*.tla` |
| TLA+ configs | `formal/**/*.cfg` (optional) |
| Alloy models | `formal/**/*.als` (optional alternative) |

## Responsibilities

- Keep models small (one protocol / shared resource)
- Name invariants and temporal properties explicitly
- Do not duplicate OpenAPI field lists or OCL arithmetic posts in the formal model
- Flag tooling gaps; never pretend a model was checked if the checker did not run

## Verification hooks

- Parse / type-check the model
- Run the project-chosen checker (TBD per repo: TLC, Apalache, Alloy, …)
- On failure: `solidsdd-apply-formal` (spec) or clarify SoT vs implementation with the parent

## Skill mapping

- Write/update: `solidsdd-apply-formal`
- Check: `solidsdd-verify-formal`
- Judge: `kind=formal`, `adapter_hint` e.g. `tla` / `alloy` / `defer-formal`

## Status

Design-only. No evaluation sample yet. Language-native DbC remains a separate deferred track.
