# Project template layout

Minimal layout a consuming repo can copy. Paths match skill defaults ([contract-layout](../reference-src/contract-layout.md), [change-lifecycle](../reference-src/change-lifecycle.md)).

```text
your-project/
  .solidsdd/
    active-change.json           # { "version": "1", "change_id": "<id>" }
    changes/
      <change_id>/
        change-context.md        # demand / NFR / tech (solidsdd-intake)
        change-context-gate.json # optional human pause before brief
        change-brief.json        # scope for this change (solidsdd-brief)
        work-plan.json           # after solidsdd-decompose
        status.json              # active | done | abandoned
  requirements/
    *.feature                    # property-level Gherkin (not Cucumber SoT); accumulates
  openapi/
    openapi.yaml                 # if HTTP/OpenAPI
  graphql/
    schema.graphql               # if GraphQL (optional alternative)
  contracts/
    *.ocl                        # DbC loop authority
  tests/
    contracts/
      *.test.ts                  # derived (Vitest) — or:
  spec/
    contracts/
      *_spec.rb                  # derived (RSpec) if Ruby target
  formal/                        # optional Phase 3
    *.tla
    *.cfg
  .agents/skills/solidsdd-*/     # gh skill install
  .cursor/rules/solidsdd.mdc     # copy from solidsdd-loop/references/project-rule.mdc
```

`change_id` is a meaningful kebab-case name (e.g. `initial-calculator`, `add-operation-history`). Additional requirements start a **new** change directory—do not enlarge an old Brief into a living PRD.

## Bootstrap steps

1. Install skills — [install.md](install.md)
2. Copy project rule into `.cursor/rules/solidsdd.mdc` (from `skills/solidsdd-loop/references/project-rule.mdc` or repo `rules/solidsdd.mdc`)
3. Set **Working language** in that rule — one line under `## Working language`:
   - English (default): `Working language: en`
   - Japanese prose under `.solidsdd/`: `Working language: ja`
   - Keep JSON keys, Change Context headings, and Gherkin keywords in English (see skill `references/working-language.md`)
4. Add empty dirs you need (or let apply skills create files)
5. Smoke: `solidsdd-context` then a small `solidsdd-judge` on a known change
6. Optional formal: fetch TLC (`tools` from solid_sdd or document JDK + `tla2tools.jar` in your repo)

## What not to commit

- Generated noise (`node_modules`, TLC `states/`)
- `tla2tools.jar` (fetch locally; see solid_sdd `tools/tla/`)
- Secrets

## Checklist link

Use the expanded list in [install.md](install.md) §Adoption checklist.