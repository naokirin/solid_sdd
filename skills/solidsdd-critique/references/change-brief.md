# Change brief (solidsdd.brief)

`solidsdd-brief` turns a raw change request into a **ChangeBrief**: structured scope for one change. It is the **return point** when later phases (decompose, judge, critique) are unsure whether something is in scope.

## Why

Without a brief, the loop only has chat prose or already-sliced Scenarios. Agents invent or drop non-goals; density judgment has no shared premise.

## Role split (required)

| Layer | Artifact | Answers |
|-------|----------|---------|
| Stack facts | `solidsdd-context` summary | What exists in the repo? |
| Framing / rationale | `change-context.md` (`solidsdd-intake`) | Demand, NFRs, tech selection, judgments |
| **Change premise** | **ChangeBrief** | What are we doing / not doing / assuming? |
| Acceptance structure | Gherkin (property-level Scenarios) | Which properties must hold? |
| Loop authority | OpenAPI / OCL / formal | How do we check implementation? |

ChangeBrief is **not** a living product PRD and **not** a substitute for OCL/OpenAPI. It is authority for **this change’s scope** (history OK; perpetual editorial ownership is not the goal). Additional requirements start a **new** change—see [change-lifecycle.md](change-lifecycle.md). Read `change-context.md` before inventing scope that contradicts recorded tech/NFR judgments.

## Default artifact path

| Artifact | Path |
|----------|------|
| Active pointer | `.solidsdd/active-change.json` |
| Change Context | `.solidsdd/changes/<change_id>/change-context.md` |
| ChangeBrief JSON | `.solidsdd/changes/<change_id>/change-brief.json` |
| Change status | `.solidsdd/changes/<change_id>/status.json` |

Resolve via the active pointer. Override layout paths via `.solidsdd/config.yaml`. Do not write a flat `.solidsdd/change-brief.json` (legacy only).

`solidsdd-intake` creates `change_id` and `change-context.md`. `solidsdd-brief` writes `change-brief.json` for the **active** change (must not invent a conflicting id).

## Required content

- `change_id` — meaningful kebab-case id; must match the directory name under `changes/`
- `goal` — outcome for this change
- `in_scope` / `out_of_scope` / `success_criteria` — arrays of **`{ "id", "text" }`** objects (not bare strings). Prefer ids `R1…` (in scope), `X1…` (out of scope), `SC1…` (success). Ids must be unique across the Brief. `out_of_scope` must not be empty hand-waving; name concrete non-goals
- Avoid a "(for now, only X)" / "(当面はXのみ)" parenthetical inside an `out_of_scope` entry — it reads as two different claims at once (X itself is also excluded vs. X is the assumed in-scope default and only alternatives to X are excluded) and downstream skills (decompose, Gherkin, contracts) cannot tell which was meant, so X ends up promised nowhere and delivered nowhere. If X is a real guaranteed default behavior, give it its own `in_scope` / `success_criteria` id so it gets a Gherkin Scenario and a contract. If it is not actually guaranteed, exclude the broader policy without naming an implied default at all (e.g. "job scheduling/priority policy (processing order across jobs is unspecified/not guaranteed)" rather than "(for now, FIFO only)")
- Prefer short `text` values over essays
- JSON **keys** stay English; string **values** (`text`, `goal`, …) use the project **working language** ([working-language.md](working-language.md))

**Breaking:** older Briefs with `string[]` scope lists are invalid. Migrate to `{ id, text }` objects.

Optional: `background`, `assumptions`, `constraints`, `open_questions`, `confidence`, `human_gate`.

When continuing an existing product line, put **only this change’s delta** in `in_scope`; use `assumptions` / `constraints` for “keep existing behavior” rather than re-listing the whole product.

## Coverage ids

Downstream WorkPlan items and Gherkin Scenarios reference these ids via `covers` / Scenario tags (`@R1`). Mechanical coverage is checked by `scripts/solidsdd-lint.sh` before critique. Critique judges whether coverage is *adequate*, not whether ids exist.

Optional: author `text` fields using **EARS** patterns ([ears-requirements.md](ears-requirements.md))—especially unwanted / state-driven—while keeping Gherkin as acceptance.

## When later skills must re-read the brief

- Prefer re-reading `change-context.md` when tech/NFR rationale is needed; Brief stays the scope checklist
- `solidsdd-decompose` — each item must `covers` Brief `in_scope` / `success_criteria` ids; must not cover `out_of_scope` ids; Scenario tags must match
- `solidsdd-judge` — density / skip / defer when unsure: check brief **and** Change Context §5 before inventing stack/adapters; set target `covers` to WorkPlan item ids when known
- `solidsdd-critique` — run lint first; scope drift / missing id coverage → fail (often already lint-imported); framing gaps → `solidsdd-intake`
- Ambiguous verify / gate — orchestrator may stop and point at brief `open_questions` / `human_gate` or Change Context §7

## Critique expectations

`subject: change_brief` — major when in/out of scope are missing or contradictory, success criteria are unverifiable slogans only, or open questions that block slicing are unmarked (no gate / low confidence). Bare-string scope lists are schema/lint blockers. See [adversarial-critique.md](adversarial-critique.md).
