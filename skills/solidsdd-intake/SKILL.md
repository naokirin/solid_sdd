---
name: solidsdd-intake
description: >-
  Produce a Change Context Markdown for one change: demand, non-functional
  requirements, technology selection, and key judgments (natural language with
  fixed headings). Writes change-context-gate.json for optional human approval
  of important framing decisions. Creates change_id and lifecycle paths. When
  called from solidsdd-run, must run as an explicit Task subagent. Does not emit
  ChangeBrief, WorkPlan, or contracts.
license: MIT
---

# solidsdd.intake

## Execution

**subagent required** when invoked from `solidsdd.run` (or any outer orchestrator). Parent must use Task and must not thin or rewrite the returned Change Context inline. Solo user invocation may run in the current agent.

## Purpose

Emit `change-context.md` so later skills (and humans) can see **why** NFRs and technologies were set—not only the scoped Brief / Gherkin outcomes. Starts the change lifecycle (`change_id`, directory, active pointer). Optionally signals a **human gate** when framing decisions need approval (not when the initial instruction already made them clear).

## References

- [change-context.md](references/change-context.md) — **fixed headings, gate rules (required)**
- [working-language.md](references/working-language.md) — **prose language (required)**
- [change-context-gate.schema.json](references/change-context-gate.schema.json)
- [change-lifecycle.md](references/change-lifecycle.md) — **paths, change_id, next-change flow (required)**
- [active-change.schema.json](references/active-change.schema.json)
- [change-status.schema.json](references/change-status.schema.json)
- [human-gates.md](references/human-gates.md)

## Constraints

- Produce Change Context + gate JSON (+ lifecycle pointer/status) only
- Default paths: `.solidsdd/changes/<change_id>/change-context.md` and `change-context-gate.json`
- Use **exactly** the required top-level headings in [change-context.md](references/change-context.md) (English headings; body in working language)
- Write section bodies in the resolved **working language** ([working-language.md](references/working-language.md))
- No ChangeBrief, Gherkin, WorkPlan, ApplicationPlan, OpenAPI / OCL / formal / implementation / test edits
- Do **not** choose contract density (that is `solidsdd-judge`); do record intended stack / API style in §5
- Do **not** slice into WorkPlan items (that is `solidsdd-decompose`)
- Prefer concise bullets; natural language OK; not an essay PRD
- **Do not** set `human_gate.required: true` when the user’s initial instruction already settled the decisions (see gate rules)

## Steps

1. Read change request / user intent and context (`solidsdd-context` output if available).
2. Resolve **working language** per [working-language.md](references/working-language.md) (project rule → user request → `en`).
3. If only legacy flat Brief exists, migrate per [change-lifecycle.md](references/change-lifecycle.md) first when paths collide; otherwise proceed.
4. Decide `change_id`: use caller-supplied id when valid; otherwise derive meaningful kebab-case from goal; on collision under `changes/`, append `-2`, `-3`, …
5. If another change is `active` and this is a **new** change, set the previous `status.json` to `done` or `abandoned` as appropriate before switching.
6. Apply section rules in [change-context.md](references/change-context.md). Especially:
   - §4 Non-functional requirements — each with requirement / rationale / verification-or-deferred (or explicit N/A + why)
   - §5 Technology selection — each decision with alternatives + rationale + source (`user` / `repo_existing` / `agent_default`)
   - §6 Key judgments — include `Working language: <tag> (from project rule|user request|default)` 
7. Decide Change Context gate per [change-context.md](references/change-context.md) §Human gate and [human-gates.md](references/human-gates.md):
   - Default **false** when instructions were clear or stack is inherited without conflict
   - **true** for material `agent_default` tech, stack conflicts, new security/money NFR, or blocking §7 questions
   - When true, list concrete `decisions_to_confirm`
8. Validate gate JSON against [change-context-gate.schema.json](references/change-context-gate.schema.json).
9. Create `.solidsdd/changes/<change_id>/` and write:
   - `change-context.md`
   - `change-context-gate.json`
   - `status.json` with `"status": "active"`
   - `.solidsdd/active-change.json` pointing at this `change_id`

## Output

The Markdown path, gate path, `change_id`, working language used, whether `human_gate.required`, and a one-paragraph summary. Return these to the parent unchanged in meaning.
