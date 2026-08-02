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
2. Else project rule `Working language:`.
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
| Non-functional requirements | `change-context.md` §4 with content (not empty placeholder) |
| Technology selection | `change-context.md` §5 with content |
| Design — WorkPlan | `work-plan.json` |
| Design — ApplicationPlan | One or more ApplicationPlan JSON files for this change (see discovery below) |
| Design — API contract | OpenAPI and/or GraphQL file exists at project defaults (or rule overrides) |
| Design — DbC (OCL) | At least one `contracts/**/*.ocl` (or project override) |
| Design — Formal | At least one `formal/**` spec when relevant; else omit or mark not performed |
| Key judgments | `change-context.md` §6 |
| Open questions | Always render; if no §7 / Brief `open_questions`, say none or not performed for the missing source |

### ApplicationPlan discovery

Look for (first match set wins; include all that clearly belong to this change):

- `.solidsdd/changes/<change_id>/application-plan*.json`
- `.solidsdd/application-plan*.json` whose content/summary clearly ties to this `change_id` or its WorkPlan item ids
- Paths listed in Context §8 Links

If none found → Design — ApplicationPlan = **Not performed**.

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

Copy/adapt tables or bullets from Context §4–§5. Preserve requirement / rationale / verification and decision / alternatives / rationale / source. Missing Context → Not performed.

### §5 Design

Subsections (omit a subsection only when not applicable to the stack **and** no plan asked for it; otherwise mark Not performed):

1. **WorkPlan** — item id, intent, `covers`, scenario name, status, depends_on (table). Link to `work-plan.json`.
2. **ApplicationPlan** — targets: kind, location, density, status, `covers` (WorkPlan ids), rationale (table). Link to plan JSON path(s).
3. **API contract** — natural-language summary of operations/types exposed; **Markdown: link only** to `openapi/openapi.yaml` or `graphql/schema.graphql` (no full YAML dump).
4. **DbC (OCL)** — natural-language summary of types/invariants/preconditions covered; **one bullet (or nested bullet) per operation / invariant**—do not pack many ops into a single unbroken sentence. **Markdown: link only** to each `.ocl` file.
5. **Formal** (optional) — summary + link to `formal/**`.

Do not paste full OpenAPI/OCL into Markdown.

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

## Constraints

- Read-only w.r.t. all solid_sdd sources except writing `report.md` / `report.html`
- No Change Context / Brief / WorkPlan / contract / implementation edits
- No critique, verify, or lifecycle status changes
- Prefer concise tables and bullets over essay PRD prose

## When to suggest this skill

After `solidsdd-intake` (and optional Change Context gate), after Brief, or before/after design-heavy phases—when a human needs a readable snapshot. Phrase as optional confirmation aid, not a blocking gate unless the project rule says otherwise.
