# Knowledge in solid_sdd (consult / harvest)

solid_sdd treats **change-scoped** specs (Change Context, ChangeBrief, Gherkin, contracts) as the loop authority for a change, and **does not** maintain them as everlasting living product docs.

Separately, **cross-cutting knowledge** that should outlive a change—terms, policies, invariants, patterns, ADRs, lessons—lives under `knowledge/` and is indexed by `tools/solidsdd-kg` (`.solidsdd/kg/`). That knowledge is built **as part of the SDD run**, not as a side tool.

## Modes (`solidsdd-knowledge`)

| Mode | When | Artifact |
|------|------|----------|
| `consult` | After `solidsdd-context`, before / into intake | `.solidsdd/changes/<change_id>/knowledge-consult.md` (or repo-root draft if change dir not yet created—intake then moves/cites it) |
| `harvest` | After successful integration verify, **before** `status: done` | `.solidsdd/changes/<change_id>/knowledge-harvest.json` |

Requirement authority remains **ChangeBrief / Gherkin**. Graph `requirement` nodes are imported as `<change_id>/<id>` (e.g. `initial-reservation/R1`). Do **not** duplicate Brief text into `knowledge/` as a second SoT.

## What belongs in `knowledge/`

Every candidate must be **universal**, **non-trivial**, and **rarely updated** ([POL-KG-PERSISTENCE](../knowledge/policies/POL-KG-PERSISTENCE.md)). Non-trivial means a competent domain engineer would not call it obvious, or later agents would likely err on a **choice / exception / boundary**.

| Type | Put here when… |
|------|----------------|
| `concept` | Stable ubiquitous-language term (non-obvious naming or scope) |
| `policy` / `invariant` | Norm that multiple changes must obey **and** encodes a non-obvious bound |
| `pattern` | Preferred design/impl practice with rare exceptions |
| `decision` | ADR-worthy choice that later agents must not silently reverse |
| `lesson` | Incident / failed approach that should inform future Briefs |

**Do not harvest:** ephemeral acceptance wording, one-off sample paths, full OpenAPI/OCL bodies, tautologies / domain axioms restated without a choice boundary, or anything that would turn Brief into a living PRD. Trivial nodes have low information value and raise maintenance cost (staleness checks, graph noise).

## Consult (consume)

1. Ensure `.solidsdd/kg/` exists (or note gap). Run `scripts/solidsdd-kg.sh build --root .` when the CLI is available.
2. Prefer `solidsdd-kg context <id> --budget 8k` / `scope <dotted>` / `impact` for relevant policies and decisions.
3. Write a short Markdown pack for intake/brief: applicable policies, concepts, decisions, and explicit “none found”.
4. Intake reflects hits under Change Context Drivers / Constraints / Links; Brief may cite policy ids in `assumptions` / `constraints` without restating full policy text as authority.

## Harvest (produce)

1. Read Change Context, Brief, WorkPlan, notable critiques, and run `solidsdd-kg promote suggest --json` when available.
2. Propose only candidates that pass **universality + non-triviality + low churn**. Put obvious restatements in `skipped_reasons` (do not invent nodes “for completeness”).
3. Emit `knowledge-harvest.json` per [knowledge-harvest.schema.json](../schemas/knowledge-harvest.schema.json). Each `rationale` must say why the node is reusable **and** what is non-obvious.
4. Set `human_gate.required: true` when `candidates.length >= 1` **or** when the agent judges durable knowledge was discovered but needs human framing. Empty candidates with `required: false` is OK.
5. **Never apply** candidates without `gate-approval.json` `scope: knowledge_harvest` and `decision` `approve` or `approve_partial`.
6. On approval: create nodes under `knowledge/<type>/` via `solidsdd-kg promote apply --approve --type …` or hand-authored Markdown; add downstream links (`derives_from` / `links.yaml`) from `<change_id>/R*` to knowledge ids; run `solidsdd-kg check`.
7. On reject / skip: mark candidates `rejected` / `skipped` and proceed to `done`.

## Human gate

See [human-gates.md](human-gates.md). Orchestrators must not mark the change `done` while harvest gate is required and unapproved.

## Critique

Optional but recommended: `solidsdd-critique` with `subject: knowledge_harvest` after harvest emit, before the gate. Fail on living-PRD leakage, duplicate of existing knowledge without `supersedes`, missing universality rationale, or **trivial / tautological** candidates (no non-obvious choice, exception, or boundary).
