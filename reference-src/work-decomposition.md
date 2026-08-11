# Work decomposition (solidsdd.decompose)

`solidsdd-decompose` turns a **ChangeBrief** (preferred) or raw requirement into a **WorkPlan**: ordered work items for `solidsdd-run`. Each item drives **one** `solidsdd-loop` (slice). This is **not** an `ApplicationPlan` — contract kind/density stays in `solidsdd-judge` inside each loop.

Requirements are expressed in **property-level Gherkin**. See [gherkin-requirements.md](gherkin-requirements.md). Scope premise: [change-brief.md](change-brief.md). Item titles, `acceptance_criterion` strings, and Feature step prose use the project **working language**; JSON keys stay English ([working-language.md](working-language.md)).

## Slice rule (required)

- **Scenario vs Slice separation**: A Scenario is a "behavior to verify"; a Slice (WorkPlan item) is a "unit of coherent implementation change".
- Multiple Scenarios sharing the same implementation boundary, related files, or domain **must be grouped into a single Slice** (one WorkPlan item).
- **Prohibit micro-items**: Do **not** emit `vocabulary-only`, `schema-only`, `test-only`, or `verify-only` WorkPlan items. Contract additions and verify criteria must be co-delivered inside the Slice that implements the change.
- That criterion **must** be property-level Gherkin Scenario(s) — Given / When / Then (And / But as needed) — covering ChangeBrief `in_scope` / `success_criteria` **ids** via required `covers: ["R1", "SC1", …]`.
- Tag the matching Scenario in `requirements/**/*.feature` with the same ids (`@R1 @SC1`).
- “Verifiable” means a later `solidsdd-verify` (and formal verify when in scope) can **pass or fail** the criterion without human interpretation of vague prose.
- If the requirement is already expressed in a single coherent change → emit a WorkPlan with **one** item (no special skip path).
- Prefer aligning items with `requirements/**/*.feature`; set optional `feature_path` / `scenario_name` when files exist or are written.
- Recommended: set WorkPlan `change_id` to the active change id.
- See [docs/cost-reduction-plan.md](../docs/cost-reduction-plan.md) for overall execution efficiency goals.

## Do

