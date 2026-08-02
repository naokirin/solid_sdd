# Change lifecycle (iterative development)

solid_sdd models work as a sequence of **changes**. Each change has its own ChangeBrief and WorkPlan. Cross-change artifacts (Gherkin, OpenAPI, OCL, tests, formal) **accumulate** in the repo via create/update. ChangeBrief is **not** a living product PRD—start a **new** change for additional requirements instead of editing an old brief into a perpetual scope document.

See also: [change-brief.md](change-brief.md), [contract-layout.md](contract-layout.md), [gherkin-requirements.md](gherkin-requirements.md).

## Layout

```text
.solidsdd/
  active-change.json                 # points at the active change_id
  changes/
    <change_id>/
      change-brief.json
      work-plan.json                 # after solidsdd-decompose
      status.json                    # active | done | abandoned
```

| Artifact | Path | Role |
|----------|------|------|
| Active pointer | `.solidsdd/active-change.json` | Which change is in progress |
| ChangeBrief | `.solidsdd/changes/<change_id>/change-brief.json` | Scope premise / return point |
| WorkPlan | `.solidsdd/changes/<change_id>/work-plan.json` | Slice plan for this change |
| Status | `.solidsdd/changes/<change_id>/status.json` | Lifecycle state |
| Features / contracts | `requirements/`, `openapi/`, `contracts/`, `tests/`, `formal/` | Cross-change accumulation |

## Resolving the active ChangeBrief

1. Read `.solidsdd/active-change.json` → `change_id`.
2. Use `.solidsdd/changes/<change_id>/change-brief.json` as the return point.
3. WorkPlan (when present): `.solidsdd/changes/<change_id>/work-plan.json`.

Projects may override paths via a project rule. Do **not** keep a second SoT at `.solidsdd/change-brief.json` (legacy only; see migration below).

## `change_id` rules

- **Form**: lowercase kebab-case ASCII, pattern `[a-z0-9]+(-[a-z0-9]+)*`, length about 3–48.
- **Meaningful**: short name derived from the change goal (e.g. `initial-calculator`, `add-operation-history`, `fix-div-zero-error`). No UUIDs.
- **Unique**: under `.solidsdd/changes/`; on collision append `-2`, `-3`, …
- **User override**: if the caller supplies a `change_id` to `solidsdd-brief` / `solidsdd-run`, use it (after validating form); otherwise derive from goal/summary.
- The directory name and `change_brief.json` → `change_id` **must match**.

## Starting a change (including additional requirements)

1. If another change is `active`, finish it (`done`) or explicitly `abandoned` before switching—or the new brief run replaces `active-change.json` after writing the previous status when appropriate.
2. Run `solidsdd-context` so existing Features and contracts are visible.
3. Run `solidsdd-brief` with the **new** request only:
   - Choose / derive `change_id`.
   - Create `.solidsdd/changes/<change_id>/`.
   - Write `change-brief.json` (`in_scope` = this delta only).
   - Write `status.json` with `"status": "active"`.
   - Write / update `active-change.json`.
4. Preserve prior behavior via `assumptions` / `constraints` (and `out_of_scope` when re-design of old surfaces is excluded). Do not copy the entire product into `in_scope`.
5. Continue with critique → `solidsdd-decompose` → loops as usual.

## Completing a change

When `solidsdd-run` (or the human) finishes integration verify successfully:

1. Set `.solidsdd/changes/<change_id>/status.json` to `"status": "done"`.
2. Leave Brief / WorkPlan in place as history.
3. The next requirement starts a **new** `change_id` (do not enlarge the old Brief into a product PRD).

Use `"abandoned"` when the change is stopped without delivery.

## Feature and contract accumulation

| Artifact | Across changes |
|----------|----------------|
| `requirements/**/*.feature` | Create or **update**; new Scenarios for the active Brief’s `in_scope`. Destructive edits to existing Scenarios are breaking—surface in Brief / critique. |
| OpenAPI / GraphQL / OCL / formal / derived tests | `apply-*` add/update; do not break unrelated surfaces. |

Additional Scenarios belong to the **active** change’s Brief and WorkPlan items—not to a separate “requirements set” model.

## Legacy migration

Repos that still have only `.solidsdd/change-brief.json` (flat):

1. On the next `solidsdd-brief` or `solidsdd-run` that needs a Brief path, derive a meaningful `change_id` (from existing goal/summary or user input).
2. Create `.solidsdd/changes/<change_id>/`, move the Brief there, add `change_id` to the JSON, write `status.json` (`active` if work continues, else `done`), write `active-change.json`.
3. Move any ad-hoc WorkPlan / critique JSON for that change into the same directory when identifiable.
4. **Delete** the flat `.solidsdd/change-brief.json` so there is a single SoT.

Do not write a deprecated mirror of the Brief at the flat path.

## Example: second change on arithmetic-api

After `initial-calculator` is `done`, a follow-up such as operation history would:

1. Run `solidsdd-context` (existing Features / OpenAPI / OCL visible).
2. Run `solidsdd-brief` with a new id (e.g. `add-operation-history`) whose `in_scope` is only history; assume calculator + memory behavior remains.
3. Decompose → loops that **update** contracts and Features without rewriting unrelated Scenarios.

See `examples/arithmetic-api/.solidsdd/` for the migrated `initial-calculator` layout.
