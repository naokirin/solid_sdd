# Coexistence with other SDD tools

solid_sdd complements—not replaces—natural-language Spec-Driven Development loops (e.g. Kiro-style: NL spec → design/implement/test). Target users want a **harder, agent-autonomous** path from structured requirements through contracts and verify; teams that mainly want free-form NL flexibility are usually better served by host SDD tools alone.

## Ownership split

| Concern | Typical NL SDD tool | solid_sdd |
|---------|---------------------|-----------|
| Product narrative, UX copy, exploratory design | Primary | Thin Brief / Gherkin / `natural_only` or skip |
| Change premise (goals, in/out of scope) | Optional / chat | **Primary**: ChangeBrief (return point) |
| Framing (demand, NFR, tech selection) | Optional / chat | **Primary**: Change Context Markdown |
| Requirement structure (acceptance scenarios) | Optional / prose | **Primary intake**: property-level Gherkin → WorkPlan |
| HTTP/GraphQL boundary contracts | Optional / generated docs | **Primary** (OpenAPI / GraphQL SDL) for the active change |
| Module pre/post (DbC) | Rare | **Primary** (OCL → contract tests) |
| Concurrency / safety properties | Rare | **Optional formal** (TLA+/TLC), human-gated |
| “Make the feature work” coding loop | Primary implementer | `solidsdd-implement` only after contracts exist |
| Apply density (where to put contracts) | Human judgment | **`solidsdd-judge` + axes** (guided by Brief) |

## Artifact stance

Machine-checkable outputs are for **gap reduction and mechanical verification during a change**, not everlasting living docs. History of “what was specified then” is fine; requiring perpetual human editorial ownership of every past contract is not.

**Reuse**: keeping contracts from continuous active development is healthy. Reusing stale contracts from dormant / poorly maintained work is usually unsafe. Fitness is **situational**—not a single toolkit default.

## Recommended patterns

### 1. Explore in NL, enter solid_sdd via Change Context + Brief + Gherkin

1. Explore with the host SDD / agent using natural language if needed.
2. Before `solidsdd-run` on non-trivial work, produce Change Context (`solidsdd-intake`) then ChangeBrief (`solidsdd-brief`) then property-level Gherkin via `solidsdd-decompose`.
3. Treat OpenAPI/OCL/TLA+ as loop authority for those boundaries; Gherkin structures acceptance and is **not** Cucumber SoT; Change Context holds tech/NFR rationale; Brief is the scope return point.

### 2. Next product increment = new change

When additional requirements arrive after a delivered change:

1. Do **not** edit the previous Brief into a living product PRD.
2. Start a new meaningful `change_id` (`solidsdd-brief` / `solidsdd-run`); keep prior Features and contracts as baseline via `solidsdd-context`.
3. Put only the delta in the new Brief’s `in_scope`; preserve existing behavior via `assumptions` / `constraints`.

See [../reference-src/change-lifecycle.md](../reference-src/change-lifecycle.md).

### 3. Contracts first for risky changes

For breaking API, money, or authz surfaces: run solid_sdd **before** broad implementation so verify catches drift early.

### 4. Do not double-own the same artifact

| If… | Then… |
|-----|-------|
| ChangeBrief is scope authority | Do not invent out-of-scope features in WorkPlan / contracts without updating the Brief |
| OpenAPI is loop authority | Do not also maintain a conflicting hand-written “API markdown contract” as authority |
| OCL is loop authority | Do not hand-edit derived contract tests as primary |
| Gherkin is requirement intake | Do not require Cucumber (or equivalent) to green verify |
| NL tool regenerates OpenAPI loosely | Prefer solid_sdd `apply-api` or merge carefully; verify must win |

### 5. Formal stays rare

Leave TLA+/TLC to `concurrency_safety` (or policy-marked safety-critical) paths. NL SDD tools should not be expected to author formal models.

## Conflict resolution

1. **Verify fails** → fix implementation or correct the contract via apply skills; never weaken contracts only to green the NL loop.
2. **Critique fails** (scope gap, thin contracts, density bias, weak tests, missing Gherkin structure) → re-run the **source** solid_sdd skill (`brief` / `decompose` / `judge` / `apply-*` / `derive-tests`); do not paper over with implement-only fixes.
3. **NL agent and solid_sdd disagree on density** → re-run `solidsdd-judge` as a subagent; do not thin the plan in the parent.
4. **Scope ambiguity** → re-read or re-run `solidsdd-brief` before expanding WorkPlan or contracts.
5. **Human gate** → NL automation must pause the same way `solidsdd-loop` / `solidsdd-run` does.

## Non-goals

- Replacing the host IDE’s agent product
- Forcing every change through formal specs
- Mandating language-native contract gems
- Mandating Cucumber (or equivalent) as the verification runner
- Replacing host NL tools with a long-form living PRD inside solid_sdd
