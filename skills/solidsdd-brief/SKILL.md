---
name: solidsdd-brief
description: >-
  Produce a ChangeBrief for one change: change_id, goal, in/out of scope,
  assumptions, constraints, and success criteria. Return point when later
  judgment is ambiguous. When called from solidsdd-run, must run as an explicit
  Task subagent. Does not emit WorkPlan, ApplicationPlan, or contracts.
license: MIT
---

# solidsdd.brief

## Execution

**subagent required** when invoked from `solidsdd.run` (or any outer orchestrator). Parent must use Task and must not thin or rewrite the returned ChangeBrief inline. Solo user invocation may run in the current agent.

## Purpose

Emit a `ChangeBrief` so later skills share an explicit premise for what this change includes and excludes. Additional requirements start a **new** change (new `change_id`), not an edit of a prior Brief into a living PRD.

## References

- [change-brief.schema.json](references/change-brief.schema.json)
- [active-change.schema.json](references/active-change.schema.json)
- [change-status.schema.json](references/change-status.schema.json)
- [change-brief.md](references/change-brief.md) — **role and required fields (required)**
- [change-lifecycle.md](references/change-lifecycle.md) — **paths, change_id, next-change flow (required)**
- [human-gates.md](references/human-gates.md)

## Constraints

- Produce the ChangeBrief (and lifecycle pointer/status files) only
- Default paths: `.solidsdd/changes/<change_id>/change-brief.json`, `status.json`, and `.solidsdd/active-change.json`
- No Gherkin Feature edits, WorkPlan, ApplicationPlan, OpenAPI / OCL / formal / implementation / test edits
- Do **not** choose contract kinds or densities (that is `solidsdd-judge`)
- Do **not** slice into WorkPlan items (that is `solidsdd-decompose`)
- `change_id`, `in_scope`, and `out_of_scope` must be present; scope lists must be concrete
- Prefer structured fields over essay-length PRD prose
- Do **not** write a flat `.solidsdd/change-brief.json` (migrate legacy per [change-lifecycle.md](references/change-lifecycle.md))

## Steps

1. Read change request / user intent and context (`solidsdd-context` output if available).
2. If only legacy `.solidsdd/change-brief.json` exists, migrate it first per [change-lifecycle.md](references/change-lifecycle.md).
3. Decide `change_id`: use caller-supplied id when valid; otherwise derive a meaningful kebab-case name from goal/summary; on collision under `changes/`, append `-2`, `-3`, …
4. If another change is currently `active` and this is a **new** change, set the previous `status.json` to `done` or `abandoned` as appropriate before switching.
5. Apply rules in [change-brief.md](references/change-brief.md) and [change-lifecycle.md](references/change-lifecycle.md). Put only this change’s delta in `in_scope`.
6. Fill `change_id`, `goal`, `in_scope`, `out_of_scope`, `success_criteria` (plus optional background / assumptions / constraints / open_questions).
7. Apply gate rules in [human-gates.md](references/human-gates.md) when ambiguity or blocking open questions warrant a gate; set `confidence` accordingly.
8. Validate against [change-brief.schema.json](references/change-brief.schema.json).
9. Create `.solidsdd/changes/<change_id>/` and write:
   - `change-brief.json`
   - `status.json` with `"status": "active"` ([change-status.schema.json](references/change-status.schema.json))
   - `.solidsdd/active-change.json` pointing at this `change_id` ([active-change.schema.json](references/active-change.schema.json))

## Output

JSON conforming to the ChangeBrief schema, plus a one-paragraph summary and the resolved paths. Return these artifacts to the parent unchanged in meaning.
