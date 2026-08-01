# Contract artifact layout (defaults)

| Kind | Path | Notes |
|------|------|-------|
| OpenAPI | `openapi/openapi.yaml` | HTTP boundary contract |
| OCL | `contracts/**/*.ocl` | DbC source of truth |
| Contract tests | `tests/contracts/**/*.test.ts` | Derived from OCL (Vitest / TypeScript MVP) |

Projects may override paths via a project rule (see `project-rule.mdc` in `solidsdd-loop` references).

OCL-derived tests are dependents: regenerate from OCL rather than treating tests as the primary spec.
