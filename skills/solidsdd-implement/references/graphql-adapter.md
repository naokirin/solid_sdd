# GraphQL SDL adapter (Phase 2)

編集用ソース。同期先: `solidsdd-apply-api` が `adapter_hint: graphql` のとき参照。ソース変更後:

```bash
scripts/sync-skill-references.sh
```

## Role

HTTP/API boundary contracts expressed as GraphQL Schema Definition Language (SDL), as an alternative to OpenAPI when the project is GraphQL-first.

## Artifact layout (default)

| Artifact | Path |
|----------|------|
| Schema SDL | `graphql/schema.graphql` |
| Optional operations documents | `graphql/operations/**/*.graphql` |

## Responsibilities

- Add/update types, fields, arguments, and error/extension conventions used by the team
- Prefer additive, non-breaking field evolution; flag removals / type tightenings as breaking
- Keep field and type names stable when behavior is unchanged

## Verification hooks

- SDL parse / schema validity (`buildSchema` / equivalent)
- Optional contract tests against resolvers (project-specific)
- On failure, prefer `solidsdd-apply-api` (schema) or `solidsdd-implement` (resolvers)

## Skill mapping

- Write/update: `solidsdd-apply-api` with `adapter_hint: graphql`
- Check: `solidsdd-verify` (check kind may be `graphql`)

## Evaluation sample

[../../examples/arithmetic-graphql](../../examples/arithmetic-graphql) — calculate + memory over GraphQL, with OCL → Vitest.
