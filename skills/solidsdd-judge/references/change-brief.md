# Change brief (solidsdd.brief)

`solidsdd-brief` turns a raw change request into a **ChangeBrief**: structured scope for one change. It is the **return point** when later phases (decompose, judge, critique) are unsure whether something is in scope.

## Why

Without a brief, the loop only has chat prose or already-sliced Scenarios. Agents invent or drop non-goals; density judgment has no shared premise.

## Role split (required)

| Layer | Artifact | Answers |
|-------|----------|---------|
| Stack facts | `solidsdd-context` summary | What exists in the repo? |
| **Change premise** | **ChangeBrief** | What are we doing / not doing / assuming? |
| Acceptance structure | Gherkin (property-level Scenarios) | Which properties must hold? |
| Loop authority | OpenAPI / OCL / formal | How do we check implementation? |

ChangeBrief is **not** a living product PRD and **not** a substitute for OCL/OpenAPI. It is authority for **this change’s scope** (history OK; perpetual editorial ownership is not the goal).

## Default artifact path

| Artifact | Path |
|----------|------|
| ChangeBrief JSON | `.solidsdd/change-brief.json` |

Projects may override via project rule.

## Required content

- `goal` — outcome for this change
- `in_scope` / `out_of_scope` — explicit lists (out_of_scope must not be empty hand-waving; name concrete non-goals)
- `success_criteria` — whole-change observable outcomes
- Prefer short bullet strings over essays

Optional: `background`, `assumptions`, `constraints`, `open_questions`, `confidence`, `human_gate`.

## When later skills must re-read the brief

- `solidsdd-decompose` — Scenarios must cover `in_scope` / `success_criteria` and must not pull in `out_of_scope`
- `solidsdd-judge` — density / skip / defer when unsure: check brief before inventing scope
- `solidsdd-critique` — scope drift vs brief → fail with suggested `solidsdd-brief` or `solidsdd-decompose`
- Ambiguous verify / gate — orchestrator may stop and point at brief `open_questions` / `human_gate`

## Critique expectations

`subject: change_brief` — major when in/out of scope are missing or contradictory, success criteria are unverifiable slogans only, or open questions that block slicing are unmarked (no gate / low confidence). See [adversarial-critique.md](adversarial-critique.md).
