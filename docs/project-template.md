# Project template layout

Minimal layout a consuming repo can copy. Paths match skill defaults ([contract-layout](../reference-src/contract-layout.md), [change-lifecycle](../reference-src/change-lifecycle.md)).

```text
your-project/
  .solidsdd/
    config.yaml                  # path layout SoT (optional; defaults if missing)
    tooling.json                 # written by install-into-project.sh
    vendor/solid_sdd/            # scripts + schemas + skill copies (installer)
    active-change.json           # { "version": "1", "change_id": "<id>" }
    changes/
      <change_id>/
        change-context.md        # demand / NFR / tech (solidsdd-intake)
        change-context-gate.json # optional human pause before brief
        change-brief.json        # scope for this change (solidsdd-brief)
        work-plan.json           # after solidsdd-decompose
        knowledge-consult.md     # solidsdd-knowledge consult (optional until kg adopted)
        knowledge-harvest.json   # solidsdd-knowledge harvest before done
        status.json              # active | done | abandoned
    kg/                          # solidsdd-kg schema/config/links (when knowledge adopted)
  knowledge/                     # durable cross-cutting nodes (not living Brief)
    concepts/ | policies/ | decisions/ | lessons/ | patterns/
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
  .agents/skills/solidsdd-*/     # install-into-project.sh (--agent cursor|copilot|codex)
  .cursor/rules/solidsdd.mdc     # installer copies for Cursor
```

`change_id` is a meaningful kebab-case name (e.g. `initial-calculator`, `add-operation-history`). Additional requirements start a **new** change directory—do not enlarge an old Brief into a living PRD.

Override any of the default directories/files with `.solidsdd/config.yaml` (`paths.*`; see [contract-layout](../reference-src/contract-layout.md) and `schemas/project-config.schema.json`). Relocate the meta root with env `SOLIDSDD_DIR`. Install mechanical CLIs with [install.md](install.md) (`--vendor-dir` if not using the default vendor path).

`knowledge/` holds rarely changing cross-cutting policies/concepts/decisions. `solidsdd-run` **consults** it before framing and **harvests** candidates after integration verify (human-gated). It is not a second requirement SoT—see [knowledge.md](../reference-src/knowledge.md) and [tools/solidsdd-kg](../tools/solidsdd-kg).

## Bootstrap steps

1. Install skills **and** tooling — [install.md](install.md) (`scripts/install-into-project.sh --language <tag>`)
2. Confirm `.solidsdd/tooling.json` and agent skill dirs
3. Confirm **Working language** in `.solidsdd/config.yaml` → `working_language` (set by `--language` during install, or edit the key directly; every agent's rule reads this one shared value):
   - English (default / missing key): `working_language: "en"`
   - Japanese prose under `.solidsdd/`: `working_language: "ja"`
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