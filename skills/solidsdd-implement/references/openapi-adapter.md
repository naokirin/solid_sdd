# OpenAPI adapter

編集用ソース。`gh skill` 配布時は `skills/solidsdd-apply-api/references/openapi-adapter.md`（および implement/verify 同梱）が利用側に入ります。ここを直したら該当 `references/` を更新してください。

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
- On failure, prefer returning to `solidsdd.apply.api` or `solidsdd.implement`

## Skill mapping

- Write/update: `solidsdd-apply-api`
- Consume in implementation: `solidsdd-implement`
- Check: `solidsdd-verify`
