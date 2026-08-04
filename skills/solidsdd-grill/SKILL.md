---
name: solidsdd-grill
description: >-
  Conditional structured interview before solidsdd-intake when framing is
  ambiguous. Asks one question at a time with options, pros/cons, and a
  recommendation; persists answers in clarifications/open.json. Skip when the
  user instruction already settled framing. When called from solidsdd-run, run
  as an explicit Task subagent.
license: MIT
---

# solidsdd.grill

## Execution

**subagent required** when invoked from `solidsdd.run`. Parent must use Task and must not thin or invent answers inline. Solo user invocation may run in the current agent.

## Purpose

Reduce silent `agent_default` framing by **grilling** unsettled decisions (Intent Storming / Grill Me style) **before** Change Context is finalized. Not a living product interview loop — change-scoped only.

## References

- [clarifications.md](references/clarifications.md) — **queue rules (required)**
- [clarifications.schema.json](references/clarifications.schema.json)
- [change-context.md](references/change-context.md) — Means vs tech; gate triggers
- [human-gates.md](references/human-gates.md)
- [working-language.md](references/working-language.md)
- [change-lifecycle.md](references/change-lifecycle.md)

## When to run (conditional)

Run Grill when **any** of:

- User explicitly asks to grill / interview / clarify intent first
- Initial instruction leaves material tech or Means undecided (likely heavy `agent_default`)
- Multiple blocking open questions are already visible
- Parent / `solidsdd-next` recommends `grill`

**Skip** when the user’s initial instruction already settled demand, NFRs, and tech (same rule as Change Context gate: do not invent ceremony).

## Constraints

- Ask **one** question per turn (or per Task return that expects a human answer)
- Prefer 2–4 options, pros/cons, and a **recommended** choice with evidence
- Persist every question/answer to `clarifications/open.json` — do not rely on chat alone
- Do **not** write ChangeBrief, WorkPlan, contracts, or implementation
- Do **not** invent a conflicting `change_id`; create lifecycle paths only if intake has not run and a provisional id is required (prefer parent-supplied `change_id`)
- Working language for prose: [working-language.md](references/working-language.md)

## Steps

1. Read user request + `solidsdd-context` summary + optional `knowledge-consult.md`.
2. Decide whether Grill is needed (see above). If skip → return `{ "skipped": true, "reason": "…" }` and do not create empty ceremony.
3. Ensure `.solidsdd/changes/<change_id>/` exists (caller may create via intake first; if Grill runs first, create change dir + `status.json` `active` + `clarifications/` only — leave Context to intake).
4. Initialize or load `clarifications/open.json` validating against [clarifications.schema.json](references/clarifications.schema.json).
5. Build an open-question backlog (Means before one-off tech when both are open). For each question until stop:
   - Present: current understanding, why it matters, **one** question, options, pros/cons, recommendation, evidence, what becomes fixed
   - On answer: set item `status: resolved`, `decision`, `rationale`, `maturity: confirmed` (or `hypothesized` if still tentative)
   - Stop when: no blocking opens remain, user says stop, or packet/Context is ready for intake
6. Set `human_gate.required: true` while any `blocking` item is `open`; otherwise `false`.
7. Align unresolved items with upcoming Context §7 / gate `decisions_to_confirm`.
8. Return path to `clarifications/open.json`, remaining open ids, and whether intake may proceed.

## Output

- Path to `.solidsdd/changes/<change_id>/clarifications/open.json`
- `skipped` or list of resolved / still-open clarification ids
- Explicit signal: **ready for `solidsdd-intake`** or **stopped for human answers**
