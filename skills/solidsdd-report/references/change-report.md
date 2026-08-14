# Change report (solidsdd.report)

`solidsdd-report` reads existing change artifacts and emits a **human-readable** report for one change. It does **not** invent missing requirements, NFRs, tech choices, or design—sections without source artifacts are marked **not performed** (Japanese: **未実施**).

Manual skill only. Not part of `solidsdd-run` / `solidsdd-loop` automation. Orchestrators and human-gate stops may **suggest** running it so people can review framing and design so far.

## Role split

| Layer | Artifact | Report section |
|-------|----------|----------------|
| Framing | `change-context.md` | Demand, NFR, tech, judgments, open questions |
| Scope | `change-brief.json` | Functional requirements (scope lists) |
| Acceptance | `requirements/**/*.feature` | Functional requirements (scenarios) |
| Slice plan | `work-plan.json` | Design (work plan summary) |
| Structural design | ArchitecturePlan JSON | Design (modules / dependencies / ownership / constraints) |
| Apply judgment | ApplicationPlan JSON | Design (contract targets) |
| Contracts | OpenAPI / GraphQL / OCL / formal | Design (links + raw embed in HTML) |

The report is a **view**, not a new source of truth. Do not feed the report back as input that overrides Brief / contracts.

## Inputs

| Input | Default | Notes |
|-------|---------|-------|
| `change_id` | from `.solidsdd/active-change.json` | Caller override wins when a valid id is given |
| `format` | `markdown` | `html` optional (alone or in addition) |
| `language` | resolve per below | Caller override: `ja` / `en` (or equivalent); report-only |

### Resolving `change_id`

1. If the caller supplies `change_id`, use it (validate kebab-case; directory must exist under `.solidsdd/changes/`).
2. Else read `.solidsdd/active-change.json` → `change_id`.
3. If neither works, stop and ask for `change_id` (do not invent).

### Inferring report language

Follow [working-language.md](working-language.md):

1. Caller `language` override wins (**report only** — do not rewrite SoT artifacts).
2. Else `.solidsdd/config.yaml` → `working_language`.
3. Else Change Context §6 recorded language / dominant language of `change-context.md` (and Brief prose if context missing).
4. Else dominant language of the user request if clear; otherwise `en`.
5. Mixed sources: follow Change Context; keep quoted Gherkin/Scenario text as in the Feature files.
6. Status labels: Japanese → `未実施` / `実施済`; English → `Not performed` / `Present`.

## Output paths

| Format | Path |
|--------|------|
| Markdown (default) | `.solidsdd/changes/<change_id>/report.md` |
| HTML (optional) | `.solidsdd/changes/<change_id>/report.html` |

Overwrite previous reports for the same `change_id`. Do not write product-wide reports outside the change directory.

## Presence rules (required)

For each report section (and each design subsection), decide:

| State | When |
|-------|------|
| **Present** | The governing artifact exists and has usable content for that section |
| **Not performed** | Artifact missing, empty, or section not yet produced by the owning skill |

Rules:

- Never fabricate demand, NFRs, tech choices, WorkPlan items, ApplicationPlan targets, or contract bodies.
- When **Not performed**, write a short stub only (status + which skill produces it). No speculative bullets.
- Partial sections: show what exists; mark only the missing subsections as not performed (e.g. WorkPlan present, OpenAPI not performed).
- Cross-change Feature files may exist from prior changes—include Scenarios referenced by this change’s Brief / WorkPlan / Context §8 Links; if none of those exist yet, mark functional detail **Not performed** even if unrelated Features are on disk.

### Artifact → section map

