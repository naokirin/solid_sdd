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
│ Outer = solidsdd.run (req → WorkPlan)    │
│   decompose + critique(work_plan)        │
│   → parallel solidsdd.loop waves         │
│   → integration verify                   │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│ Slice = solidsdd.loop / parent agent     │
│   context on parent; judge+ must Subagent│
│   critique after each producer           │
└──────────────────┬──────────────────────┘
                   │ Task (explicit Subagent)
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   judge / apply.*   derive.tests   implement / verify
        └──── critique (separate Task) ────┘
```

Execution policy: [execution-model.md](execution-model.md). Adversarial critique: [../reference-src/adversarial-critique.md](../reference-src/adversarial-critique.md).

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
   Like SpecKit clarify / analyze, `solidsdd.critique` is an independent command that adversarially evaluates (including weak contracts) in a separate Task.

## Core skills (MVP)

| Skill | Responsibility | Execution policy | Main I/O |
|-------|----------------|------------------|----------|
| `solidsdd.run` | Outer orchestration (decompose → **parallel** slice loops → integration verify) | orchestrator only | Loop log / final state |
| `solidsdd.loop` | Slice orchestration (one change intent) | orchestrator only | Loop log / final state |
| `solidsdd.context` | Discover stack and existing contracts | orchestrator | Context summary |
| `solidsdd.decompose` | Work decomposition | **subagent required** | WorkPlan |
| `solidsdd.judge` | Application judgment | **subagent required** | ApplicationPlan |
| `solidsdd.critique` | Adversarial evaluation of phase artifacts | **subagent required** | CritiqueReport |
| `solidsdd.apply.api` | Add/update OpenAPI | **subagent required** | OpenAPI diff |
| `solidsdd.apply.dbc` | Add/update OCL | **subagent required** | `.ocl` diff |
| `solidsdd.derive.tests` | OCL→contract tests | **subagent required** | Test diff |
| `solidsdd.implement` | Implement to contracts | **subagent required** | Code diff |
| `solidsdd.verify` | OpenAPI + contract-test verification | **subagent required** | VerificationReport |

Formal skills (e.g. `solidsdd.apply.formal` / `solidsdd.verify.formal`) are Phase 3. `solidsdd.judge` may explicitly defer when formal specs would help but are not yet supported.

## Work decomposition (`solidsdd.decompose`) output model

Shared schema: [../schemas/work-plan.schema.json](../schemas/work-plan.schema.json)

```text
WorkPlan:
  acceptance_of_whole? / human_gate? / confidence?
  items[]:
    id / intent / acceptance_criterion   … 1 item = 1 verifiable acceptance criterion
    depends_on[] / status
    confidence? / human_gate?
```

Distinct from `ApplicationPlan.targets` (where contracts land). Decomposition rules: [../reference-src/work-decomposition.md](../reference-src/work-decomposition.md).

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
| Manual | User names a skill. The conversation agent may run it. For chained skills, launch subagent-required skills via Task; recommend `critique` right after each producer |
| Automatic | `solidsdd.run` (outer) decomposes, runs **wave-parallel** slices for ready items, then integration verify. Each slice’s `solidsdd.loop` runs context (optional), judge, critique, apply, derive, implement, verify **always via Subagent**. Failures also re-run via Subagent (with retry limits). A single slice may use `solidsdd.loop` alone |

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

Skills follow the Cursor / Agent Skills (`SKILL.md`) format as **self-contained packages including `references/`**. The main install path for consumers is `gh skill install` ([install.md](install.md)).

## Open questions

- Default thresholds for “how much verification is required”
- OCL dialect / toolchain (how far to automate syntax checks). API side already uses `@redocly/cli --extends=spec` (PATH / `npx`; skip if unavailable)
- Opt-in design for language-native DbC (assuming gem refusal)
- Boundaries of coexistence / replacement with other SDD tools (Kiro, etc.)
