---
name: solidsdd-report
description: >-
  Emit a human-readable Change Report (Markdown by default, optional HTML) for
  one change: demand, functional and non-functional requirements, technology
  selection, and design so far. Missing phases are marked not performed
  (未実施). Use when the user asks for a readable summary, review document, or
  solidsdd.report / solidsdd-report. Manual only—not part of solidsdd-run.
license: MIT
---

# solidsdd.report

## Execution

**Manual / orchestrator** — run in the current agent when the user asks. Not invoked automatically by `solidsdd-run` or `solidsdd-loop`. After intake, Brief, or design phases, those flows may **suggest** this skill for human review.

## Purpose

Turn existing machine-oriented artifacts into a single human-readable report for **one** `change_id` (active change by default, or a caller-supplied id). Do not invent content for phases that have not run yet—mark them **未実施** / **Not performed**.

## References

- [change-report.md](references/change-report.md) — **sections, presence rules, Markdown/HTML (required)**
- [working-language.md](references/working-language.md) — language resolution
- [change-lifecycle.md](references/change-lifecycle.md) — paths and `change_id`
- [contract-layout.md](references/contract-layout.md) — Feature / OpenAPI / OCL / formal paths
- [change-context.md](references/change-context.md) — framing sections to project
- [change-brief.md](references/change-brief.md) — scope fields
- [gherkin-requirements.md](references/gherkin-requirements.md) — Feature / Scenario role
- `scripts/solidsdd-report/README.md` (vendored alongside `scripts/solidsdd-report.sh`) — **`collect` / `render` usage (required)**; do the discovery/table/highlighting/diagram work in change-report.md via these scripts, not by hand

## Parameters

| Name | Required | Default | Meaning |
|------|----------|---------|---------|
| `change_id` | no | active change | Target change directory |
| `format` | no | `markdown` | `markdown`, `html`, or both |
| `language` | no | resolve per working-language.md | e.g. `ja` / `en` (report-only override) |

## Constraints

- Write only `.solidsdd/changes/<change_id>/report.md` and/or `report.html` — via `scripts/solidsdd-report.sh render`, not a hand-assembled Write
- Do **not** edit Change Context, Brief, WorkPlan, Features, OpenAPI, OCL, formal, tests, or implementation
- Do **not** fabricate missing requirements, NFRs, tech choices, or design
- Markdown: contract bodies are **links** only (plus natural-language summary)
- HTML: calm navy/black dark theme with **white body text**; Raw panels use `highlight.py`'s deterministic tokenizer (no Pygments/CDN dependency; avoid loud yellow/chartreuse) — `render` calls it internally
- Report language: caller `language` → project rule → Context / sources → `en` ([working-language.md](references/working-language.md)); override does not rewrite SoT — pass it as `"language"` in the narrative JSON (below)

## Steps

1. Run `scripts/solidsdd-report.sh collect --project-root . [--change-id ID] --pretty` (caller `change_id` override, else `active-change.json` — stop and ask if neither resolves). This runs [change-report.md](references/change-report.md)'s entire "Presence rules" / "ApplicationPlan discovery" / "ArchitecturePlan discovery" / coverage-matrix / diagram-eligibility logic mechanically — read its JSON output rather than re-deriving any of that by hand.
2. From the collected JSON's `sections`, note which of `design.api_contract` / `design.dbc` / `design.formal` are `"present"`. For each, read the linked contract file(s) (`artifacts.openapi_path` / `graphql_path` / `ocl_paths` / `formal_paths`) and write a short natural-language summary — this is the only prose synthesis this skill still does. Everything else in the report (Brief/NFR/WorkPlan/ArchitecturePlan/ApplicationPlan tables, verbatim Change Context prose, verbatim Gherkin Scenarios, the coverage matrix, diagrams) is mechanical and handled by `render` — do not re-type or re-summarize those. When Formal has an identifiable mode/status variable (see change-report.md "State diagrams"), also note its states/transitions.
3. Write a small narrative JSON with only what step 2 produced, e.g.:
   ```json
   {
     "language": "ja",
     "status_overview": "one paragraph, optional",
     "api_contract_summary": "…",
     "dbc_summary": "…",
     "formal_summary": "…",
     "formal_state_diagram": {"states": ["Idle", "Owned"], "transitions": [{"from": "Idle", "to": "Owned", "label": "Acquire"}]}
   }
   ```
   Omit fields (or the whole file) for sections that are `"not_performed"` or where no natural-language summary is warranted.
4. Run `scripts/solidsdd-report.sh render --project-root . --change-id ID --narrative PATH --format markdown|html|both` — writes `report.md`/`report.html` directly under `.solidsdd/changes/<change_id>/`. Do not hand-assemble the file content yourself; `render` embeds highlighted raw contracts, diagrams, and every mechanical section itself. For `html`, diagram SVGs render only when the [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) is available offline (a `mmdc` binary on `PATH`, or `npx --offline` finding an already-installed copy) — otherwise those diagrams fall back to Mermaid source only (still a complete, correct report). If nicer inline diagrams matter here, ask the user whether to allow a one-time network install and, only if they agree, re-run with `--allow-network` (see [change-report.md](references/change-report.md) "HTML rendering") — never pass that flag without asking first. If `report.html` still has no rendered SVGs after `--allow-network` (diagrams stay collapsed `<details>` Mermaid-source blocks), do not conclude the environment can't support it — first read `scripts/solidsdd-report/README.md`'s "Troubleshooting: SVG never renders" section; both documented causes (an ARM64 host resolving Puppeteer's own Chromium download to an x86-64 build; a Snap-confined system Chromium refusing to read files under `npx`'s cache or a dotfile directory) have a known fix there before you re-derive the diagnosis from scratch.

## Output

- Path(s) to `report.md` / `report.html` (from `render`'s output)
- `change_id` and language
- Short overview of Present vs Not performed sections (from `collect`'s `sections`)
