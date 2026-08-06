# OpenAPI adapter

## Role

HTTP API boundaries as OpenAPI 3.x documents.

## Artifact layout (default)

| Artifact | Path |
|----------|------|
| OpenAPI document | `openapi/openapi.yaml` |
| Optional overlays / examples | `openapi/examples/` |

Override via `.solidsdd/config.yaml` → `paths.openapi` (see contract-layout / `schemas/project-config.schema.json`).

## Responsibilities

- Add or update paths, operations, schemas, and error responses
- Keep `operationId` stable when behavior is unchanged
- Flag breaking changes (removed fields, stricter types, status code changes)

## Verification hooks

- **Structural lint (when tooling available):** `@redocly/cli` with `--extends=spec`

  ```bash
  redocly lint openapi/openapi.yaml --extends=spec
  # fallback: npx --yes @redocly/cli@latest lint openapi/openapi.yaml --extends=spec
  ```

  Prefer `redocly` on `PATH`; else `npx`. If neither works, `solidsdd-verify` records `kind: openapi` as `skipped` (missing tool is not a report-level fail).
- Contract tests or response validation against the document
- On Redocly / contract-doc failure, prefer `solidsdd.apply.api`; on impl mismatch, `solidsdd.implement`

## Skill mapping

- Write/update: `solidsdd-apply-api`
- Consume in implementation: `solidsdd-implement`
- Check: `solidsdd-verify`
