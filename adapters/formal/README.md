# Formal specification adapter

## Role

Express **safety / liveness / concurrency** properties that API contracts and OCL→tests do not cheaply cover. Formal specs are **optional** and narrow-scope. Prefer OpenAPI/GraphQL + OCL unless the apply conditions below hold.

## When to `apply` (vs `defer`)

Prefer `status: apply` for `kind: formal` only when **all** hold:

1. Signal `concurrency_safety` (or equivalent: distributed consensus, multi-writer shared state, failover) is present **and** density would be `strict`, **or** product policy marks the boundary as safety-critical
2. A formal adapter is available (`adapter_hint` e.g. `tla`, `alloy`) and the checker is documented for the project
3. Scope is bounded (one protocol / one shared resource)—not “formalize the whole app”
4. `human_gate.required: true` (mandatory for early formal apply)

Otherwise keep `status: defer` with `adapter_hint: defer-formal`. Never silently drop formal need.

Rule of thumb: formal specs check properties that contract tests cannot cheaply falsify (interleavings, global invariants across processes). If a Vitest/RSpec example is enough, stay on DbC.

## Default checker: TLA+ / TLC

| Choice | Role |
|--------|------|
| **TLC** (default) | Model-check `.tla` + `.cfg` |
| Apalache | Optional later (inductive invariants) |
| Alloy | Optional alternate notation (`adapter_hint: alloy`) |

### TLC setup (consuming project)

1. JDK 17+ (Temurin recommended)
2. Provide a TLC runner the project documents (common pattern: `tools/tla/fetch-tla2tools.sh` then `tools/tla/tlc.sh`, or a project `./verify.sh` wrapper)
3. Do not commit `tla2tools.jar` unless the project explicitly chooses to

If jar/JDK/runner is missing: `failure_class: tooling`, `loop_action: stop` or `human_gate`.

## Artifact layout (default)

| Artifact | Path |
|----------|------|
| TLA+ modules | `formal/**/*.tla` |
| TLC configs | `formal/**/*.cfg` |
| Alloy models | `formal/**/*.als` (optional) |

## Responsibilities

- Keep models small (one protocol / shared resource)
- Name invariants and temporal properties explicitly
- Do not duplicate OpenAPI field lists or OCL arithmetic posts in the formal model
- Flag tooling gaps; never pretend a model was checked if the checker did not run

## Verification hooks

- Parse / type-check via TLC
- Run the project TLC command, e.g. `tools/tla/tlc.sh <Spec.tla> -config <Spec.cfg>` or `./verify.sh`
- On invariant violation: prefer `solidsdd-apply-formal` (spec) unless implementation SoT is clearer

## Skill mapping

- Write/update: `solidsdd-apply-formal` (`adapter_hint: tla`)
- Check: `solidsdd-verify-formal` (VerificationReport check kind `formal`)

## Evaluation sample shape

A typical sample is exclusive shared-memory adds under a small `Clients` bound: TLC must report no error (e.g. “No error has been found”).
