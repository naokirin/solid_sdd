---
name: solidsdd-report
description: >-
  Emit a human-readable Change Report (Markdown by default, optional HTML) for
  one change: demand, functional and non-functional requirements, technology
  selection, and design so far. Missing phases are marked not performed
  (未実施). Use when the user asks for a readable summary, review document, or
  solidsdd.report / solidsdd-report. Manual only—not part of solidsdd-run.
license: MIT
---

# solidsdd.report

## Execution

**Manual / orchestrator** — run in the current agent when the user asks. Not invoked automatically by `solidsdd-run` or `solidsdd-loop`. After intake, Brief, or design phases, those flows may **suggest** this skill for human review.

## Purpose

Turn existing machine-oriented artifacts into a single human-readable report for **one** `change_id` (active change by default, or a caller-supplied id). Do not invent content for phases that have not run yet—mark them **未実施** / **Not performed**.

## References

- [change-report.md](references/change-report.md) — **sections, presence rules, Markdown/HTML (required)**
- [change-lifecycle.md](references/change-lifecycle.md) — paths and `change_id`
- [contract-layout.md](references/contract-layout.md) — Feature / OpenAPI / OCL / formal paths
- [change-context.md](references/change-context.md) — framing sections to project
- [change-brief.md](references/change-brief.md) — scope fields
- [gherkin-requirements.md](references/gherkin-requirements.md) — Feature / Scenario role

## Parameters

| Name | Required | Default | Meaning |
|------|----------|---------|---------|
| `change_id` | no | active change | Target change directory |
| `format` | no | `markdown` | `markdown`, `html`, or both |
| `language` | no | infer from sources | e.g. `ja` / `en` |

## Constraints

- Write only `.solidsdd/changes/<change_id>/report.md` and/or `report.html`
- Do **not** edit Change Context, Brief, WorkPlan, Features, OpenAPI, OCL, formal, tests, or implementation
- Do **not** fabricate missing requirements, NFRs, tech choices, or design
- Markdown: contract bodies are **links** only (plus natural-language summary)
- HTML: calm navy/black dark theme with **white body text**; Raw panels use generation-time highlighting (Pygments `github-dark` + muted token overrides; avoid loud yellow/chartreuse)
- Report language matches sources unless `language` is set

## Steps

1. Resolve `change_id` per [change-report.md](references/change-report.md) (caller override → `active-change.json` → stop if unknown).
2. Decide report language (override or infer).
3. Collect artifacts under `.solidsdd/changes/<change_id>/` and project contract paths ([contract-layout.md](references/contract-layout.md)):
   - `change-context.md`, `change-brief.json`, `work-plan.json`, status
   - Features tied to this change (Brief / WorkPlan / Context §8)
   - ApplicationPlan JSON (discovery rules in change-report)
   - OpenAPI / GraphQL / OCL / formal when present
4. For each required section, mark **Present** or **Not performed** and fill only from real sources.
5. Write `report.md` (unless the caller asked for HTML only).
6. If `format` includes `html`, write self-contained `report.html` with summary + raw tabs/collapsibles for contracts and plan JSON.
7. Return paths written, language used, and a one-paragraph status overview (which sections are present vs not performed).

## Output

- Path(s) to `report.md` / `report.html`
- `change_id` and language
- Short overview of Present vs Not performed sections