| Report section | Present when |
|----------------|--------------|
| Demand and problem | `change-context.md` with §1 (and §2 when present) |
| Functional requirements | `change-brief.json` and/or Feature paths tied to this change |
| Non-functional requirements | `nfr.json` and/or `change-context.md` §4 with content |
| Technology selection | `change-context.md` §5 with content |
| Design — WorkPlan | `work-plan.json` |
| Design — ArchitecturePlan | `architecture-plan.json` for this change exists with `status: changed` (an existing file with `status: unchanged` is **Present** too, rendered as a one-line note, not Not performed) |
| Design — ApplicationPlan | One or more ApplicationPlan JSON files for this change (see discovery below) |
| Design — API contract | OpenAPI and/or GraphQL file exists at project defaults (or rule overrides) |
| Design — DbC (OCL) | At least one `contracts/**/*.ocl` (or project override) |
| Design — Formal | At least one `formal/**` spec when relevant; else omit or mark not performed |
| Key judgments | `change-context.md` §6 |
| Open questions | Always render; if no §7 / Brief `open_questions`, say none or not performed for the missing source |

### ApplicationPlan discovery

Look for (first match set wins; include all that clearly belong to this change):

- `.solidsdd/changes/<change_id>/items/*/application-plan.json` (**preferred**)
- `.solidsdd/changes/<change_id>/application-plan*.json`
- `.solidsdd/application-plan*.json` whose content/summary clearly ties to this `change_id` or its WorkPlan item ids (legacy)
- Paths listed in Context §8 Links

Also cite `run-state.json` in §8 Source artifacts when present (phase / item statuses).

If none found → Design — ApplicationPlan = **Not performed**.

### ArchitecturePlan discovery

Look for `.solidsdd/changes/<change_id>/architecture-plan.json` (change-level, not per-item — unlike ApplicationPlan; it is a **generated projection** of `.solidsdd/architecture/workspace.dsl` + `invariants.yaml`, not hand-authored). If missing → Design — ArchitecturePlan = **Not performed** (`solidsdd-architecture`). If present with `status: unchanged`, render as **Present** with a one-line "no structural change" note (do not treat it as Not performed — the judgment ran, it just found nothing to record) plus its `summary` when given. When `status: changed` and `.solidsdd/changes/<change_id>/architecture-reasoning.md` exists, link it alongside the ArchitecturePlan tables as the *why* behind the modules/dependencies/constraints shown (do not inline its full text — it is prose, not a table). When `.solidsdd/changes/<change_id>/physical-design.md` also exists (Architecture Depth Level 3 only), link it too as the Logical → Physical realization — do not inline its table; it is optional and most changes won't have one.

## Required document shape (Markdown)

Use these top-level headings. Translate heading text to the report language; keep the same order and numbering.

```markdown
# Change report: <change_id>

## Status overview
## 1. Demand and problem
## 2. Functional requirements
## 3. Non-functional requirements
## 4. Technology selection
## 5. Design
## 6. Key judgments and trade-offs
## 7. Open questions
## 8. Source artifacts
```

### Status overview

Table of sections → Present / Not performed (and skill that produces the missing piece).

### §1 Demand and problem

From Change Context §1–§2. Include drivers/constraints. If Context missing → entire section Not performed (`solidsdd-intake`).

### §2 Functional requirements

- From Brief: `goal`, `in_scope`, `out_of_scope`, `success_criteria` — render each scoped item as **`id` — `text`** (do not drop ids or concrete scope items).
- From Features: Scenario names + tags (`@R1` …) + short Given/When/Then paraphrase or verbatim Scenario blocks; link to `feature_path`.
- **Coverage matrix** (when Brief + WorkPlan exist): table or list of Brief `R*` / `SC*` ids → WorkPlan item ids that `covers` them → Scenario name / tags. Mark uncovered ids explicitly (should already fail lint).
- If Brief and Features both missing → Not performed (`solidsdd-brief` / `solidsdd-decompose`).

### §3–§4 NFR and technology

- Prefer `nfr.json` as SoT for §3 Non-functional requirements (render id / quality / status / requirement / threshold). Fall back to Context §4 only if `nfr.json` is missing (mark that SoT is absent).
- Technology: copy/adapt tables from Context §5. Missing Context → Not performed.

### §5 Design

Subsections (omit a subsection only when not applicable to the stack **and** no plan asked for it; otherwise mark Not performed):

