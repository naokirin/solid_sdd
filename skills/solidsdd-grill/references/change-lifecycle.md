# Change lifecycle (iterative development)

solid_sdd models work as a sequence of **changes**. Each change has its own Change Context, ChangeBrief, and WorkPlan. Cross-change artifacts (Gherkin, OpenAPI, OCL, tests, formal) **accumulate** in the repo via create/update. ChangeBrief is **not** a living product PRD—start a **new** change for additional requirements instead of editing an old brief into a perpetual scope document.

See also: [change-context.md](change-context.md), [change-brief.md](change-brief.md), [contract-layout.md](contract-layout.md), [gherkin-requirements.md](gherkin-requirements.md), [working-language.md](working-language.md) (prose language for `.solidsdd` artifacts).

## Layout

```text
.solidsdd/
  active-change.json                 # points at the active change_id
  kg/                                # solidsdd-kg schema/config/links (optional until knowledge adopted)
  changes/
    <change_id>/
      change-context.md              # demand, NFR, tech selection (solidsdd-intake)
      nfr.json                       # NFR SoT (Context §4 projection)
      change-context-gate.json       # optional human gate after intake
      change-brief.json
      work-plan.json                 # after solidsdd-decompose
      run-state.json                 # orchestrator phase / retries / item map
      knowledge-consult.md           # solidsdd-knowledge consult snapshot
      knowledge-harvest.json         # solidsdd-knowledge harvest candidates (+ gate)
      gate-approval.json             # latest human gate approval (when gated)
      gate-approvals/                # optional append-only approval history
      items/<item_id>/               # ApplicationPlan, critiques, verification per slice
      report.md                      # optional human snapshot (solidsdd-report)
      report.html                    # optional HTML snapshot
      status.json                    # active | done | abandoned

knowledge/                           # durable cross-cutting nodes (not living Brief)
  concepts/ | policies/ | patterns/ | decisions/ | lessons/
```

| Artifact | Path | Role |
|----------|------|------|
| Active pointer | `.solidsdd/active-change.json` | Which change is in progress |
| Change Context | `.solidsdd/changes/<change_id>/change-context.md` | Demand / NFR / tech selection / judgments |
| NFR SoT | `.solidsdd/changes/<change_id>/nfr.json` | Structured NFRs (Context §4 projection) |
| Change Context gate | `.solidsdd/changes/<change_id>/change-context-gate.json` | Whether to pause before Brief |
| ChangeBrief | `.solidsdd/changes/<change_id>/change-brief.json` | Scope premise / return point |
| WorkPlan | `.solidsdd/changes/<change_id>/work-plan.json` | Slice plan for this change |
| Run state | `.solidsdd/changes/<change_id>/run-state.json` | Phase, waves, retry budgets ([run-state.md](run-state.md)) |
| Knowledge consult | `.solidsdd/changes/<change_id>/knowledge-consult.md` | Existing knowledge pack for framing ([knowledge.md](knowledge.md)) |
| Knowledge harvest | `.solidsdd/changes/<change_id>/knowledge-harvest.json` | Promotion candidates before done ([knowledge.md](knowledge.md)) |
| Gate approval | `.solidsdd/changes/<change_id>/gate-approval.json` | Latest human approval past a gate ([human-gates.md](human-gates.md)) |
| Per-item artifacts | `.solidsdd/changes/<change_id>/items/<item_id>/` | Plans / critiques / verify for each WorkPlan item |
| Change report | `.solidsdd/changes/<change_id>/report.md` (+ optional `report.html`) | Human-readable view (`solidsdd-report`; not SoT) |
| Status | `.solidsdd/changes/<change_id>/status.json` | Lifecycle state |
| Features / contracts | `requirements/`, `openapi/`, `contracts/`, `tests/`, `formal/` | Cross-change accumulation |
| Knowledge graph | `knowledge/`, `.solidsdd/kg/` | Durable cross-cutting knowledge (not change SoT) |

## Resolving the active change

1. Read `.solidsdd/active-change.json` → `change_id`.
2. Framing: `.solidsdd/changes/<change_id>/change-context.md`.
3. Scope return point: `.solidsdd/changes/<change_id>/change-brief.json`.
4. WorkPlan (when present): `.solidsdd/changes/<change_id>/work-plan.json`.
5. Run state (when present): `.solidsdd/changes/<change_id>/run-state.json` — resume phase / retries ([run-state.md](run-state.md)).

Projects may override paths via a project rule. Do **not** keep a second SoT at `.solidsdd/change-brief.json` (legacy only; see migration below).

## `change_id` rules

