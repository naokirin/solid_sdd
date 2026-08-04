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
- [x] Consumer install guide ([install.md](install.md) — self-contained `gh skill` skills)
- [x] `skills/*/references/` sync script (`scripts/sync-skill-references.sh`)
- [x] Cursor / Claude Code hooks + git pre-commit (error + fix command on drift)
- [ ] `gh skill publish` for [naokirin/solid_sdd](https://github.com/naokirin/solid_sdd) (release / `agent-skills` topic)

## Phase 1: MVP (minimal connected system)

**Status: evaluation complete** (see [mvp-evaluation.md](mvp-evaluation.md)). Distribution (`gh skill publish`) deferred.

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

## Near-term next actions

1. `gh skill publish` for [naokirin/solid_sdd](https://github.com/naokirin/solid_sdd) (distribution)
2. External project adoption → intake in [feedback-tuning.md](feedback-tuning.md), or opt-in design for language-native DbC
3. Optional Markdown/HTML projection skills for human-readable views of contracts (without changing loop authority)
4. Optional: mechanical EARS pattern detection in lint (Workstream G follow-on)
5. Honor [run-cost.md](run-cost.md) on future live replays (greenfield WorkPlan + strict Task isolation)
6. Live replay with `scripts/solidsdd-next.sh` on a sample change (resume smoke)
