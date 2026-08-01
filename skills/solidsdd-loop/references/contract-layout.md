# Contract artifact layout (defaults)

| Kind | Path | Notes |
|------|------|-------|
| OpenAPI | `openapi/openapi.yaml` | HTTP boundary contract (default API adapter) |
| GraphQL SDL | `graphql/schema.graphql` | Optional API adapter (`adapter_hint: graphql`) |
| OCL | `contracts/**/*.ocl` | DbC source of truth |
| Contract tests (TS) | `tests/contracts/**/*.test.ts` | Derived from OCL (Vitest / TypeScript MVP) |
| Contract specs (Ruby) | `spec/contracts/**/*_spec.rb` | Derived from OCL (RSpec target) |
| Formal specs (Phase 3) | `formal/**` | Optional; TLA+ / Alloy — see formal adapter |

Projects may override paths via a project rule (see `project-rule.mdc` in `solidsdd-loop` references).

OCL-derived tests are dependents: regenerate from OCL rather than treating tests as the primary spec.
