# Roadmap

## Evaluation premise

Without the end-state chain (judgment → apply → implement → verify), it is hard to evaluate whether the intended design works. For MVP we therefore **wire the main path once, excluding formal specs**.

Formal specs are valuable but heavy to adopt and tend to narrow scope, so they are **intentionally deferred**. The judgment model still keeps `formal` (no missing kind) and can emit `defer` with a reason.

## Phase 0: Vision and design

- [x] Capture problem and goals ([vision.md](vision.md))
- [x] Rules / skill architecture ([architecture.md](architecture.md))
- [x] Split MVP vs later work (this document)
- [x] Initial adapters: OpenAPI + OCL→contract tests ([adapters.md](adapters.md))
- [x] Evaluation scenario: TypeScript arithmetic API ([../examples/arithmetic-api](../examples/arithmetic-api))
- [x] Skill I/O schemas (`ApplicationPlan`, etc.)
- [x] Skill definition skeletons (`skills/`)
- [x] Consumer install guide ([install.md](install.md) — `install-into-project.sh`; skills + mechanical tooling)
- [x] `skills/*/references/` sync script (`scripts/sync-skill-references.sh`)
- [x] Cursor / Claude Code hooks + git pre-commit (error + fix command on drift)
- [x] Drop skill-only CLI as consumer channel; installer is the sole install path

## Phase 1: MVP (minimal connected system)

**Status: evaluation complete** (see [mvp-evaluation.md](mvp-evaluation.md)). Consumer distribution is via `install-into-project.sh`.

**In scope**

| Element | Contents |
|---------|----------|
| Rules | Minimal set: apply policy, artifact layout, verify-required |
| `solidsdd.context` | Discover stack and existing contracts |
| `solidsdd.judge` | API / DbC / skip (formal may defer) |
| `solidsdd.apply.api` | OpenAPI 3.x |
| `solidsdd.apply.dbc` | UML OCL |
| `solidsdd.derive.tests` | OCL→contract tests (subagent) |
| `solidsdd.implement` | Implementation updates aligned to contracts |
| `solidsdd.verify` | Redocly API lint (when available) + contract tests |
| `solidsdd.loop` | Automatic orchestration of the above |

**Out of scope (intentional)**

- Applying / model-checking formal specs (TLA+ / Alloy / VDM, etc.)
- Exhaustive adapters for many stacks
- Advanced confidence estimation or large policy engines

**MVP success criteria**

1. [x] For a sample change, running skills manually leaves contracts in place; verify passes / intentional breakage is detected
2. [x] The same change via `solidsdd.loop` alone approaches equivalent results
3. [x] `solidsdd.judge` can explain “why API / DbC / skip” along the axes
4. [x] When formal specs would help, `defer` + reason appear (not silently ignored)

## Phase 2: Stronger judgment and adapters

**Status: complete** (see [phase2.md](phase2.md)). Language-native contracts intentionally deferred.

- [x] Sharper judgment axes (breaking changes, authz/money boundaries, churn, confidence, etc.) — [../reference-src/judgment-axes.md](../reference-src/judgment-axes.md)
- [x] GraphQL adapter + evaluation sample — [../adapters/graphql/README.md](../adapters/graphql/README.md), [../examples/arithmetic-graphql](../examples/arithmetic-graphql)
- [x] Alternate-language contract-test target (Ruby / RSpec) — [../adapters/ruby-rspec/README.md](../adapters/ruby-rspec/README.md), [../examples/arithmetic-ruby](../examples/arithmetic-ruby)
- [x] Human-gate conditions (low confidence, breaking changes, etc.) — [../reference-src/human-gates.md](../reference-src/human-gates.md)
- [x] Standardized verification reports and loop-recovery rules — schema + [../reference-src/loop-retry.md](../reference-src/loop-retry.md)
- [x] End-to-end evaluation of GraphQL / Ruby samples — [phase2-evaluation.md](phase2-evaluation.md)
- [ ] Language-native DbC (optional gems, etc.) — **deferred** (opt-in design needed given project gem refusal)

## Phase 3: Formal specifications

**Status: complete** ([phase3.md](phase3.md), [phase3-evaluation.md](phase3-evaluation.md), [phase3-gate-dryrun.md](phase3-gate-dryrun.md)).