1. **WorkPlan** — item id, intent, `covers`, scenario name, status, depends_on (table). Link to `work-plan.json`.
2. **ArchitecturePlan** — `status`; when `changed`: **a dependency diagram first** (see "Diagrams" below), then modules (id, responsibility, `owns`, `public`), dependencies (from, to, reason, kind), constraints (type, from, to, reason) as tables; when `unchanged`: one-line note + `summary`. Link to `architecture-plan.json`. When `physical-design.md` exists (Level 3 only), add a short **Physical Design** sub-note linking to it and naming the Logical → Physical realizations it records (one line per row is enough — do not reproduce its tables in the report).
3. **ApplicationPlan** — when the plan is large enough to benefit (see "Diagrams"), **a target-mapping diagram first**, then targets: kind, location, density, status, `covers` (WorkPlan ids), rationale (table). Link to plan JSON path(s).
4. **API contract** — natural-language summary of operations/types exposed; **Markdown: link only** to `openapi/openapi.yaml` or `graphql/schema.graphql` (no full YAML dump).
5. **DbC (OCL)** — natural-language summary of types/invariants/preconditions covered; **one bullet (or nested bullet) per operation / invariant**—do not pack many ops into a single unbroken sentence. **Markdown: link only** to each `.ocl` file.
6. **Formal** (optional) — when a spec has an identifiable state/mode variable (see "Diagrams"), **a state diagram first**, then summary + link to `formal/**`.

Do not paste full OpenAPI/OCL into Markdown.

### Diagrams

A picture is easier to scan than a table **only** when the underlying
artifact actually has graph or state-machine shape. Check each source
against the table below; do not add a diagram anywhere else (see
"Non-targets" at the end of this section) — a diagram is never a
substitute for the required tables, it goes **in addition to** them,
placed right after the one-line `status`/`summary` line and before the
tables (skim the picture, then read the detail).

| Source | Diagram kind | When |
|--------|--------------|------|
| ArchitecturePlan | dependency graph (`flowchart`) | `status: changed` and `modules[]` has ≥ 2 entries — always include |
| WorkPlan | dependency graph (`flowchart`) | ≥ 2 items and at least one `depends_on` edge — include; a WorkPlan with no `depends_on` edges at all is a flat list and doesn't need one |
| ApplicationPlan | target mapping (`flowchart`, bipartite) | ≥ 3 targets, or targets span ≥ 2 `kind`s — a plan with 1–2 targets of one kind is already fully readable as a table |
| Formal (TLA+ / Alloy) | state diagram (`stateDiagram-v2`) | The spec has an identifiable state/mode/owner-style variable with a small number of distinct values driving its actions — see below |

#### Dependency graphs (ArchitecturePlan, WorkPlan)

