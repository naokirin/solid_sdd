# solidsdd-next

Deterministic **next-action** hints for `solidsdd-run` / resume (Intent-inspired I4).  
**Read-only:** never writes `run-state.json`. Depth B: `next` + `validate --declared`.

## Usage

```bash
scripts/solidsdd-next.sh next --project-root /path/to/project [--change-id ID] [--pretty]
scripts/solidsdd-next.sh validate --project-root /path/to/project --declared critique_change_brief [--change-id ID]
```

Requires Python 3 + `jsonschema`.

## Output

`next` prints a [run-next.schema.json](../../schemas/run-next.schema.json) object:

| Field | Meaning |
|-------|---------|
| `action` | Primary recommended step id |
| `skill` / `subject` | When a Task skill applies |
| `item_ids` | Ready WorkPlan items for waves |
| `legal_actions` | Set accepted by `validate --declared` |
| `reason` / `inputs` | Why / what to pass |

`validate` exits `0` when `--declared` equals `action` or is in `legal_actions`; else `1`.

## Orchestrator rules

1. At each outer step **start**, prefer running `next`.
2. Before launching a producer Task, `validate --declared <action>`.
3. On deviation, append `isolation_notes`: `next_deviation:<action>:<reason>` and continue only with an explicit reason.
4. Parent still **writes** `run-state.phase` after steps (this tool does not).

## Resume scenario (example)

On an interrupted change under `examples/inventory-reservation`:

```bash
cd examples/inventory-reservation
../../scripts/solidsdd-next.sh next --pretty
../../scripts/solidsdd-next.sh validate --declared "$(../../scripts/solidsdd-next.sh next | python3 -c 'import json,sys; print(json.load(sys.stdin)["action"])')"
```

If `phase` is `brief` without a passing critique file, `next` returns `critique_change_brief`. Declaring `waves` fails `validate`. Parent resumes by following `action` / `skill` without inventing phase order from chat.

## Execution Profile awareness

`next` reads `triage-result.json` and `run-state.execution_profile.effective` (see [triage.md](../../reference-src/triage.md)) and tailors its recommendation:

- `direct` (no `run-state.json` yet): `action: direct_implementation`, `legal_actions: [direct_implementation, done]` — never recommends `intake`/`brief`/`decompose`/`architecture`/`waves`.
- `thin`: `action: thin_implementation` (skill `solidsdd-implement`) → once implemented, `action: thin_verification` (skill `solidsdd-verify`) → on pass, `action: done`; on fail, `action: critique_verification_report` (never silently retries at `thin` — that's an escalation trigger).
- `standard` / `full`: unchanged behavior — the full phase-based recommendations below apply once Triage's `triage` phase is passed.
