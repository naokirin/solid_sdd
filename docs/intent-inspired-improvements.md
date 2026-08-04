# Intent-inspired improvements (1–6)

**Status:** I1–I4 implemented (2026-08-04)  
**Date:** 2026-08-04  
**Context:** Lessons from [Intent CLI / IDD](https://zenn.dev/jtechjapan_pub/articles/intent-cli-concept) ([intent-system](https://github.com/J-Tech-Japan/intent-system)) applied to solid_sdd **without** turning Change Context / Brief into a living intent-tree PRD.

Related: [vision.md](vision.md), [coexistence.md](coexistence.md), [hardening-plan.md](hardening-plan.md), [roadmap.md](roadmap.md), [schema-evolution.md](schema-evolution.md), [POL-KG-PERSISTENCE](../knowledge/policies/POL-KG-PERSISTENCE.md).

## Scope

| ID | Content | Status |
|----|---------|--------|
| 1 | Knowledge / framing maturity (`hypothesized` → `confirmed` → `canonical`) | done (I1) |
| 2 | Conditional Grill (structured interview before intake) | done (I2) |
| 3 | Means (decision criteria) vs tech selection | done (I1) |
| 4 | Persistent clarifications queue + resume | done (I2) |
| 5 | Optional facets + `knowledge_consistency` critique | done (I3) |
| 6 | Deterministic `next` + declared-step validate (no state writes) | done (I4) |

**Out of scope:** GitHub four-thread / Issue-contract autonomous loops; Mission/Vision as required toolkit layers; intent-tree as project SoT; `solidsdd-next` writing `run-state.phase`.

## Design locks

### Maturity ≠ lifecycle `status`

KG `status` remains `draft` / `active` / `deprecated` / `contested`. Epistemic certainty uses additive frontmatter:

- `maturity`: `hypothesized` | `confirmed` | `canonical`
- Missing on existing nodes → treat as `confirmed`
- Human-gated harvest apply → default `canonical`
- Unconfirmed Grill inferences → `hypothesized` (lower consult rank; may cite as Brief assumptions)

### Means vs tech

- Change Context **§5** = stack choices for this change
- Change Context **§6** Means-like judgments + `knowledge/` = reusable decision criteria
- Do not harvest one-off stack picks into `knowledge/`

### Facets (optional)

`facets`: `vocabulary` | `invariant` | `decider` | `acceptance-property` (array). Complements `type`; used for consult sectioning and lint of unknown values.

### Clarifications

`.solidsdd/changes/<change_id>/clarifications/open.json` — durable Q/A with optional recommendation + evidence. Blocking open items integrate with human gates / `run-state` stop-resume.

### Grill

`solidsdd-grill` is **conditional** (ambiguous framing, heavy `agent_default`, or user asks). Clear instructions → skip. One question at a time; answers land in clarifications; then intake.

### Next (depth B)

`scripts/solidsdd-next`: `next` and `validate --declared …` only. Parent still writes `run-state.json`. Deviations → `isolation_notes`.

## Implementation phases

| Phase | Delivers | Status |
|-------|----------|--------|
| **Doc lock** | This document + roadmap / feedback-tuning / schema-evolution links | done |
| **I1** | `maturity` + Means rules + harvest/promote/context ranking | done |
| **I2** | clarifications schema + `solidsdd-grill` + run/intake wiring | done |
| **I3** | `facets` + `knowledge_consistency` + lint/context | done |
| **I4** | `solidsdd-next` (`next` / `validate`) + run references | done |

## Acceptance (stream)

1. Hypothesized knowledge ranks below canonical in consult; approved harvest may become canonical
2. Ambiguous framing can Grill → clarify → intake; clear instructions can skip Grill
3. Means vs tech rules appear in Context / POL; harvest critique can reject one-off stack / living-PRD leakage
4. Blocking clarifications resume from disk
5. `knowledge_consistency` is a defined critique subject and runnable from `solidsdd-run`
6. `solidsdd-next next` returns a legal next action; `validate` rejects illegal declared steps without mutating state
