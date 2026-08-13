# Working language

Prose under `.solidsdd/` (and related human-readable acceptance text) follows a single **working language** so teams can write Change Context, Briefs, and reports in Japanese or another language without translating schema structure.

## How to set it (humans)

The value lives in **one place**, `.solidsdd/config.yaml` → `working_language` (schema: `schemas/project-config.schema.json`) — not duplicated into each agent's rule file. Every installed rule (`.cursor/rules/solidsdd.mdc`, `.devin/rules/solidsdd.md`, the `solid_sdd:begin`/`solid_sdd:end` block in `CLAUDE.md` / `AGENTS.md` / `.github/copilot-instructions.md`) just points at that key, so changing it later never means editing rule files per agent.

Set it with:

```bash
scripts/install-into-project.sh --language ja   # writes .solidsdd/config.yaml → working_language: "ja"
```

(asks interactively if `--language` is omitted; see [install.md](../docs/install.md#project-rule--working-language)). To change it later, either re-run with a different `--language`, or edit the key directly:

```yaml
working_language: "ja"
```

Use `en` (default / missing key), `ja`, or another short language tag.

## Resolution order (agents)

1. **Caller override** — e.g. `solidsdd-report` parameter `language` (`ja` / `en`). Affects **that report only**; does not rewrite Context / Brief / WorkPlan.
2. **`.solidsdd/config.yaml`** — `working_language` key.
3. **User request** — if the key is unset and the request’s dominant language is clear, use that.
4. **Default** — `en`.

After `solidsdd-intake`, later skills may also read the language recorded in Change Context §6 (see below) when `.solidsdd/config.yaml` is not in the subagent context.

## In scope (write in the working language)

| Artifact | What |
|----------|------|
| Change Context | Body prose under each section |
| ChangeBrief / WorkPlan / ApplicationPlan / Critique / Verification JSON | String **values** (`goal`, `detail`, `acceptance_criterion`, rationales, …) |
| Gherkin | Feature / Scenario **titles** and step **prose** |
| Change report (`report.md` / `report.html`) | Headings and body (unless caller `language` overrides) |

## Out of scope (always English / fixed)

| Kind | Examples |
|------|----------|
| JSON object keys and schema field names | `change_id`, `in_scope`, `human_gate` |
| Change Context **top-level headings** | `## 1. Demand and problem`, … (see [change-context.md](change-context.md)) |
| Gherkin **keywords** | `Feature`, `Scenario`, `Given`, `When`, `Then`, `And`, `But` |
| Machine identifiers | `change_id`, adapter ids, file paths, enum tokens (`active`, `fail`, …) |

Do **not** invent localized heading titles or Japanese Gherkin keywords (`機能` / `前提`, etc.).

## Intake recording

`solidsdd-intake` resolves the working language, writes Context body in that language, and records a short bullet under **§6. Key judgments and trade-offs**, e.g. `Working language: ja (from config.yaml)`. Downstream skills treat that as a hint when `.solidsdd/config.yaml` is not in context.

## Report override

`solidsdd-report` may emit a report in a different language via `language` without changing SoT artifacts. Quoted Gherkin / contract snippets stay as in source files.
