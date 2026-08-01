# OpenAPI adapter

## Role

HTTP API boundaries as OpenAPI 3.x documents.

## Artifact layout (default)

| Artifact | Path |
|----------|------|
| OpenAPI document | `openapi/openapi.yaml` |
| Optional overlays / examples | `openapi/examples/` |

Projects may override paths via rules.

## Responsibilities

- Add or update paths, operations, schemas, and error responses
- Keep `operationId` stable when behavior is unchanged
- Flag breaking changes (removed fields, stricter types, status code changes)

## Verification hooks

- Document structural validity (OpenAPI 3.x)
- Contract tests or response validation against the document
- On failure, prefer returning to `sdd.apply.api` or `sdd.implement`

## Skill mapping

- Write/update: `sdd-apply-api`
- Consume in implementation: `sdd-implement`
- Check: `sdd-verify`