**Nodes**: one per module (ArchitecturePlan) or item id (WorkPlan), label =
`id` (+ a short responsibility/intent fragment when it fits).
**Edges**: solid, labelled with `kind` when present, for
`dependencies[]` / `depends_on`. Dashed **red**, labelled `forbidden`, for
`constraints[]` entries with `type: forbid_dependency`. Never render
`no_cycles` as an edge — it is a graph-wide rule, not a specific edge; note
it once in prose next to the diagram instead (e.g. "no dependency cycles
required among these modules").

```mermaid
flowchart LR
  inventory["inventory<br/>own available stock"]
  reservation["reservation<br/>own hold lifecycle"]
  reservation -->|runtime| inventory
  inventory -.->|forbidden| reservation
  linkStyle 1 stroke:#ff6b6b,stroke-dasharray: 4 2
```

#### Target mapping (ApplicationPlan)

Bipartite: left column = WorkPlan item ids the plan `covers` (or Brief scope
ids when a plan has no `covers`), right column = one node per **distinct**
`(kind, location)` pair, labelled with `kind` + a short location fragment +
`density`. Edge from each covering item to each target it maps to; no
edge styling needed (there is no "forbidden" concept here — `status: defer`
targets are simply labelled `(defer)` on the node instead of a distinct
edge style).

```mermaid
flowchart LR
  W1["W1"]
  W2["W2"]
  api1["api: POST /reservations<br/>density: standard"]
  dbc1["dbc: Reservation.ocl#reserve<br/>density: standard"]
  W1 --> api1
  W1 --> dbc1
  W2 --> dbc1
```

#### State diagrams (Formal: TLA+ / Alloy)

Formal specs are prose/math, not structured JSON — read the spec and
identify the **one** variable that most resembles a mode/status/owner
(e.g. `owner`, `status`, `phase` in the `.tla`/`.als` source). Treat its
small set of distinct values as states, and each action (operator that
appears in the `Next` disjunction, or Alloy predicate) that changes that
variable as a transition between the states it moves between. This is a
**simplification for illustration**, not a formal transcription — say so
in one caption line under the diagram, and always link the actual spec
file as the source of truth. Skip the diagram (keep prose + link only)
when no such single variable exists, or when the spec has more states
than fit legibly (roughly > 6).

Do not fold parameterized/per-process detail (e.g. a `remaining[c]`
function over multiple clients) into extra states — caption it instead
(e.g. "each client repeats Acquire → Add up to its own limit"). The
diagram shows the **shape** of the control flow, not the full formal
semantics.

```mermaid
stateDiagram-v2
  [*] --> Idle
  Idle --> Owned: Acquire(c)
  Owned --> Idle: Add(c)
  Idle --> [*]: Terminating (Done)
```

#### Markdown rendering (all kinds)

Emit a fenced ` ```mermaid ` block using the diagram kind's own syntax
(`flowchart LR` / `stateDiagram-v2`) — GitHub, GitLab, and most Markdown
viewers render these natively; they degrade to readable pseudo-diagram
text everywhere else, so no fallback image is needed. Sanitize node ids
for Mermaid (module/item ids may contain `-`; Mermaid node ids should
not — replace `-` with `_` for the node id, keep the original id in the
label text).

#### HTML rendering (all kinds)

Render as an **inline, generation-time SVG** (no JS library, no CDN —
consistent with this spec's "prefer generation-time processing, stay
offline-safe" stance):

1. **Dependency graphs / target mappings**: place nodes left-to-right (or,
   for the bipartite target mapping, in two columns) in the order they
   appear in the source array, one row per column, evenly spaced boxes.
   Draw a straight solid arrow between boxes per edge, labelled with
   `kind` near the midpoint when present; draw forbidden edges dashed red,
   curved above the row, labelled `forbidden`.
2. **State diagrams**: for ≤ 4–5 states, arrange boxes in a simple row or
   small loop and draw labelled arrows for each transition the same way;
   above that, or when transitions would cross too much to stay legible,
   skip the SVG and keep only the Mermaid source.
3. In every case: above roughly 6–8 nodes, or when a hand-laid-out single
   row/loop would stop being legible, skip the SVG and keep only the
   Mermaid source — do not force a layout that would be misleading.

Put the rendered SVG in view by default, and the raw Mermaid source in a
`Diagram source` `<details>`/tab next to it (same tab/accordion mechanism as
Raw JSON below) so a reader can copy it into a Mermaid-aware tool. Reuse the
report's existing color tokens (`--accent` for normal edges/nodes,
`#ff6b6b` for forbidden edges) so the diagram matches the rest of the dark
theme.

#### Non-targets

Do not add a diagram for sections that are not graph- or state-shaped:
NFR table, Brief scope list, coverage matrix (Brief ids → WorkPlan items →
Scenario — already a clear table, a mapping diagram would just duplicate
it with less precision), OCL invariants, Gherkin Scenarios (Given/When/Then
is already a readable structured format — behavior belongs there per
[architecture-axes.md](architecture-axes.md)'s Role separation table; a
report diagram of it risks drifting from that source of truth instead of
just linking/quoting it), API contract endpoint lists (the OpenAPI/GraphQL
file itself, linked, is the right level of detail). When genuinely unsure
whether a section qualifies, prefer no diagram — a wrong or cluttered one
hurts understanding more than a good table does.

### §6–§7 Judgments and open questions

From Context §6–§7 and Brief `open_questions`. Deduplicate.

### §8 Source artifacts

Bullet list of paths actually read (Context, Brief, WorkPlan, Features, plans, contracts).

## HTML format (optional)

When `format` includes `html`, write a **self-contained** `report.html` (inline CSS; minimal inline JS allowed for tabs).

Requirements:

- Same section order and presence rules as Markdown.
- **Dark theme by default**: calm deep navy / near-black surfaces (`#070b14`–`#0f1626` range), **white or near-white body text** (`#ffffff` / light gray for secondary). Avoid loud yellow / chartreuse / neon monokai-style code backgrounds; prefer muted syntax themes such as Pygments `github-dark` (or equivalent) with inlined CSS.
- **Syntax token contrast (required for Raw)**: keys and string/scalar values must be clearly distinguishable (e.g. cool cyan keys vs warm salmon strings). In Gherkin, keywords (`Feature` / `Scenario` / `Given` / `When` / `Then`) must contrast with step/title prose (near-white). Do not paint keys and `.nf` step text the same color.
- **Natural language** is the default visible body for each design/contract block.
- For OpenAPI, GraphQL, OCL, formal, and ApplicationPlan/WorkPlan raw JSON:
  - Provide **tabs** or equivalent switcher: e.g. `Summary` | `Raw`
  - And/or `<details>` / accordion so raw can be expanded without leaving the page
- Embed raw file contents inside the HTML (escape properly). If a file is huge (> ~100KB), embed a truncated head with a clear note and keep the repo path link.
- **Syntax highlighting on Raw panels** (YAML / JSON / Gherkin Feature / OCL / formal / GraphQL as applicable).
  - **Prefer generation-time highlighting** (e.g. Pygments) with token CSS **inlined** in `report.html`, so colors work offline, under `file://`, and in IDE HTML previews without a network.
  - CDN highlight.js is optional only; if used, load from a known-good package path such as `@highlightjs/cdn-assets` (plain `npm/highlight.js@…/highlight.min.js` may 404). Raw must remain readable if scripts fail.
  - Mark languages appropriately when using a runtime highlighter (`language-yaml`, `language-json`, `language-gherkin`, custom `language-ocl`, etc.).
- Basic layout/tabs must not *require* a CDN (page remains usable offline without colors when generation-time highlighting was skipped).
- **Diagrams** (dependency graphs, target mappings, state diagrams — see "Diagrams" above): inline, generation-time SVG — no bundled/CDN JS library. Raw Mermaid source available alongside for portability.

### Suggested HTML patterns

```html
<section class="contract">
  <h3>API contract</h3>
  <p class="summary">…natural language…</p>
  <div class="tabs" data-tabs>
    <button type="button" aria-selected="true" data-tab="summary">Summary</button>
    <button type="button" data-tab="raw">Raw</button>
    <div data-panel="summary">…</div>
    <div data-panel="raw" hidden>
      <p><a href="../../../openapi/openapi.yaml">openapi/openapi.yaml</a></p>
      <pre><code class="language-yaml">…escaped raw…</code></pre>
    </div>
  </div>
</section>
```

Relative links from `.solidsdd/changes/<change_id>/report.html` to repo-root contracts must be correct (typically `../../../openapi/…`, `../../../contracts/…`).

A dependency diagram (see "Diagrams" above) sits inline, SVG first, source
in a `<details>`:

```html
<figure class="diagram">
  <svg viewBox="0 0 640 200" width="100%" role="img" aria-label="Module dependency diagram">
    <!-- nodes as rounded <rect> + <text>, solid arrows for dependencies,
         dashed red arrows labelled "forbidden" for forbid_dependency -->
  </svg>
  <details>
    <summary>Diagram source (Mermaid)</summary>
    <pre class="raw"><code>flowchart LR
  ...</code></pre>
  </details>
</figure>
```

## Constraints

- Read-only w.r.t. all solid_sdd sources except writing `report.md` / `report.html`
- No Change Context / Brief / WorkPlan / contract / implementation edits
- No critique, verify, or lifecycle status changes
- Prefer concise tables and bullets over essay PRD prose

## When to suggest this skill

After `solidsdd-intake` (and optional Change Context gate), after Brief, or before/after design-heavy phases—when a human needs a readable snapshot. Phrase as optional confirmation aid, not a blocking gate unless the project rule says otherwise.