- [x] `solidsdd.apply.formal` / `solidsdd.verify.formal` skill skeletons
- [x] Conditions under which `solidsdd.judge` may `apply` `formal` — [../reference-src/judgment-axes.md](../reference-src/judgment-axes.md) + [phase3.md](phase3.md)
- [x] Narrow-scope adoption guide (role split) — [phase3.md](phase3.md)
- [x] Reconfirm role split vs existing API / DbC paths
- [x] Concrete checker integration (**TLC**) + minimal evaluation sample — [../tools/tla](../tools/tla), [../examples/memory-formal](../examples/memory-formal)
- [x] Phase 3 end-to-end evaluation notes (sample TLC) — [phase3-evaluation.md](phase3-evaluation.md)
- [x] Loop dry run: human_gate → apply-formal — [phase3-gate-dryrun.md](phase3-gate-dryrun.md)

## Phase 4: Operations and ecosystem

**Status: documentation slice started** ([phase4.md](phase4.md)). Public release and real-project feedback still open.

- [x] Coexistence patterns with other SDD tools — [coexistence.md](coexistence.md)
- [x] Expanded adoption checklist — [install.md](install.md)
- [x] Project template layout — [project-template.md](project-template.md)
- [x] Rule tuning from eval corpus (Pass 1) — [feedback-tuning.md](feedback-tuning.md)
- [x] Adversarial critique skill (`solidsdd-critique`) wired into the loop — [../reference-src/adversarial-critique.md](../reference-src/adversarial-critique.md)
- [x] Outer run + work decomposition — `solidsdd-run` / `solidsdd-decompose` + [../reference-src/work-decomposition.md](../reference-src/work-decomposition.md) / [../schemas/work-plan.schema.json](../schemas/work-plan.schema.json)
- [x] Gherkin as requirement intake (property-level; not Cucumber SoT) — [../reference-src/gherkin-requirements.md](../reference-src/gherkin-requirements.md)
- [x] ChangeBrief scope phase (`solidsdd-brief`) — [../reference-src/change-brief.md](../reference-src/change-brief.md) / [../schemas/change-brief.schema.json](../schemas/change-brief.schema.json)
- [x] Change Context framing (`solidsdd-intake`) — [../reference-src/change-context.md](../reference-src/change-context.md)
- [x] Optional human gate after Change Context (tech/NFR confirmation when unclear) — [../reference-src/human-gates.md](../reference-src/human-gates.md)
- [x] Iterative change layout (`active-change.json` + `.solidsdd/changes/<change_id>/`) — [../reference-src/change-lifecycle.md](../reference-src/change-lifecycle.md)
- [ ] Publish template repository on GitHub
- [ ] Additional feedback from external production projects

## Phase 5: Hardening

**Status: Milestones M1–M4 shipped** ([hardening-plan.md](hardening-plan.md)). Raise mechanical assurance so requirements hardness does not bottom out in LLM judgment alone.

Ordered workstreams (see plan for schemas, acceptance, and open decisions):

1. ID traceability (`covers` chain) — P0 — **done**
2. Deterministic pre-critique lint (`scripts/solidsdd-lint`) — P0 — **done**
3. Orchestrator state persistence (`run-state.json`, per-item plans/reports) — P0/P1 — **done**
4. Structured NFRs (`nfr.json`) + critique regression corpus — P1 — **done**
5. CI, approval records, cross-change checks, richer examples; optional EARS entry — P1–P3 — **done** (EARS pattern lint deferred)

## Phase 5b: Intent-inspired improvements

**Status: I1–I4 shipped** ([intent-inspired-improvements.md](intent-inspired-improvements.md)).

Borrow maturity, conditional Grill, Means vs tech, clarifications, facets / knowledge consistency, and deterministic `next`+validate from Intent-Driven Development tooling — without making Change Context / Brief a living intent-tree. GitHub four-thread loops remain out of scope.

## Phase 6: Structural design (ArchitecturePlan)

**Status: shipped.** Minimal, first-class representation of system structure
(modules / dependencies / dependency direction / public boundaries / ownership /
structural constraints), distinct from `ApplicationPlan` (which specification
technique applies where) — see [architecture.md](architecture.md) "Architecture
judgment" and [../reference-src/architecture-axes.md](../reference-src/architecture-axes.md).
Not a design methodology: no DDD / Clean / Hexagonal / Onion / MVC / CQRS / Event
Sourcing requirement.

