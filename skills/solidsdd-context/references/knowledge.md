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

Prefer **Means** (reusable decision criteria from Change Context §6) over **tech selection** (Change Context §5 stack picks for this change). Do not harvest one-off language/API/persistence choices that belong only in Context.

| Type | Put here when… |
|------|----------------|
| `concept` | Stable ubiquitous-language term (non-obvious naming or scope) — see **Ubiquitous language** below |
| `policy` / `invariant` | Norm that multiple changes must obey **and** encodes a non-obvious bound |
| `pattern` | Preferred design/impl practice with rare exceptions |
| `decision` | ADR-worthy choice that later agents must not silently reverse |
| `lesson` | Incident / failed approach that should inform future Briefs |

**Do not harvest:** ephemeral acceptance wording, one-off sample paths, full OpenAPI/OCL bodies, tautologies / domain axioms restated without a choice boundary, one-off §5 stack selections, or anything that would turn Brief into a living PRD. Trivial nodes have low information value and raise maintenance cost (staleness checks, graph noise).

### Ubiquitous language (`concept`)

**Problem:** Without durable terms, later agents infer vocabulary from scattered OpenAPI / OCL / Gherkin / code — drift and reinvention follow.

**Role split:**

| Kind | Answers | Example |
|------|---------|---------|
| `concept` | **What** does this term mean? Scope, aliases, contrast with near-neighbors | `soft-hold` vs confirmed order; `visible` vs `exists` |
| `policy` / `decision` | **How** must we decide or behave? | opaque-principal AuthZ only; list is unfiltered full dump |

`concept` nodes are **short definitions + pointers** to contract SoT (OpenAPI schema name, OCL type, named error). They are **not** a second copy of OpenAPI/OCL bodies.

**When to harvest `concept` (all must hold):**

1. **Stability** — term recurs across multiple changes or contracts
2. **Scope risk** — competent engineers confuse it with a neighbor (`hold` vs `reservation`, `availableStock` vs on-hand inventory, `visible` vs `exists`)
3. **Low churn** — definition changes rarely; contract details may evolve but the term’s meaning stays

Set **`facets: [vocabulary]`** on every `concept` (and on policy/decision nodes that primarily define a term’s meaning).

**When to skip (put in `skipped_reasons`):**

- Pure OpenAPI field rename or wire shape with no semantic ambiguity
- Tautology with no contrast (“a hold is a hold”)
- One-off sample id / path name

**Greenfield:** the first meaningful change should seed **core domain concepts** (typically 3–8) alongside Means policies — not only ADR-style policy/decision nodes.

**Consult output:** include a dedicated **Ubiquitous language** section (table: id, term, one-line definition, contract pointers). List vocabulary **gaps** when Brief/Gherkin use domain terms with no `concept` node. Prefer `solidsdd-kg context` facet index when nodes carry `facets: vocabulary`.

**Harvest provenance for concepts:** `rationale` must cite **(1)** where the term was settled (Grill Q, Brief Means, contract elevation, critique), **(2)** why reuse matters, **(3)** what is confused without the node (neighbor term, scope, or named-error channel).

### Maturity (epistemic; not lifecycle `status`)

Optional frontmatter `maturity`: `hypothesized` | `confirmed` | `canonical`. Missing → treat as `confirmed`. Human-gated harvest **apply** defaults new nodes to `canonical`. Consult / `solidsdd-kg context` ranks canonical above confirmed above hypothesized.

### Facets (optional)

Optional frontmatter `facets`: array of `vocabulary` | `invariant` | `decider` | `acceptance-property`. Complements `type` for consult sectioning and lint. Unknown facet values fail `solidsdd-kg check` / lint.

## Consult (consume)

1. Ensure `.solidsdd/kg/` exists (or note gap). Run `scripts/solidsdd-kg.sh build --root .` when the CLI is available.
2. Prefer `solidsdd-kg context <id> --budget 8k` / `scope <dotted>` / `impact` for relevant policies and decisions.
3. Write a short Markdown pack for intake/brief with these sections:
   - **Policies / decisions / invariants** (Means)
   - **Ubiquitous language** — table of applicable `concept` nodes (`facets: vocabulary`) or **None**
   - **Suggested citations** for Brief `assumptions` / `constraints`
   - **Gaps** — missing kg, CLI gap, **undefined domain terms** used in prior contracts/Brief
4. Intake reflects hits under Change Context Drivers / Constraints / Links; Brief may cite policy **and concept** ids in `assumptions` / `constraints` without restating full text as authority.

## Harvest (produce)

1. Read Change Context, Brief, WorkPlan, notable critiques, and run `solidsdd-kg promote suggest --json` when available (includes `contract_vocabulary` hints for named errors / schema types not yet covered by `concept` nodes).
2. Propose candidates that pass **universality + non-triviality + low churn** (Means **and** ubiquitous-language `concept` where scope risk exists). Put obvious restatements and §5-only stack picks in `skipped_reasons` (do not invent nodes “for completeness”).
3. For each `concept` candidate: set `facets: ["vocabulary"]`; keep `body` to 1–3 sentences + contract pointers; prefer `id` prefix `CON-`.
4. Emit `knowledge-harvest.json` per [knowledge-harvest.schema.json](../schemas/knowledge-harvest.schema.json). Each `rationale` must say **(1)** why this change yielded the candidate (extraction provenance: Grill Q, Brief Means, Context §6, existing POL extension, critique finding, etc.), **(2)** why the node is reusable across changes, **and** **(3)** what is non-obvious (choice, exception, or boundary). Set candidate `maturity` to `hypothesized` until human confirms; after gate apply, nodes are written `canonical`.
5. Set `human_gate.required: true` when `candidates.length >= 1` **or** when the agent judges durable knowledge was discovered but needs human framing. Empty candidates with `required: false` is OK.
6. **Never apply** candidates without `gate-approval.json` `scope: knowledge_harvest` and `decision` `approve` or `approve_partial`.
7. On approval: create nodes under `knowledge/<type>/` via `solidsdd-kg promote apply --approve --type …` or hand-authored Markdown (apply writes `maturity: canonical`); add downstream links (`derives_from` / `links.yaml`) from `<change_id>/R*` to knowledge ids; run `solidsdd-kg check`.
8. On reject / skip: mark candidates `rejected` / `skipped` and proceed to `done`.

## Human gate

See [human-gates.md](human-gates.md). Orchestrators must not mark the change `done` while harvest gate is required and unapproved.

## Critique

Optional but recommended: `solidsdd-critique` with `subject: knowledge_harvest` after harvest emit, before the gate. Fail on living-PRD leakage, one-off §5 tech selection harvested as policy, duplicate of existing knowledge without `supersedes`, missing universality rationale, **missing candidacy reason** (no extraction provenance / why-harvested in `rationale`), or **trivial / tautological** candidates (no non-obvious choice, exception, or boundary).
