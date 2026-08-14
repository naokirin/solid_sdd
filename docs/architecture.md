# Architecture

## Overview

solid_sdd is designed to run in two layers:

1. **Rules (persistent constraints)**  
   Standing guidance for when, what, and at what quality to specify.
2. **Skills (callable phase procedures)**  
   Command-like units that a user or orchestrator can run in any order.

As with Kiro-like SDD tools, **manual step-by-step execution** and **AI automation** share the same skill set.

```text
┌─────────────────────────────────────────┐
│              Rules (standing constraints)│
│  policy / layout / verify-required, etc. │
└──────────────────┬──────────────────────┘
                   │ constraints & context
┌──────────────────▼──────────────────────┐
│ Outer = solidsdd.run (req → Context → Brief → WP) │
│   intake + critique(change_context)      │
│   [optional human gate before brief]     │
│   brief + critique(change_brief)         │
│   decompose + critique(work_plan)        │
│   [critique(cross_change) when needed]   │
│   architecture [+ critique when changed] │
│   → parallel solidsdd.loop waves         │
│     (serialize on WorkPlan touches∩)     │
│   → integration verify                   │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│ Slice = solidsdd.loop / parent agent     │
│   context on parent; slices via Subagent │
│   checkpoint/failure-driven critique     │
└──────────────────┬──────────────────────┘
                   │ Task (explicit Subagent)
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   Plan Slice   Implement Slice  Verify Slice
        └─(Failure/Checkpoint Critique)─┘
```

Execution policy: [execution-model.md](execution-model.md). Run cost / greenfield mitigations: [run-cost.md](run-cost.md). Adversarial critique: [../reference-src/adversarial-critique.md](../reference-src/adversarial-critique.md).

## Design principles

1. **Skills are self-contained and composable**  
   “Judgment only” or “API contract update only” must work. The auto loop is composition of those skills.
2. **Separate judgment from materialization**  
   Do not mix “what should be applied” with “how to write it as OpenAPI / language contracts.”
3. **Make verification a required loop node**  
   Generation is not the end. Detect contract–implementation drift and return to the loop.
4. **Absorb the stack in adapters**  
   The core owns contract kinds and verification-result models; concrete tech is plugin-like.
5. **Make human touchpoints explicit**  
   Default is automatic. Only approvals, exceptions, and policy changes are human gates (configurable in rules).
6. **Enforce separation of concerns with Subagents**  
   Do not run judgment, apply, derive-tests, implement, and verify in one continuous agent context (avoids bias, self-grading, and watered-down contracts).
7. **Producers do not grade their own phase artifacts**  
   When invoked by a checkpoint or failure, `solidsdd.critique` adversarially evaluates phase artifacts (including weak contracts) in a separate Task.

## Core skills (MVP)

| Skill | Responsibility | Execution policy | Main I/O |
|-------|----------------|------------------|----------|
| `solidsdd.run` | Outer orchestration (consult → [grill?] → intake → brief → decompose → **parallel** loops → verify → harvest) | orchestrator only | Loop log / final state |
| `solidsdd.loop` | Slice orchestration (one change intent) | orchestrator only | Loop log / final state |
| `solidsdd.context` | Discover stack and existing contracts | orchestrator | Context summary |
| `solidsdd.knowledge` | Consult / harvest durable `knowledge/` (CLI: `solidsdd-kg`) | **subagent required** (from run) | `knowledge-consult.md` / `knowledge-harvest.json` |
| `solidsdd.grill` | Conditional structured interview | **subagent required** | `clarifications/open.json` |
| `solidsdd.intake` | Change framing (demand / NFR / tech) + optional gate | **subagent required** | `change-context.md`, `change-context-gate.json` |
| `solidsdd.report` | Human-readable Change Report (Markdown / optional HTML) | manual (orchestrator OK) | `report.md` / `report.html` |
| `solidsdd.brief` | Change scope premise | **subagent required** | ChangeBrief |
| `solidsdd.decompose` | Work decomposition | **subagent required** | WorkPlan |
| `solidsdd.architecture` | Structural judgment (modules / dependencies / ownership / constraints) | **subagent required** | Architecture Model (`workspace.dsl`, `invariants.yaml`) + `architecture-reasoning.md` + generated `ArchitecturePlan` |
| `solidsdd.judge` | Application judgment | **subagent required** | ApplicationPlan |
| `solidsdd.critique` | Adversarial evaluation of phase artifacts | **subagent required** | CritiqueReport |
| `solidsdd.apply.api` | Add/update OpenAPI | **subagent required** | OpenAPI diff |
| `solidsdd.apply.dbc` | Add/update OCL | **subagent required** | `.ocl` diff |
| `solidsdd.derive.tests` | OCL→contract tests | **subagent required** | Test diff |
| `solidsdd.implement` | Implement to contracts | **subagent required** | Code diff |
| `solidsdd.verify` | OpenAPI + contract-test verification | **subagent required** | VerificationReport |

