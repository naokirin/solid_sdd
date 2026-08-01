# GraphQL SDL adapter (Phase 2 skeleton)

編集用ソース。同期先: 今後 `solidsdd-apply-api` が `adapter_hint: graphql` のとき参照（現状 OpenAPI が既定）。ソース変更後:

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

- SDL parse / schema validity
- Optional contract tests against resolvers (project-specific)
- On failure, prefer `solidsdd-apply-api` (schema) or `solidsdd-implement` (resolvers)

## Skill mapping

- Write/update: `solidsdd-apply-api` with `adapter_hint: graphql`
- Check: `solidsdd-verify` (check kind may be `graphql`)

## Status

Skeleton for Phase 2. MVP evaluation sample remains OpenAPI + OCL. Full GraphQL eval sample is future work.
