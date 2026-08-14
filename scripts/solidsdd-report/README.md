# solidsdd-report tooling

Deterministic helpers for `solidsdd-report`, plus a `render` step that writes
`report.md` / `report.html` itself. Moving highlighting/diagramming into
scripts only pays off if the report-writing agent never has to *transcribe*
their output through its own generation stream — so `render.py` assembles
the finished file directly from `collect.py`'s data (tables, verbatim Change
Context prose, verbatim Gherkin, coverage matrix, raw contract embeds,
diagrams) plus a small, agent-authored "narrative" JSON containing only the
handful of sections that genuinely need LLM synthesis (API contract / DbC /
Formal natural-language summaries, the status-overview paragraph). The
report is a *view*, not new authored content, so most of it never needed an
LLM pass in the first place.

## Usage

From a consuming project root (directory that contains `.solidsdd/`):

```bash
scripts/solidsdd-report.sh collect --change-id ID [--project-root .] [--out PATH] [--pretty]
scripts/solidsdd-report.sh highlight PATH [--display-path REL] [--max-bytes N] [--out PATH] [--pretty]
scripts/solidsdd-report.sh highlight --css-only   # print TOKEN_CSS to inline once in report.html
scripts/solidsdd-report.sh diagram [--in PATH] [--pretty]   # payload JSON on stdin when --in omitted
scripts/solidsdd-report.sh render --change-id ID [--project-root .] [--narrative PATH] [--format markdown|html|both]
```

`render` writes `.solidsdd/changes/ID/report.md` and/or `report.html`
directly — the caller doesn't paste generated content into a Write call.
`--narrative` is optional; omit it (or omit fields) and those sections fall
back to a "no natural-language summary supplied" stub the agent can leave as
a TODO or a follow-up edit. `collect` / `highlight` / `diagram` remain
available standalone for a caller that wants to inspect or post-process the
intermediate data before rendering.

Requires Python 3 + [`PyYAML`](https://pypi.org/project/PyYAML/) (same as
`solidsdd-lint` / `solidsdd-architecture`). No other third-party dependency —
`highlight.py`'s tokenizers are regex-based on purpose, so no Pygments/CDN
install is needed in a consuming project.

## Modules

| File | Role |
|------|------|
| `collect.py` | Resolves `change_id`, reads Change Context / ChangeBrief / WorkPlan / `nfr.json` / tied Features / ApplicationPlan(s) / ArchitecturePlan / contracts, computes Present / Not-performed per report section, the Brief-id coverage matrix, working-language hint, verbatim Change Context section text, verbatim tied Gherkin Scenario blocks, and diagram-eligibility + node/edge data. Emits one JSON blob. |
| `highlight.py` | Regex tokenizer for JSON / YAML / Gherkin / OCL / GraphQL → HTML `<span class="tok-*">`-wrapped source, with a fixed `TOKEN_CSS` block (cyan keys, salmon strings, muted amber keywords — no yellow/chartreuse). Truncates raw embeds at `--max-bytes` (default 100KB) per change-report.md. |
| `diagram.py` | Mermaid source + a hand-laid-out inline SVG for the three diagram kinds change-report.md defines (`dependency_graph`, `target_mapping`, `state_diagram`). SVG is omitted (Mermaid-only) once the node count passes the point a fixed layout stays legible — the caller doesn't need to judge that threshold itself. |
| `render.py` | Combines `collect.py` + `highlight.py` + `diagram.py` output with the narrative JSON and writes `report.md`/`report.html` directly to disk. |
| `cli.py` | `collect` / `highlight` / `diagram` / `render` subcommands, dispatched by `scripts/solidsdd-report.sh`. |

## Narrative JSON (render's only free-text input)

```json
{
  "language": "en",
  "status_overview": "One paragraph on where this change stands.",
  "api_contract_summary": "Natural-language summary of operations/types exposed.",
  "dbc_summary": "Natural-language summary of OCL types/invariants/preconditions.",
  "formal_summary": "Natural-language summary of the formal spec.",
  "formal_state_diagram": {"states": ["Idle", "Owned"], "transitions": [{"from": "Idle", "to": "Owned", "label": "Acquire"}]}
}
```

All fields are optional. `formal_state_diagram` is only worth supplying when
a Formal spec has an identifiable mode/status variable driving a small
number of states (see change-report.md "State diagrams") — deciding that
still requires reading the `.tla`/`.als` source, which stays the agent's job.

## Output

`collect`: see the JSON shape produced by `collect()` — `sections` (per
report section: `state: "present"\|"not_performed"` + owning skill),
`coverage_matrix` (Brief `R*`/`SC*` id → covering WorkPlan items → tied
Scenario), `diagrams` (per-kind `eligible` flag + ready-to-render node/edge
data), `artifacts` (parsed content + resolved paths + verbatim section text),
`source_artifacts` (flat list for report §8).

`highlight`: `{"path", "language", "truncated", "original_bytes", "html"}`.

`diagram`: `{"mermaid", "svg"}` (`svg` is `null` above the legibility
threshold — keep the Mermaid source only in that case, exactly as
change-report.md already allows).

`render`: `{"markdown": "<path written>", "html": "<path written>"}` for
whichever `--format` was requested.

## What this does *not* do

No natural-language synthesis beyond the narrative JSON's few fields — that
stays the report-writing agent's job. It also does not cache across runs
(re-collecting/re-rendering is still a full pass every time) — see
change-report.md for that as a separate, later concern.
