---
name: solidsdd-brief
description: >-
  Produce a ChangeBrief for one change: goal, in/out of scope, assumptions,
  constraints, and success criteria. Return point when later judgment is
  ambiguous. When called from solidsdd-run, must run as an explicit Task
  subagent. Does not emit WorkPlan, ApplicationPlan, or contracts.
license: MIT
---

# solidsdd.brief

## Execution

**subagent required** when invoked from `solidsdd.run` (or any outer orchestrator). Parent must use Task and must not thin or rewrite the returned ChangeBrief inline. Solo user invocation may run in the current agent.

## Purpose

Emit a `ChangeBrief` so later skills share an explicit premise for what this change includes and excludes.

## References

- [change-brief.schema.json](references/change-brief.schema.json)
- [change-brief.md](references/change-brief.md) — **role and required fields (required)**
- [human-gates.md](references/human-gates.md)

## Constraints

- Produce the ChangeBrief only (default path `.solidsdd/change-brief.json`)
- No Gherkin Feature edits, WorkPlan, ApplicationPlan, OpenAPI / OCL / formal / implementation / test edits
- Do **not** choose contract kinds or densities (that is `solidsdd-judge`)
- Do **not** slice into WorkPlan items (that is `solidsdd-decompose`)
- `in_scope` and `out_of_scope` must both be non-empty concrete lists
- Prefer structured fields over essay-length PRD prose

## Steps

1. Read change request / user intent and context (`solidsdd-context` output if available).
2. Apply rules in [change-brief.md](references/change-brief.md).
3. Fill `goal`, `in_scope`, `out_of_scope`, `success_criteria` (plus optional background / assumptions / constraints / open_questions).
4. Apply gate rules in [human-gates.md](references/human-gates.md) when ambiguity or blocking open questions warrant a gate; set `confidence` accordingly.
5. Validate against [change-brief.schema.json](references/change-brief.schema.json).
6. Write JSON to `.solidsdd/change-brief.json` (or project override).

## Output

JSON conforming to the ChangeBrief schema, plus a one-paragraph summary. Return these artifacts to the parent unchanged in meaning.
