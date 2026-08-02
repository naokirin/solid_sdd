# Work decomposition (solidsdd.decompose)

`solidsdd-decompose` turns a requirement (or large change intent) into a **WorkPlan**: ordered work items for `solidsdd-run`. Each item drives **one** `solidsdd-loop` (slice). This is **not** an `ApplicationPlan` — contract kind/density stays in `solidsdd-judge` inside each loop.

## Slice rule (required)

- **One item = exactly one verifiable acceptance criterion**
- “Verifiable” means a later `solidsdd-verify` (and formal verify when in scope) can **pass or fail** the criterion without human interpretation of vague prose
- If the requirement is already a single verifiable criterion → emit a WorkPlan with **one** item (no special skip path)

## Do

- Cover the whole requirement: union of item criteria (+ `acceptance_of_whole`) must not leave silent gaps
- Prefer criteria that map to existing contract checks (API responses/errors, OCL-derived tests, TLC invariants) or clearly extendable ones
- Order via `depends_on` (acyclic); set initial `status` to `ready` when `depends_on` is empty, else `pending`
- Prefer independent items (empty `depends_on`) when slices do not need each other’s artifacts — `solidsdd-run` will execute a wave of all `ready` items **in parallel**
- Set `human_gate` / low `confidence` when the requirement is ambiguous or slicing is uncertain

## Do not

- Emit OpenAPI / OCL / formal / implementation / test edits
- Emit `ApplicationPlan` or choose `api` / `dbc` / `formal` density (that is `solidsdd-judge`)
- Pack multiple independent acceptance criteria into one item
- Slice so finely that a criterion cannot be checked in isolation (merge if verify would be vacuous)

## Examples of good vs bad criteria

| Good (one checkable AC) | Bad |
|-------------------------|-----|
| `POST /div` returns 400 (or domain error) when `divisor=0` | “Make division robust” |
| Contract tests for `mod` preconditions pass | “Finish arithmetic module” |
| OpenAPI documents `add` request/response schemas | “Improve the API” |

## Relation to orchestrators

| Skill | Role |
|-------|------|
| `solidsdd-run` | Outer: decompose → critique(work_plan) → loop per item → final verify |
| `solidsdd-loop` | Inner: one slice intent → judge → apply → implement → verify |
| `solidsdd-decompose` | Producer of WorkPlan only |
