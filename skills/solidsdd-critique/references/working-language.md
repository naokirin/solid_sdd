# Working language

Prose under `.solidsdd/` (and related human-readable acceptance text) follows a single **working language** so teams can write Change Context, Briefs, and reports in Japanese or another language without translating schema structure.

## How to set it (humans)

In the consuming project’s solid_sdd project rule (copy of `project-rule.mdc` / `rules/solidsdd.mdc`):

```markdown
## Working language

- Working language: ja
```

Use `en` (default), `ja`, or another short language tag. **That one line is enough**—skills resolve language from the rule.

## Resolution order (agents)

1. **Caller override** — e.g. `solidsdd-report` parameter `language` (`ja` / `en`). Affects **that report only**; does not rewrite Context / Brief / WorkPlan.
2. **Project rule** — `Working language:` line in the project rule.
3. **User request** — if the rule is unset and the request’s dominant language is clear, use that.
4. **Default** — `en`.

After `solidsdd-intake`, later skills may also read the language recorded in Change Context §6 (see below) when the rule is unavailable in the subagent context.

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

`solidsdd-intake` resolves the working language, writes Context body in that language, and records a short bullet under **§6. Key judgments and trade-offs**, e.g. `Working language: ja (from project rule)`. Downstream skills treat that as a hint when the rule text is not in context.

## Report override

`solidsdd-report` may emit a report in a different language via `language` without changing SoT artifacts. Quoted Gherkin / contract snippets stay as in source files.
