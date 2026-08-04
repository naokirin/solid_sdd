---
name: solidsdd-knowledge
description: >-
  Build and consume durable cross-cutting knowledge as part of solid_sdd SDD
  work. mode=consult loads existing knowledge/ into framing; mode=harvest
  proposes policy/concept/decision/lesson candidates after integration verify
  (human-gated; never auto-promote). When called from solidsdd-run, must run
  as an explicit Task subagent. Uses tools/solidsdd-kg when available.
license: MIT
---

# solidsdd.knowledge

## Execution

**subagent required** when invoked from `solidsdd.run` (or any outer orchestrator). Parent must use Task and must not thin or rewrite `knowledge-consult.md` / `knowledge-harvest.json` inline. Solo user invocation may run in the current agent (including harvest-only after a finished change).

## Purpose

Close the SDD gap where durable knowledge is buried inside volatile requirements: **consult** existing `knowledge/` before framing, and **harvest** durable nodes at change end under a **human gate**. ChangeBrief / Gherkin remain requirement SoT; `knowledge/` is not a living PRD.

## References

- [knowledge.md](references/knowledge.md) — **modes, what to harvest, apply rules (required)**
- [knowledge-harvest.schema.json](references/knowledge-harvest.schema.json)
- [change-lifecycle.md](references/change-lifecycle.md)
- [human-gates.md](references/human-gates.md)
- [gate-approval.schema.json](references/gate-approval.schema.json)
- [working-language.md](references/working-language.md)

## Parameters

| Name | Required | Default | Meaning |
|------|----------|---------|---------|
| `mode` | yes | — | `consult` or `harvest` |
| `change_id` | no | active change | Target change directory |
| `apply` | no | false | After harvest gate approval only: write approved candidates |

## Constraints

- Do **not** auto-write `knowledge/` without `gate-approval.json` `scope: knowledge_harvest` and `decision` `approve` / `approve_partial`
- Do **not** move Brief `in_scope` / Scenarios wholesale into knowledge
- Do **not** edit OpenAPI / OCL / Features / implementation as part of this skill
- Prefer `scripts/solidsdd-kg.sh` when present; if Go/CLI unavailable, still emit consult/harvest artifacts from filesystem reading of `knowledge/**` and note the tooling gap
- Working language for prose fields: project rule / Context §6 ([working-language.md](references/working-language.md))

## Steps — `mode: consult`

1. Resolve `change_id` from caller or `.solidsdd/active-change.json` (may be unset before intake—then write a draft under `/tmp` or wait until intake created the change dir; prefer writing under the change dir when it exists).
2. Note whether `knowledge/` and `.solidsdd/kg/` exist (`solidsdd-context` may already have flagged this).
3. When CLI available: `scripts/solidsdd-kg.sh build --root .` then, as useful:
   - `scope <dotted>` for org/product scopes from Context / project
   - `context <node-id> --budget 8k` for top policies/decisions (e.g. from `knowledge/policies`, `knowledge/decisions`)
   - `impact` on relevant ids when Brief R* already exist (`<change_id>/R*`)
4. Write `.solidsdd/changes/<change_id>/knowledge-consult.md` with:
   - Applicable policies / concepts / decisions (or **None**)
   - Suggested ids for Brief `assumptions` / `constraints` citations
   - Gaps (missing `.solidsdd/kg/`, CLI unavailable)
5. Return path + short summary for intake/brief.

## Steps — `mode: harvest`

1. Resolve active `change_id`. Require integration verify success (or explicit user harvest-only request).
2. Read Change Context, Brief, WorkPlan (optional critiques). When CLI available: `scripts/solidsdd-kg.sh promote suggest --root . --json`.
3. Propose only **durable and non-trivial** candidates per [knowledge.md](references/knowledge.md) (universality + non-obvious choice/boundary + low churn). Fill `knowledge-harvest.json` validating against [knowledge-harvest.schema.json](references/knowledge-harvest.schema.json).
4. Set `human_gate.required: true` when `candidates.length >= 1` (or durable knowledge needs human framing). Empty list → `required: false`.
5. Set `run-state.json` `phase` to `knowledge_harvest` when called from run.
6. **Stop for gate** when required: do not apply. Parent obtains `gate-approval.json` (`scope: knowledge_harvest`).
7. When caller passes `apply: true` **and** matching approval exists:
   - For each `approved` / allowed candidate: `scripts/solidsdd-kg.sh promote apply --approve --type <type> --id … --title … --scope …` (and/or hand-write Markdown under `knowledge/<plural>/`)
   - Add downstream links: knowledge frontmatter and/or `.solidsdd/kg/links.yaml` from `<change_id>/R*` → knowledge id (`derives_from` / `rationale` as appropriate)
   - Mark candidates `applied` / `skipped` / `rejected`; run `scripts/solidsdd-kg.sh check --root .`
8. Return harvest path, gate status, and apply results.

## Output

### consult

- Path to `knowledge-consult.md`
- One-paragraph summary of applicable knowledge (or none)

### harvest

- Path to `knowledge-harvest.json`
- Whether `human_gate.required`
- If applied: created paths + `check` summary