- [x] `ArchitecturePlan` schema (`status: changed` / `unchanged` shortcut, `modules[]` / `dependencies[]` / `constraints[]`) — [../schemas/architecture-plan.schema.json](../schemas/architecture-plan.schema.json)
- [x] `solidsdd-architecture` skill (judgment only; no contract/implementation edits) — [../skills/solidsdd-architecture/SKILL.md](../skills/solidsdd-architecture/SKILL.md)
- [x] Architecture Review folded into `solidsdd-critique` (`subject: architecture_plan`, Checkpoint Review, skipped on `status: unchanged`) — [../reference-src/adversarial-critique.md](../reference-src/adversarial-critique.md)
- [x] Mechanical Architecture Verification (dependency/module existence, forbidden dependency, declared-cycle detection) via `scripts/solidsdd-lint.sh`, reused for free by every `solidsdd-critique` call
- [x] Minimal `solidsdd-run` integration (one conditional step between WorkPlan and the wave loops; `solidsdd-loop` / plan-slice-cheatsheet untouched)
- [x] One existing example demonstrates the artifact — [../examples/inventory-reservation](../examples/inventory-reservation) `structure-inventory-reservation-split`
- [x] Schema / verification / regression tests via the existing `evals/critique/cases` harness
- [x] Documentation (this file, [architecture.md](architecture.md), [../reference-src/architecture-axes.md](../reference-src/architecture-axes.md))
- [ ] Per-language static import cross-check against the actual codebase (deliberately deferred — future per-language adapter, not required for the mechanical checks above)

## Phase 6b: Structurizr DSL Architecture Model

**Status: shipped.** Evolved Phase 6 from "structural judgment producing one
change-level JSON delta" into "structural judgment that edits a persistent,
whole-project Architecture Model, plus a separate record of *why*." See
[architecture.md](architecture.md) "Architecture judgment" output model
(three-layer: DSL / Reasoning / generated projection).

- [x] `.solidsdd/architecture/workspace.dsl` (Structurizr DSL subset, no JVM required) as the structural Source of Truth, persistent across changes — [../reference-src/structurizr-dsl.md](../reference-src/structurizr-dsl.md)
- [x] `.solidsdd/architecture/invariants.yaml` for `forbid_dependency`/`no_cycles` constraints and prose Architecture Invariants (rules *about* the model, not duplicated structure) — [../schemas/architecture-invariants.schema.json](../schemas/architecture-invariants.schema.json)
- [x] `architecture-reasoning.md` per change-level structural decision (Logical Decomposition: responsibility / state / knowledge ownership / change locality; boundary and dependency-direction rationale; trade-offs) — [../reference-src/architecture-reasoning-template.md](../reference-src/architecture-reasoning-template.md)
- [x] `architecture-depth.md` (Level 0–4) so most changes stay at Level 0 and never touch the model — [../reference-src/architecture-depth.md](../reference-src/architecture-depth.md)
- [x] `architecture-plan.json` kept schema-unchanged as a **generated projection** (`scripts/solidsdd-architecture/project.py`, filtered by `change:<change_id>` tags) — never hand-authored, so `solidsdd-lint` / `solidsdd-critique` / `solidsdd-report` / eval fixtures 013–016 keep working unmodified
- [x] Self-contained Python DSL parser/validator (`scripts/solidsdd-architecture/`) — syntax, referenced-element existence, forbidden-dependency / no-cycles / ownership-conflict / parent-child / internal-boundary-leakage checks, folded into `scripts/solidsdd-lint.sh`
- [x] Optional, off-by-default `--with-structurizr-cli` integration with the real Structurizr CLI as a second check (`tools/structurizr/`, mirrors the `tools/tla/` optional-toolchain pattern) — never a hard dependency
- [x] `solidsdd-next` / `run-state.schema.json` gained `architecture` / `critique_architecture` phases (previously the schema and `solidsdd-run-state`'s own phase list didn't accept the phase `solidsdd-run/SKILL.md` step 14b already instructed agents to set)
- [x] `docs/execution-model.md` orchestration diagram / per-skill policy / parent obligations updated to include `solidsdd.architecture` (previously missing)
- [x] Five worked examples: No Architecture Change, New Module, Boundary Split, Dependency Inversion, Concurrency (Architecture → BDD → TLA+) — [../examples/inventory-reservation](../examples/inventory-reservation), [../examples/architecture-dependency-inversion](../examples/architecture-dependency-inversion), [../examples/memory-formal](../examples/memory-formal)
- [x] `solidsdd-judge` reads `architecture-plan.json` (when present, `status: changed`) as read-only context via the new `architecture_public_boundary` signal — [../reference-src/judgment-axes.md](../reference-src/judgment-axes.md); `ApplicationPlan`/`ArchitecturePlan` role separation stays intact (judge never edits the Architecture Model)