Formal skills (e.g. `solidsdd.apply.formal` / `solidsdd.verify.formal`) are Phase 3. `solidsdd.judge` may explicitly defer when formal specs would help but are not yet supported. Durable knowledge is not a living PRD—see [../reference-src/knowledge.md](../reference-src/knowledge.md).

## Change context (`solidsdd.intake`) output

Fixed-heading Markdown at `.solidsdd/changes/<change_id>/change-context.md` (demand, NFRs, technology selection, judgments) plus `change-context-gate.json` for an optional human pause before Brief when framing needs confirmation (not when the initial instruction already made decisions clear). Rules: [../reference-src/change-context.md](../reference-src/change-context.md).

## Working language

Prose under `.solidsdd/` (Context body, Brief/WorkPlan JSON string values, critique details, reports) follows `.solidsdd/config.yaml` → `working_language` (missing key means `en`) — one shared value every agent's rule reads, not a per-agent literal. JSON keys, Context top-level headings, and Gherkin keywords stay English. Policy: [../reference-src/working-language.md](../reference-src/working-language.md).

## Change report (`solidsdd.report`) output

Manual human-readable snapshot at `.solidsdd/changes/<change_id>/report.md` (optional `report.html`). Projects demand, functional/NFR, tech selection, and design from existing artifacts; missing phases are marked not performed. Not part of `solidsdd-run`. Rules: [../reference-src/change-report.md](../reference-src/change-report.md).

## Change brief (`solidsdd.brief`) output model

Shared schema: [../schemas/change-brief.schema.json](../schemas/change-brief.schema.json)

```text
ChangeBrief:
  change_id / summary / goal / background?
  in_scope[] / out_of_scope[]
  assumptions? / constraints? / success_criteria[]
  open_questions? / confidence? / human_gate?
```

Scope return point for the active change (path: `.solidsdd/changes/<change_id>/change-brief.json` via `active-change.json`). Rules: [../reference-src/change-brief.md](../reference-src/change-brief.md). Iterative / additional requirements: [../reference-src/change-lifecycle.md](../reference-src/change-lifecycle.md).

## Work decomposition (`solidsdd.decompose`) output model

Shared schema: [../schemas/work-plan.schema.json](../schemas/work-plan.schema.json)

```text
WorkPlan:
  change_id? / acceptance_of_whole? / human_gate? / confidence?
  items[]:
    id / intent / acceptance_criterion   … 1 item = 1 property-level Gherkin Scenario
    covers[]                             … Brief scope ids (required)
    touches[]?                           … primary edit paths (wave contention)
    feature_path? / scenario_name?
    depends_on[] / status
    confidence? / human_gate?
```

Requirements use property-level Gherkin ([../reference-src/gherkin-requirements.md](../reference-src/gherkin-requirements.md)), guided by ChangeBrief. Optional EARS wording in Brief texts: [../reference-src/ears-requirements.md](../reference-src/ears-requirements.md). Distinct from `ApplicationPlan.targets` (where contracts land). Decomposition rules: [../reference-src/work-decomposition.md](../reference-src/work-decomposition.md).