- **Form**: lowercase kebab-case ASCII, pattern `[a-z0-9]+(-[a-z0-9]+)*`, length about 3–48.
- **Meaningful**: short name derived from the change goal (e.g. `initial-calculator`, `add-operation-history`, `fix-div-zero-error`). No UUIDs.
- **Unique**: under `.solidsdd/changes/`; on collision append `-2`, `-3`, …
- **User override**: if the caller supplies a `change_id` to `solidsdd-intake` / `solidsdd-brief` / `solidsdd-run`, use it (after validating form); otherwise derive from goal/summary.
- The directory name and `change_brief.json` → `change_id` **must match**.
- **`solidsdd-intake` owns creating** `change_id` + directory for a new change. `solidsdd-brief` reuses the active id.

## Starting a change (including additional requirements)

1. If another change is `active`, finish it (`done`) or explicitly `abandoned` before switching—or the new intake run replaces `active-change.json` after writing the previous status when appropriate.
2. Run `solidsdd-context` so existing Features and contracts are visible.
3. Run `solidsdd-knowledge` (`mode: consult`) when `knowledge/` or `.solidsdd/kg/` exists (or to record “none”); write `knowledge-consult.md` once the change directory exists (intake may create the dir first—then re-run consult or move the draft).
4. Run `solidsdd-intake` with the **new** request:
   - Choose / derive `change_id`.
   - Create `.solidsdd/changes/<change_id>/`.
   - Write `change-context.md` (demand, NFRs, tech selection, judgments).
   - Write `change-context-gate.json` (gate only when framing needs confirmation — [change-context.md](change-context.md)).
   - Write `status.json` with `"status": "active"`.
   - Write / update `active-change.json`.
   - Prefer placing/updating `knowledge-consult.md` in the change dir (re-run consult if it ran before the dir existed).
5. Critique Change Context; if gate `required`, stop until humans approve.
6. Run `solidsdd-brief` against the **active** change (do not invent a second id):
   - Write `change-brief.json` (`in_scope` = this delta only; align with Change Context).
7. Preserve prior behavior via Brief `assumptions` / `constraints` (and `out_of_scope` when re-design of old surfaces is excluded). Do not copy the entire product into `in_scope`.
8. Continue with critique → `solidsdd-decompose` → create/update `run-state.json` + `items/` → loops as usual ([run-state.md](run-state.md)).

## Completing a change

When `solidsdd-run` (or the human) finishes integration verify successfully:

1. Run `solidsdd-knowledge` (`mode: harvest`) → `knowledge-harvest.json`. Critique optionally (`subject: knowledge_harvest`). If `human_gate.required`, obtain `gate-approval.json` (`scope: knowledge_harvest`) before applying any `knowledge/` writes ([knowledge.md](knowledge.md)).
2. Set `.solidsdd/changes/<change_id>/status.json` to `"status": "done"`.
3. Set `run-state.json` `phase` to `done` (keep item artifact dirs as history).
4. Leave Change Context / Brief / WorkPlan in place as history.
5. The next requirement starts a **new** `change_id` (do not enlarge the old Brief into a product PRD).

Use `"abandoned"` when the change is stopped without delivery; set `run-state` `phase` to `stopped` with `stopped_reason` when useful.

## Feature and contract accumulation

| Artifact | Across changes |
|----------|----------------|
| `requirements/**/*.feature` | Create or **update**; new Scenarios for the active Brief’s `in_scope`. Destructive edits to existing Scenarios are breaking—surface in Brief / critique. |
| OpenAPI / GraphQL / OCL / formal / derived tests | `apply-*` add/update; do not break unrelated surfaces. |

Additional Scenarios belong to the **active** change’s Brief and WorkPlan items—not to a separate “requirements set” model.

## Legacy migration

Repos that still have only `.solidsdd/change-brief.json` (flat):

1. On the next `solidsdd-intake` / `solidsdd-brief` / `solidsdd-run` that needs a Brief path, derive a meaningful `change_id` (from existing goal/summary or user input).
2. Create `.solidsdd/changes/<change_id>/`, move the Brief there, add `change_id` to the JSON, write `status.json` (`active` if work continues, else `done`), write `active-change.json`.
3. If `change-context.md` is missing, run `solidsdd-intake` (or write a context doc from known Brief + repo stack) before continuing new work.
4. Move any ad-hoc WorkPlan / critique JSON for that change into the same directory when identifiable.
5. **Delete** the flat `.solidsdd/change-brief.json` so there is a single SoT.

Do not write a deprecated mirror of the Brief at the flat path.

## Example: second change on arithmetic-api

After `initial-calculator` is `done`, a follow-up such as operation history would:

1. Run `solidsdd-context` (existing Features / OpenAPI / OCL visible).
2. Run `solidsdd-intake` with a new id (e.g. `add-operation-history`) documenting demand, NFRs, and tech choices for that delta.
3. Run `solidsdd-brief` whose `in_scope` is only history; assume calculator + memory behavior remains.
4. Decompose → loops that **update** contracts and Features without rewriting unrelated Scenarios.

See `examples/arithmetic-api/.solidsdd/` for the `initial-calculator` layout.
