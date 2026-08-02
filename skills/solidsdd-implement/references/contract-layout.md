# Contract artifact layout (defaults)

| Kind | Path | Notes |
|------|------|-------|
| Active change pointer | `.solidsdd/active-change.json` | `{ "version": "1", "change_id": "<id>" }` |
| ChangeBrief | `.solidsdd/changes/<change_id>/change-brief.json` | Scope premise for the active change (return point) |
| WorkPlan | `.solidsdd/changes/<change_id>/work-plan.json` | Slice plan for this change (`solidsdd-decompose`) |
| Change status | `.solidsdd/changes/<change_id>/status.json` | `active` \| `done` \| `abandoned` |
| Requirements (Gherkin) | `requirements/**/*.feature` | Property-level acceptance; not executable test SoT; accumulates across changes |
| OpenAPI | `openapi/openapi.yaml` | HTTP boundary contract (default API adapter) |
| GraphQL SDL | `graphql/schema.graphql` | Optional API adapter (`adapter_hint: graphql`) |
| OCL | `contracts/**/*.ocl` | DbC source of truth for the active change loop |
| Contract tests (TS) | `tests/contracts/**/*.test.ts` | Derived from OCL (Vitest / TypeScript MVP) |
| Contract specs (Ruby) | `spec/contracts/**/*_spec.rb` | Derived from OCL (RSpec target) |
| Formal specs (Phase 3) | `formal/**` | Optional; TLA+ / Alloy — see `solidsdd-apply-formal` when installed |

Resolve the active Brief via `active-change.json` → `changes/<change_id>/`. See [change-lifecycle.md](change-lifecycle.md).

**Legacy:** flat `.solidsdd/change-brief.json` only — migrate on next brief/run (do not keep a dual SoT).

Projects may override paths via a project rule (commonly installed from the `solidsdd-loop` skill as `project-rule.mdc`).

OCL-derived tests are dependents: regenerate from OCL rather than treating tests as the primary spec.

ChangeBrief is scope authority for the change; Gherkin structures acceptance. Neither replaces OCL or API contracts. See [change-brief.md](change-brief.md) and [gherkin-requirements.md](gherkin-requirements.md).
