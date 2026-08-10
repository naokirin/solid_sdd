# Schema evolution

solid_sdd JSON artifacts use `"version": "1"` as a **const** in each schema. This document is the migration policy so future breaking changes have a path.

## Rules while `version` remains `"1"`

1. **Additive fields preferred** — new optional properties / enum values that do not invalidate existing valid documents.
2. **Hard breaks are allowed only with an explicit milestone** (e.g. ChangeBrief `{ id, text }` in hardening M1) and in-repo example migration in the same change.
3. **Do not** silently reinterpret existing fields; rename via a new field + deprecate note in schema `description` for one release cycle when possible.
4. Document each intentional break in [feedback-tuning.md](feedback-tuning.md) intake log and [hardening-plan.md](hardening-plan.md) / roadmap.

## Moving to `version: "2"`

When additive changes are insufficient:

1. Draft `*.schema.json` with `"const": "2"` (keep v1 schemas as `*-v1.schema.json` or tagged git release for one cycle).
2. Provide a migrator under `scripts/migrate/` (stdin/stdout or `--project-root`) that rewrites `.solidsdd/**` artifacts.
3. Update skills / lint to accept v2; optionally accept v1 read-only with a major lint finding “migrate required”.
4. Migrate all in-repo examples and eval fixtures in the same PR.
5. Cut a release note listing removed/renamed fields.

## Shipped additive fields (v1, intent-inspired stream)

See [intent-inspired-improvements.md](intent-inspired-improvements.md). Prefer optional properties / enum values; do not reinterpret KG lifecycle `status`.

| Artifact / surface | Additive |
|--------------------|----------|
| Knowledge frontmatter | optional `maturity` (`hypothesized` \| `confirmed` \| `canonical`); optional `facets` (`vocabulary` \| `invariant` \| `decider` \| `acceptance-property`) |
| `knowledge-harvest.json` | optional candidate `maturity` / `facets` |
| `clarifications/open.json` | new schema (change-scoped Q/A queue) |
| `run-state.json` `phase` | additive enum value `grill` |
| CritiqueReport `subject` | additive `knowledge_consistency` |
| GateApproval `scope` | additive `clarifications` |
| `run-next` output | new schema for `solidsdd-next` (not a change artifact version bump) |
| KG `derives_from` edge | `to` may include `concept` (requirement → ubiquitous-language link) |

## Current notable breaks (v1 era)

| Date | Artifact | Break |
|------|----------|-------|
| 2026-08-03 | ChangeBrief | `in_scope` / `out_of_scope` / `success_criteria` → `{ id, text }` objects |
| 2026-08-03 | WorkPlan | required `covers`; optional `touches` / `change_id` |
| 2026-08-03 | NFR | new `nfr.json` SoT (Context §4 projection) |
| 2026-08-03 | GateApproval | new `gate-approval.json` (free-text `approver`) |
| 2026-08-03 | CritiqueReport | additive subject `cross_change_consistency` |