## Phase 6c: Architecture Reasoning / Physical Design / Traceability

**Status: shipped.** Sharpened the design flow inside `solidsdd-architecture`
from "Logical structure judgment" into an explicit
`Requirement → Decision Drivers → Logical Architecture → Physical Design →
Implementation` sequence, still gated by [architecture-depth.md](../reference-src/architecture-depth.md)
so most changes stay at Level 0–1. No new persistent Source of Truth: the
Structurizr Model remains authoritative; everything below is change-local
reasoning or a generated/derived check.

- [x] Decision Drivers step (Requirement → Decision Drivers → Design Alternatives → Architecture Decision) plus Consistency/Concurrency Boundary as explicit Logical Decomposition axes — [../reference-src/architecture-axes.md](../reference-src/architecture-axes.md), [../reference-src/architecture-reasoning-template.md](../reference-src/architecture-reasoning-template.md)
- [x] Physical Design as a separate, optional Level-3-only artifact (`physical-design.md`: module/package/directory/class/process/service/database/adapter boundary, Physical Dependency) — [../reference-src/physical-design.md](../reference-src/physical-design.md)
- [x] Architecture Traceability guidance: when an explicit Logical → Physical mapping is worth recording vs. self-evident, migration-coexistence handling, explicit "don't embed filesystem metadata in `workspace.dsl`" rule, and Physical → Implementation reframed as **Implementation Conformance** (finding the code is a lookup; whether it still matches what was declared is a distinct, mechanically-unverified concern) — [../reference-src/architecture-traceability.md](../reference-src/architecture-traceability.md)
- [x] Mechanical cross-check of `physical-design.md` against the Architecture Model (`scripts/solidsdd-architecture/physical.py`: unknown Logical Element references, `A -> B` Physical Dependency lines checked only against `forbid_dependency` — direction is not required to mirror the Logical relationship, since Physical realization may legitimately invert it), folded into `solidsdd-lint.sh` and `solidsdd-architecture.sh validate --change-id` — reuses the existing `forbid_dependency` constraint type, no schema change
- [x] `solidsdd-critique`'s `architecture_plan` Architecture Review reads `physical-design.md` when present and checks it for adequacy (missing/hollow at Level 3, boundary-mechanism mismatch) — [../reference-src/adversarial-critique.md](../reference-src/adversarial-critique.md)
- [x] `solidsdd-run` step 14b documents `physical-design.md` as a possible Architecture output and makes explicit that the whole step (Logical through Physical Design) completes before any implementation wave starts
- [x] 11 new unit tests (`scripts/solidsdd-architecture/test_physical.py`); full existing suite, `sync-skill-references.sh --check`, `check-skill-frontmatter.sh`, and both existing Architecture examples stay green throughout
- [ ] No dedicated Module Skill exists in solid_sdd; Physical Design responsibility stays inside `solidsdd-architecture` (Level 3) rather than being split out prematurely — see "Relation to solid_sdd Skills" in [physical-design.md](../reference-src/physical-design.md)

## Near-term next actions

1. GitHub Release / tag workflow for `install-into-project.sh --repo/--ref` (optional packaging of install-manifest payload)
2. External project adoption → intake in [feedback-tuning.md](feedback-tuning.md), or opt-in design for language-native DbC
3. Optional Markdown/HTML projection skills for human-readable views of contracts (without changing loop authority)
4. Optional: mechanical EARS pattern detection in lint (Workstream G follow-on)
5. Honor [run-cost.md](run-cost.md) on future live replays (follow-on co-delivered slices, **B1–B5** cost skips, context packs, strict Task isolation where producers still run)
6. Live replay with `scripts/solidsdd-next.sh` on a sample change (resume smoke)
