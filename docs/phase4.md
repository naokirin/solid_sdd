# Phase 4 — Operations and ecosystem

Phase 4 packages solid_sdd for day-to-day use alongside other SDD tools and makes first-time adoption checklist-driven.

## Delivered in this slice

| Area | Doc |
|------|-----|
| Coexistence with other SDD tools | [coexistence.md](coexistence.md) |
| Adoption checklist (expanded) | [install.md](install.md) §Adoption checklist |
| Quick-start template layout | [project-template.md](project-template.md) |
| Eval-corpus rule tuning (Pass 1) | [feedback-tuning.md](feedback-tuning.md) |
| Adversarial critique skill (SpecKit-style analyze gate) | `solidsdd-critique` + [../reference-src/adversarial-critique.md](../reference-src/adversarial-critique.md) |
| Outer run + work decomposition | `solidsdd-run` / `solidsdd-decompose` + [../reference-src/work-decomposition.md](../reference-src/work-decomposition.md) / [../schemas/work-plan.schema.json](../schemas/work-plan.schema.json) |
| ChangeBrief scope phase | `solidsdd-brief` + [../reference-src/change-brief.md](../reference-src/change-brief.md) / [../schemas/change-brief.schema.json](../schemas/change-brief.schema.json) |
| Change Context framing | `solidsdd-intake` + [../reference-src/change-context.md](../reference-src/change-context.md) (+ optional gate) |
| Gherkin requirement intake | [../reference-src/gherkin-requirements.md](../reference-src/gherkin-requirements.md) (property-level) |
| Iterative change layout | [../reference-src/change-lifecycle.md](../reference-src/change-lifecycle.md) + `active-change` / per-`change_id` dirs |

## Still open

- External production-project feedback → further threshold tuning ([feedback-tuning.md](feedback-tuning.md) intake log)
- `gh skill publish` for [naokirin/solid_sdd](https://github.com/naokirin/solid_sdd) + template repository
- Optional language-native DbC (opt-in design; still deferred)
- Optional human-readable projection skills (Markdown / HTML from contracts) — readability without changing loop authority

## Follow-on: Phase 5 Hardening

Mechanical assurance for requirements quality (ID traceability, pre-critique lint, run-state persistence, structured NFRs, critique eval corpus, CI) is tracked separately in [hardening-plan.md](hardening-plan.md) and [roadmap.md](roadmap.md) §Phase 5.

## Success criteria (Phase 4)

1. A new team can install skills and pass the checklist without reading every architecture doc.
2. Coexistence guidance states what solid_sdd owns vs leaves to Kiro-like NL SDD loops.
3. Template layout matches default contract paths used by skills.
4. Additional requirements are modeled as a new meaningful `change_id` with accumulated Features/contracts (not a living Brief PRD).