Deterministic coverage / NFR / gate checks: `scripts/solidsdd-lint.sh` (critique Step 0/1). Deterministic **next** / declared-step check: `scripts/solidsdd-next.sh` (does not write run-state). Hardening plan: [hardening-plan.md](hardening-plan.md). Intent-inspired stream: [intent-inspired-improvements.md](intent-inspired-improvements.md). Schema evolution: [schema-evolution.md](schema-evolution.md).

## Architecture judgment (`solidsdd.architecture`) output model

Judges **structure only** — modules, dependencies, dependency direction, public
boundaries, ownership, and structural constraints — not a design methodology (no
DDD / Clean / Hexagonal / … requirement) and not *which specification technique
applies where* (that is `solidsdd.judge` / `ApplicationPlan`, below). Most changes
do not affect existing structure and emit `status: unchanged` directly. When a
change does affect structure, the output is three layers, each with a distinct
job — do not duplicate the same structural fact across more than one of them:

```text
.solidsdd/architecture/workspace.dsl      structure: Source of Truth
  (Structurizr DSL subset, persistent,      (elements / relationships /
   whole-project — not per change)           hierarchy / tags / properties / views)

.solidsdd/architecture/invariants.yaml    rules ABOUT that structure
  (persistent, whole-project)               (forbid_dependency / no_cycles
                                             constraints, prose invariants)

.solidsdd/changes/<change_id>/            why (change-local)
  architecture-reasoning.md                 (Logical Decomposition, boundary/
                                             dependency rationale, trade-offs)

.solidsdd/changes/<change_id>/            generated projection, for
  architecture-plan.json                    existing consumers (see below)

.solidsdd/changes/<change_id>/            optional, Level 3 only: Logical →
  physical-design.md                        Physical realization (module /
                                             package / directory / process /
                                             service / database / adapter
                                             boundary), when non-obvious
```

`architecture-plan.json` (schema:
[../schemas/architecture-plan.schema.json](../schemas/architecture-plan.schema.json))
is unchanged in shape and is **generated**, never hand-authored — a
deterministic, change-scoped view of the model above:

```text
ArchitecturePlan:
  version / status: changed | unchanged
  change_id? / summary? / confidence? / human_gate?
  modules[]:            … only when status: changed
    id / responsibility
    owns? / public?
  dependencies[]:
    from / to
    reason? / kind?: runtime | data | event | api
  constraints[]:
    type: forbid_dependency | no_cycles
    from? / to? / reason?
```

`scripts/solidsdd-architecture/project.py` builds it from elements/relationships
tagged `change:<change_id>` in `workspace.dsl`, plus relevant entries from
`invariants.yaml`. This keeps `solidsdd-lint`, `solidsdd-critique`, and
`solidsdd-report` working against the same artifact shape they always have,
while the DSL — not this generated JSON — is the durable Source of Truth for
structure across changes. `ArchitecturePlan` stays change-level, sibling of
`work-plan.json`, not per-item like `ApplicationPlan`.

Mechanical verification — DSL syntax, referenced-element existence, forbidden
dependencies, declared-cycle detection, ownership conflicts, internal-boundary
leakage — runs via `scripts/solidsdd-architecture/validate.py`, folded into
`scripts/solidsdd-lint.sh`'s findings, which every `solidsdd-critique` call
already runs first regardless of subject — no separate verification step is
needed. No Java/JVM toolchain is required; Structurizr CLI remains an optional,
not-yet-adopted toolchain for future rendering/validation.

Depth: [../reference-src/architecture-depth.md](../reference-src/architecture-depth.md)
(most changes stay at Level 0 and never touch the model).
Axes: [../reference-src/architecture-axes.md](../reference-src/architecture-axes.md).
DSL grammar: [../reference-src/structurizr-dsl.md](../reference-src/structurizr-dsl.md).
Reasoning template: [../reference-src/architecture-reasoning-template.md](../reference-src/architecture-reasoning-template.md).
Physical Design (Level 3 only): [../reference-src/physical-design.md](../reference-src/physical-design.md).
Human gates: [../reference-src/human-gates.md](../reference-src/human-gates.md).

### Role separation

