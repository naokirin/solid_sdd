# Project template layout

Minimal layout a consuming repo can copy. Paths match skill defaults ([contract-layout](../reference-src/contract-layout.md)).

```text
your-project/
  openapi/
    openapi.yaml                 # if HTTP/OpenAPI
  graphql/
    schema.graphql               # if GraphQL (optional alternative)
  contracts/
    *.ocl                        # DbC SoT
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

## Bootstrap steps

1. Install skills — [install.md](install.md)
2. Copy project rule
3. Add empty dirs you need (or let apply skills create files)
4. Smoke: `solidsdd-context` then a small `solidsdd-judge` on a known change
5. Optional formal: fetch TLC (`tools` from solid_sdd or document JDK + `tla2tools.jar` in your repo)

## What not to commit

- Generated noise (`node_modules`, TLC `states/`)
- `tla2tools.jar` (fetch locally; see solid_sdd `tools/tla/`)
- Secrets

## Checklist link

Use the expanded list in [install.md](install.md) §Adoption checklist.