- Resolve the active ChangeBrief via `.solidsdd/active-change.json` → `.solidsdd/changes/<change_id>/change-brief.json` (or project override / legacy migration per [change-lifecycle.md](change-lifecycle.md)); treat it as scope authority
- Write the WorkPlan to `.solidsdd/changes/<change_id>/work-plan.json` (same directory as the active Brief)
- If input is prose or incomplete Gherkin, **normalize** into Feature/Scenario form (update or create `.feature` under the default layout) before or while emitting the WorkPlan; new Scenarios must belong to this Brief’s `in_scope` and carry `@R*` / `@SC*` tags
- Cover the whole ChangeBrief: union of `items[].covers` must include every `in_scope` and `success_criteria` id; never put `out_of_scope` (`X*`) ids in `covers`
- Do not emit items that implement `out_of_scope`
- Prefer criteria that map to existing contract checks (API responses/errors, OCL-derived tests, TLC invariants) or clearly extendable ones
- On **follow-on** changes, apply [Follow-on / co-delivered slices](#follow-on--co-delivered-slices-cost-required-when-applicable) before inventing a foundation→properties split
- Order via `depends_on` (acyclic); set initial `status` to `ready` when `depends_on` is empty, else `pending`
- Prefer independent items (empty `depends_on`) when slices do not need each other’s artifacts — `solidsdd-run` will execute a wave of all `ready` items **in parallel**
- Set optional **`touches`**: paths this item’s loop will primarily edit (e.g. `openapi/openapi.yaml`, `contracts/Memory.ocl`). `solidsdd-run` serializes ready items whose `touches` sets intersect; omit only when contention is impossible to know
- Set `human_gate` / low `confidence` when the requirement is ambiguous or slicing is uncertain; if Brief has blocking `open_questions`, prefer gate / re-brief over inventing scope

## Greenfield / shared-contract changes (required when applicable)

When the consuming project has **no** (or empty) OpenAPI / OCL / package scaffold yet, or every property Scenario will edit the **same** primary paths:

1. **Do not** emit N independent `ready` items that all list the same `touches` (e.g. every item touches `openapi/openapi.yaml` + one OCL + one `src` module) with empty `depends_on`. That forces **N full serial loops** over shared files and balloons wall-clock cost without improving checkability.
2. Prefer a **foundation → properties** shape **for greenfield scaffold** (no usable OpenAPI/OCL/package yet):
   - First item (or explicit scaffold intent): establish shared surfaces (OpenAPI skeleton, module OCL shell, package/test harness) while covering the first property Scenario when possible
   - Later property items: `depends_on: ["<foundation-id>"]` (or a short chain), `status: pending` until the foundation is `done`
3. Set **`touches` honestly but narrowly** when a later item only extends one artifact (e.g. OCL + tests only). Do not copy the full shared-path set onto every item “for safety” if that item will not edit those paths.
4. Still keep **one Scenario per item** for **independent** properties — do not pack unrelated behaviors into one item merely to save loops. Fix serial shared-path cost with `depends_on` / narrow `touches` first.
5. When contracts already exist (follow-on change or mid-run after foundation), later ApplicationPlans should **extend**, not re-scaffold (judge/apply stay additive).

### Follow-on / co-delivered slices (cost; required when applicable)

Wall-clock scales with **item count × loop steps** ([docs/run-cost.md](../docs/run-cost.md)). Extra items that cannot fail independently of another item’s implementation burn full loops without extra checkability.

1. **No vocabulary-only foundation on follow-on changes.** If OpenAPI / OCL (or equivalent) already exist and this change only **adds** an operation/channel, do **not** emit a separate item whose sole acceptance is “contracts document the new vocabulary.” Fold additive contract elevation into the property-delivery item that will `apply` + `derive-tests` + `implement` in one loop.
2. **Co-delivered channels of the same operation → one item (usually one Scenario).** Success and failure of the **same** operation on a shared code path (e.g. authorized collection list **and** `UnauthorizedError` on that list; empty and nonempty success dumps) should be **one** verifiable Scenario (multiple Then / And) covering the related Brief ids—not N items that serialize on the same `src` / contract-test files. Split only when verify of A can pass while B’s implementation is still absent (true independence).
3. **Merge when a sibling verify would be vacuous.** If item B’s acceptance cannot fail once item A’s implement is green (same function / same derived suite), merge B into A (or drop B) rather than running a judge→skip-plan→verify-only loop.
4. Prefer **N = 1** WorkPlans for small additive follow-ons when union of `covers` still maps to one checkable Scenario and one primary touch set.

Critique / lint may flag “all ready items share intersecting touches with no depends_on edges” as a **minor** decomposition smell, and may flag **follow-on vocabulary-only items** or **AuthZ success/failure split across items with identical `src` touches** similarly (solid_sdd [docs/run-cost.md](../docs/run-cost.md); skill copy: [run-cost.md](run-cost.md) when bundled).

## Do not

- Emit OpenAPI / OCL / formal / implementation / test edits (Feature files for requirements are allowed)
- Emit or overwrite ChangeBrief (that is `solidsdd-brief`)
- Emit `ApplicationPlan` or choose `api` / `dbc` / `formal` density (that is `solidsdd-judge`)
- Pack multiple independent Scenarios into one item
- Leave `acceptance_criterion` as unstructured prose when a Scenario can express the check
- Omit `covers` or rely on prose match alone for Brief coverage
- Treat Gherkin as Cucumber (or equivalent) executable SoT—verification stays on API / OCL-derived tests / formal
- Slice so finely that a criterion cannot be checked in isolation (merge if verify would be vacuous)
- Expand scope beyond the ChangeBrief without updating the brief first

## Examples of good vs bad criteria

| Good (property-level Scenario) | Bad |
|--------------------------------|-----|
| `Scenario: Division by zero fails with a named domain error` with Given/When/Then | “Make division robust” |
| `Scenario: Addition returns the sum of its operands` | Only `2+3=5` with no general property (weak coverage) |
| `Scenario: Memory clear yields zero on subsequent recall` | “Finish memory module” |

## Relation to orchestrators

| Skill | Role |
|-------|------|
| `solidsdd-run` | Outer: brief → decompose → critique → loop per item → final verify |
| `solidsdd-loop` | Inner: one slice intent → judge → apply → implement → verify |
| `solidsdd-brief` | Producer of ChangeBrief (scope premise) |
| `solidsdd-decompose` | Producer of WorkPlan (+ optional `.feature` normalization) only |
