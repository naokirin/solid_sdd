# solidsdd-lint

Deterministic checks run **before** LLM critique (`solidsdd-critique` Step 0/1). Orchestrators do **not** invoke this outside critique (M1 scope).

## Usage

From a consuming project root (directory that contains `.solidsdd/`):

```bash
# From solid_sdd checkout, pointing at a project:
/path/to/solid_sdd/scripts/solidsdd-lint.sh --project-root /path/to/project [--change-id ID] [--pretty]

# Or if the script is on PATH / installed alongside skills:
scripts/solidsdd-lint.sh [--change-id ID] [--pretty]
```

Requires Python 3 + [`jsonschema`](https://pypi.org/project/jsonschema/) (`pip install jsonschema`).

## Output

JSON on stdout:

```json
{
  "version": "1",
  "change_id": "…",
  "result": "pass" | "fail",
  "findings": [
    {
      "severity": "blocker" | "major" | "minor",
      "category": "schema_violation" | "consistency" | "scope_gap" | "unverifiable_acceptance" | …,
      "location": "path#pointer",
      "detail": "…"
    }
  ]
}
```

Exit `1` when any finding is `blocker` or `major` (same rule as CritiqueReport).

## Checks (M1)

| Check | Severity |
|-------|----------|
| JSON Schema (Brief, WorkPlan, gate, status, optional plans/reports) | blocker |
| `change_id` vs directory name | blocker |
| Unknown / duplicate Brief ids; `covers` → unknown id | blocker |
| `depends_on` unknown id or cycle | blocker / major |
| Acceptance not Given/When/Then or >1 Scenario | major |
| Brief `in_scope` / `success_criteria` not in any `item.covers` | major |
| `covers` includes `out_of_scope` id | major |
| Scenario `@R*` / `@SC*` tags vs WorkPlan `covers` | major (missing) / minor (extra) |
| Ambiguity lexicon hits | minor |

Lexicon: [`ambiguity-lexicon.json`](ambiguity-lexicon.json) (EN + JA).

## Critique integration

`solidsdd-critique` must run this script first, import findings into CritiqueReport (map categories toward schema enums where possible), and only then do LLM adequacy review. Coverage existence is lint’s job; critique judges whether the cover is *adequate*.
