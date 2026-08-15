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
4. Name failure paths explicitly (zero divisor → named domain error). Find them systematically, not only when a failure is an obvious domain axiom like division by zero — for **any** operation under decomposition, check: does it reference an existing entity by id/key (→ add a not-found Scenario)? Does it transition an entity to a new state (→ add an already-in-target-state / invalid-transition Scenario)? Does it have a stated capacity/uniqueness constraint (→ add a violation Scenario)? Does a `success_criteria` / requirement state an invariant across **multiple simultaneous actors** ("never both succeed", "exactly one wins", "at most one X at a time") (→ add an explicit **concurrent-attempt** Scenario that dramatizes two actors acting at the same time, in addition to — not instead of — any sequential already-in-state Scenario; a sequential check alone does not exercise the interleaving the property is actually about). Do this **at decompose time**, from the Brief/domain reasoning alone — do not leave failure-path or concurrency-scenario discovery to a later contract layer (an OCL `pre`, an API error response, a formal spec). A contract or formal model that names a failure mode or safety property with no matching Gherkin Scenario is backwards: it invented a requirement the acceptance layer never stated (see [adversarial-critique.md](adversarial-critique.md) "Failure-path traceability gap").
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

## Example (failure-path and concurrency-scenario identification for reference/state-transition operations)

An operation that looks up an entity by id, moves it to a new state, and whose `success_criteria` claims an invariant across simultaneous actors has (at least) **four** properties, not one — the success path, one Scenario per structural failure check from convention 4, and one Scenario dramatizing simultaneity:

```gherkin
Feature: Exclusive job claiming

  @R2
  Scenario: Claiming an unclaimed job transitions it to claimed
    Given an unclaimed job exists
    When a worker claims that job
    Then the job transitions to claimed by that worker

  @R2 @SC1
  Scenario: Two workers claiming the same job concurrently — exactly one succeeds
    Given an unclaimed job exists
    And two workers attempt to claim that same job at the same time
    When both claim requests are processed concurrently
    Then exactly one worker's claim succeeds
    And the other worker receives an "already claimed" result

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

Writing only the first Scenario and letting a later OCL `pre` / formal spec invent the other three is the anti-pattern convention 4 forbids — all three were derivable at decompose time, before any contract or formal model existed: the not-found and already-claimed failures from "claim references an existing job by id and transitions it to a terminal-ish state"; the concurrent Scenario from the `success_criteria`'s "exactly one wins" phrasing. Note the concurrent Scenario and the sequential already-claimed Scenario are **not** substitutes for each other — the sequential one checks the state-machine rule, the concurrent one is what later motivates a `concurrency_safety` / `formal` judgment (see [judgment-axes.md](judgment-axes.md)); dropping either leaves a real gap.

## Critique expectations

`solidsdd-critique` (`subject: work_plan`) runs **deterministic lint first** (`scripts/solidsdd-lint.sh`): missing `covers`, missing Scenario tags, non-Gherkin acceptance, and dependency cycles fail without LLM judgment. The LLM pass then judges *adequacy* of coverage. Prefer **minor** (or omit) for “could use a more representative example” when a property-level Scenario is already checkable. See [adversarial-critique.md](adversarial-critique.md).
