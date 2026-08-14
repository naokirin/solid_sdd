# Gherkin requirements (solidsdd.decompose)

Requirements entering `solidsdd-run` / `solidsdd-decompose` use **Gherkin** (Feature / Scenario / Given–When–Then), not free-form natural language alone. Prefer **property-level** Scenarios that cover requirement intent—not a pile of single concrete examples as the only acceptance text.

## Why

Structured scenarios reduce silent gaps (missing actors, preconditions, failure paths) before contracts and implementation. The goal is **checkable slicing and requirement coverage**, not human-facing prose docs and not example-only specs.

## Role split (required)

| Layer | Format | Role |
|-------|--------|------|
| Framing / rationale | Change Context (`change-context.md`) | Demand, NFRs, tech selection, judgments |
| Change premise | ChangeBrief | Goals, in/out of scope, assumptions (return point) |
| Optional shall-statements | EARS patterns in Brief `text` | What the system shall do ([ears-requirements.md](ears-requirements.md)) |
| Requirements | Gherkin (`.feature`) | Property-level acceptance; input to decompose |
| WorkPlan item | One Scenario (text in `acceptance_criterion`) | One `solidsdd-loop` slice |
| Boundary contracts | OpenAPI / GraphQL | Machine-checkable I/O |
| Module DbC | UML OCL | Machine-checkable pre/post/inv |
| Executable checks | OCL-derived tests + API lint / formal when in scope | Verify |

**Do not** treat Gherkin as the executable test source of truth. Do not require Cucumber (or equivalent) to green the loop. Mapping Scenario → API/OCL/tests is `solidsdd-judge` / apply / derive / verify.

Concrete numeric examples belong in optional `Examples` tables, OCL-derived tests, or brief illustrations—not as the sole statement of the property.

## Artifact layout (default)

| Artifact | Path |
|----------|------|
| Feature files | `requirements/**/*.feature` |

Override via `.solidsdd/config.yaml` (`paths.requirements` / `paths.requirements_glob`). Decompose may **write or update** `.feature` files when normalizing from a ChangeBrief or incomplete Gherkin. Feature files **accumulate across changes**; each new Scenario must map to the **active** ChangeBrief’s `in_scope` / WorkPlan items. See [change-lifecycle.md](change-lifecycle.md).

## Conventions (property-level)

1. Prefer Scenarios that state a **general property** (e.g. addition returns the sum; zero divisor fails with a named domain error) over one-off examples (`2+3=5`) as the only acceptance text.
2. One **Feature** groups related behavior; each property-level **Scenario** (or independently checkable **Scenario Outline**) is one WorkPlan item when independently verifiable.
3. Optional `Examples` / illustration steps may pin a representative case; they must not replace the property statement in `Then`.
4. Name failure paths explicitly (zero divisor → named domain error). Find them systematically, not only when a failure is an obvious domain axiom like division by zero — for **any** operation under decomposition, check: does it reference an existing entity by id/key (→ add a not-found Scenario)? Does it transition an entity to a new state (→ add an already-in-target-state / invalid-transition Scenario)? Does it have a stated capacity/uniqueness constraint (→ add a violation Scenario)? Do this **at decompose time**, from the Brief/domain reasoning alone — do not leave failure-path discovery to a later contract layer (an OCL `pre`, an API error response). A contract that names a failure mode with no matching Gherkin Scenario is backwards: it invented a requirement the acceptance layer never stated (see [adversarial-critique.md](adversarial-critique.md) "Failure-path traceability gap").
5. Cover ChangeBrief `in_scope` / `success_criteria` **ids**: tag each Scenario with `@R1` / `@SC1` (etc.) matching the owning WorkPlan item’s `covers`. Do not pull in `out_of_scope` (`@X*`).
6. On later changes, **add or update** Scenarios for the new Brief only; treat destructive rewrites of existing Scenarios as breaking and surface them in Brief / critique.
7. Exploratory UX may stay thin: still prefer a minimal property Scenario over prose; judge may later choose `natural_only` / density `thin`.
8. Language: Feature/Scenario titles and step prose follow the project **working language** ([working-language.md](working-language.md), usually from the project rule); keep keywords (`Feature`, `Scenario`, `Given`, `When`, `Then`) in English.

## Example (preferred shape)

```gherkin
Feature: Arithmetic calculator operations

  @R1 @SC1
  Scenario: Addition returns the sum of its operands
    Given a calculator service available to clients
    When the client adds two numbers
    Then the result equals the mathematical sum of those operands

  @R2 @SC2
  Scenario: Division by zero fails with a named domain error
    Given a calculator service available to clients
    When the client divides by zero
    Then the operation fails with a named domain error
    And the failure is not an opaque language or runtime error
```

Avoid making the only Scenario for addition be `When adds 2 and 3 / Then result is 5` without stating the general property.

## Example (failure-path identification for reference/state-transition operations)

An operation that looks up an entity by id and moves it to a new state has (at least) three properties, not one — the success path plus one Scenario per structural failure check from convention 4 above:

```gherkin
Feature: Exclusive job claiming

  @R2
  Scenario: Claiming an unclaimed job transitions it to claimed
    Given an unclaimed job exists
    When a worker claims that job
    Then the job transitions to claimed by that worker

  @R2
  Scenario: Claiming an already-claimed job fails with a named domain error
    Given a job has already been claimed by another worker
    When a worker attempts to claim that same job
    Then the claim fails with a named "already claimed" error
    And the existing claim is unchanged

  @R2
  Scenario: Claiming a nonexistent job fails with a named not-found error
    Given no job with the given id exists
    When a worker attempts to claim that job id
    Then the claim fails with a named not-found error
```

Writing only the first Scenario and letting a later OCL `pre` (or API error branch) invent the other two is the anti-pattern convention 4 forbids — those two failure modes were derivable from "claim references an existing job by id and transitions it to a terminal-ish state" at decompose time, before any contract existed.

## Critique expectations

`solidsdd-critique` (`subject: work_plan`) runs **deterministic lint first** (`scripts/solidsdd-lint.sh`): missing `covers`, missing Scenario tags, non-Gherkin acceptance, and dependency cycles fail without LLM judgment. The LLM pass then judges *adequacy* of coverage. Prefer **minor** (or omit) for “could use a more representative example” when a property-level Scenario is already checkable. See [adversarial-critique.md](adversarial-critique.md).
