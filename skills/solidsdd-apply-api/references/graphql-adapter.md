# GraphQL SDL adapter

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

- **Structural lint (when tooling available):** `@redocly/cli` with `--extends=spec` (includes SDL parse / schema validity via Redocly’s GraphQL `struct` path)

  ```bash
  redocly lint graphql/schema.graphql --extends=spec
  # fallback: npx --yes @redocly/cli@latest lint graphql/schema.graphql --extends=spec
  ```

  Prefer `redocly` on `PATH`; else `npx`. If neither works, `solidsdd-verify` records `kind: graphql` as `skipped` (missing tool is not a report-level fail).
- Optional contract tests against resolvers (project-specific)
- On Redocly / schema failure, prefer `solidsdd-apply-api`; on resolver mismatch, `solidsdd-implement`

## Skill mapping

- Write/update: `solidsdd-apply-api` with `adapter_hint: graphql`
- Check: `solidsdd-verify` (check kind may be `graphql`)

## Evaluation sample shape

A typical sample exposes calculate + memory over GraphQL SDL, with OCL → Vitest contract tests. Consuming projects need not ship a particular example path.
