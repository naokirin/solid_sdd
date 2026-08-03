---
name: solidsdd-brief
description: >-
  Produce a ChangeBrief for one change: change_id, goal, in/out of scope,
  assumptions, constraints, and success criteria. Return point when later
  judgment is ambiguous. Expects Change Context from solidsdd-intake. When
  called from solidsdd-run, must run as an explicit Task subagent. Does not
  emit WorkPlan, ApplicationPlan, or contracts.
license: MIT
---

# solidsdd.brief

## Execution

**subagent required** when invoked from `solidsdd.run` (or any outer orchestrator). Parent must use Task and must not thin or rewrite the returned ChangeBrief inline. Solo user invocation may run in the current agent.

## Purpose

Emit a `ChangeBrief` so later skills share an explicit premise for what this change includes and excludes. Additional requirements start a **new** change (new `change_id` via `solidsdd-intake`), not an edit of a prior Brief into a living PRD.

## References

- [change-brief.schema.json](references/change-brief.schema.json)
- [active-change.schema.json](references/active-change.schema.json)
- [change-status.schema.json](references/change-status.schema.json)
- [change-brief.md](references/change-brief.md) — **role and required fields (required)**
- [working-language.md](references/working-language.md) — string values language
- [change-context.md](references/change-context.md) — framing doc from intake
- [change-context-gate.schema.json](references/change-context-gate.schema.json)
- [change-lifecycle.md](references/change-lifecycle.md) — **paths, change_id, next-change flow (required)**
- [human-gates.md](references/human-gates.md)

## Constraints

- Produce the ChangeBrief only (lifecycle pointer/status already created by `solidsdd-intake` when following `solidsdd-run`)
- Default path: `.solidsdd/changes/<change_id>/change-brief.json` for the **active** `change_id`
- No Gherkin Feature edits, WorkPlan, ApplicationPlan, OpenAPI / OCL / formal / implementation / test edits
- Do **not** choose contract kinds or densities (that is `solidsdd-judge`)
- Do **not** slice into WorkPlan items (that is `solidsdd-decompose`)
- Do **not** overwrite `change-context.md` (that is `solidsdd-intake`)
- `change_id`, `in_scope`, and `out_of_scope` must be present; scope lists must be concrete **`{ id, text }` objects** (not bare strings); prefer `R*` / `X*` / `SC*` ids
- Prefer structured fields over essay-length PRD prose
- JSON keys English; string values in the **working language** ([working-language.md](references/working-language.md); prefer Context §6 / project rule)
- Do **not** write a flat `.solidsdd/change-brief.json` (migrate legacy per [change-lifecycle.md](references/change-lifecycle.md))

## Steps

1. Read change request / user intent, `solidsdd-context` output if available, **Change Context** for the active change (`.solidsdd/changes/<change_id>/change-context.md`), and `knowledge-consult.md` when present. Resolve working language from project rule or Context §6. Existing knowledge policy/decision ids may appear in `assumptions` / `constraints` as citations—do **not** duplicate policy bodies as a second SoT.
2. If only legacy `.solidsdd/change-brief.json` exists, migrate it first per [change-lifecycle.md](references/change-lifecycle.md).
3. Resolve `change_id`:
   - Prefer `.solidsdd/active-change.json` when `change-context.md` exists for that id.
   - If the user invoked **brief alone** and no Change Context exists: run the `solidsdd-intake` procedure first (same solo session), then continue—or stop and ask the parent to run `solidsdd-intake`.
   - Do **not** invent a second `change_id` that diverges from an existing Change Context.
4. Apply rules in [change-brief.md](references/change-brief.md) and [change-lifecycle.md](references/change-lifecycle.md). Put only this change’s delta in `in_scope` as `{ id, text }` (prefer `R1…`). Align `out_of_scope` (`X1…`) / `success_criteria` (`SC1…`) / constraints with Change Context §§4–6. Ids must be unique across the Brief.
5. Fill `change_id`, `goal`, `in_scope`, `out_of_scope`, `success_criteria` (plus optional background / assumptions / constraints / open_questions) in the working language.
6. Apply gate rules in [human-gates.md](references/human-gates.md) when ambiguity or blocking open questions warrant a gate; set `confidence` accordingly. Do **not** start Brief under `solidsdd-run` while Change Context gate is still `required: true` (orchestrator stops first).
7. Validate against [change-brief.schema.json](references/change-brief.schema.json).
8. Write `.solidsdd/changes/<change_id>/change-brief.json`. Ensure `status.json` remains `active` and `active-change.json` points here (create only if missing after intake).

## Output

JSON conforming to the ChangeBrief schema, plus a one-paragraph summary and the resolved paths. Return these artifacts to the parent unchanged in meaning.