| Artifact | Answers |
|----------|---------|
| Gherkin | What behavior is required? |
| `ArchitecturePlan` | How is the system structurally organized (modules / dependencies / ownership / constraints)? |
| `ApplicationPlan` | Which specification mechanism (API / DbC / formal) applies where? |
| OpenAPI / GraphQL | What is the external API contract? |
| OCL / DbC | What local invariants/contracts must hold? |
| TLA+ / Alloy | What state/temporal properties must hold? |

## Application judgment (`solidsdd.judge`) output model

Shared schema: [../schemas/application-plan.schema.json](../schemas/application-plan.schema.json)

```text
ApplicationPlan:
  human_gate? / confidence?          … Phase 2 (optional)
  targets[]:
    kind: api | dbc | formal | natural_only
    location: boundary or module id
    density: thin | standard | strict
    rationale: reason (references axes)
    adapter_hint: openapi | graphql | ocl | ...
    status: apply | defer | skip
    signals? / breaking? / confidence? / human_gate?  … Phase 2
```

`formal` is mainly `defer` (with reason) or conditional Phase 3 `apply`.

Axes: [../reference-src/judgment-axes.md](../reference-src/judgment-axes.md) and [vision.md](vision.md). Rules may override project-specific thresholds. Human gates and loop recovery: [phase2.md](phase2.md).

## Adapter layer

MVP adapters are fixed as follows (see [adapters.md](adapters.md)). Phase 2 adds a GraphQL skeleton.

```text
Contract Kind          Adapter
─────────────          ─────────────────────────────
API boundary    →      OpenAPI 3.x (default) / GraphQL SDL
Module DbC      →      UML OCL → contract tests (Vitest default / RSpec ok)
Formal          →      TLA+ / Alloy etc. (Phase 3 design; judge may apply conditionally; early rollout requires gates)
```

OCL path: OCL is the source of truth. Test code is a dependent artifact generated by a subagent from OCL; `solidsdd.verify` checks compliance by running those tests. Language-native contracts are optional and deferred. Formal role split: [phase3.md](phase3.md).

Adapter responsibilities:

- Artifact layout conventions (paths, naming)
- Generate/update templates
- How to invoke verification (OpenAPI checks, OCL-derived test runs, etc.)
- Fallback when the stack is undetected (propose only / human gate)

## What the rules layer holds (examples)

- Default application density (thin for exploratory areas; strict for money / authz boundaries, etc.)
- Whether merge/done without verification is forbidden
- Handling of API breaking changes (warn / block / require approval)
- Orchestrator max loop count and escalation on failure
- Human-gate conditions (first adoption, breaking changes, low judgment confidence, etc.)

## Manual vs automatic execution

| Mode | Behavior |
|------|----------|
| Manual | User names a skill. The conversation agent may run it. For chained skills, launch subagent-required skills via Task |
| Automatic | `solidsdd.run` (outer) runs intake → brief → decompose, then **wave-parallel** slices for ready items, then integration verify. Each slice’s `solidsdd.loop` runs Plan Slice, Plan Review, Implement Slice, Verify Slice **always via Subagent**. Failures trigger Review/Fix via Subagent (with retry limits). A single slice may use `solidsdd.loop` alone |

Both modes use the **same rules, skills, and artifact layout**. Automation has no private back door.

## Repository layout

```text
solid_sdd/
  README.md
  docs/                 # vision & design
  schemas/              # shared schemas (ApplicationPlan / WorkPlan, etc.)
  adapters/             # OpenAPI / GraphQL / OCL / ruby-rspec / formal conventions
  skills/               # Cursor Skill definitions
  rules/                # standing rules (grow over time)
  examples/             # evaluation samples
```

Skills follow the Cursor / Agent Skills (`SKILL.md`) format as **self-contained packages including `references/`**. Consumers install via [`scripts/install-into-project.sh`](../scripts/install-into-project.sh) (skills **and** mechanical scripts/schemas; see [install.md](install.md)).

## Open questions

- Default thresholds for “how much verification is required”
- OCL dialect / toolchain (how far to automate syntax checks). API side already uses `@redocly/cli --extends=spec` (PATH / `npx`; skip if unavailable)
- Opt-in design for language-native DbC (assuming gem refusal)
- Boundaries of coexistence / replacement with other SDD tools (Kiro, etc.)
