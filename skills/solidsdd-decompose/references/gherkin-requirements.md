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
4. Name failure paths and cross-cutting properties explicitly, systematically — not only when one is an obvious domain axiom (zero divisor → named domain error). Do this **at decompose time**, from Brief/domain reasoning alone; do not leave it for a later contract layer to invent (see checklist below).
5. Cover ChangeBrief `in_scope` / `success_criteria` **ids**: tag each Scenario with `@R1` / `@SC1` (etc.) matching the owning WorkPlan item’s `covers`. Do not pull in `out_of_scope` (`@X*`).
6. On later changes, **add or update** Scenarios for the new Brief only; treat destructive rewrites of existing Scenarios as breaking and surface them in Brief / critique.
7. Exploratory UX may stay thin: still prefer a minimal property Scenario over prose; judge may later choose `natural_only` / density `thin`.
8. Language: Feature/Scenario titles and step prose follow the project **working language** ([working-language.md](working-language.md), usually from the project rule); keep keywords (`Feature`, `Scenario`, `Given`, `When`, `Then`) in English.

## Failure-path & cross-cutting-property checklist (required)

**The rule, not a fixed list**: for every operation-shaped Scenario, partition its inputs, current state, calling actor, and any stated cross-call guarantee into classes that would produce a **distinguishable, product-visible outcome** — one the caller/observer would have to handle or notice differently. Write **one Scenario per distinguishable class**; classes that fold into identical handling stay in one Scenario (optionally an `Examples` table per convention 3) rather than being split. Do this **at decompose time**, from Brief/domain reasoning alone — do not defer class discovery to a later contract layer (OCL `pre`, API error response, formal spec); a contract/formal model naming an outcome with no matching Gherkin Scenario is backwards (see [adversarial-critique.md](adversarial-critique.md) "Failure-path / concurrency-scenario traceability gap").

Common instances of this rule — **not exhaustive**; reason from the operation itself, don't just pattern-match this table:

| The operation or requirement… | …commonly has this distinguishable class too |
|---|---|
| Looks up or selects an existing entity by some criterion (id, key, filter, query — not only "by id") | A no-match ("not found") class |
| Transitions state, or behaves differently depending on current state | One Scenario per behaviorally-distinct state, not only the target transition |
| Has required, typed, or bounded input | An invalid / out-of-range input class |
| Has a stated capacity or uniqueness constraint | A constraint-violation class |
| States an invariant across simultaneous actors ("exactly one wins", "never both succeed") | A **concurrent-attempt** class, in addition to — not instead of — any single-caller state class above |
| Distinguishes callers by identity/permission **and the product has decided a distinct outcome for it** | An unauthorized-actor class (if authorization is not yet decided, that is an open Change Context / `authz_boundary` question, not something to invent here) |
| States a repeat-safety / idempotency guarantee | A repeated-call class |

**Usually not a Gherkin class** — these belong in `nfr.json` / Change Context instead, unless they change an observable functional outcome (e.g. a size threshold that triggers pagination *is* a class):
- Pure scale / volume / latency thresholds with no distinct functional outcome
- Infra or external-dependency failure with no product-committed behavioral contract yet
- Which exception type or log line an implementation uses (OCL / API / formal's job, not Gherkin's)

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

## Critique expectations

`solidsdd-critique` (`subject: work_plan`) runs **deterministic lint first** (`scripts/solidsdd-lint.sh`): missing `covers`, missing Scenario tags, non-Gherkin acceptance, and dependency cycles fail without LLM judgment. The LLM pass then judges *adequacy* of coverage. Prefer **minor** (or omit) for “could use a more representative example” when a property-level Scenario is already checkable. See [adversarial-critique.md](adversarial-critique.md).
