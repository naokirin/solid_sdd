# Run state and per-item artifacts (solidsdd.run / solidsdd.loop)

Orchestrators **persist** progress so retries, human gates, and mid-run crashes do not rely on chat memory. Source of truth for budgets and phase is `run-state.json`; ApplicationPlan / Critique / Verification JSON for each WorkPlan item live under `items/<item_id>/`. Optional Grill clarifications live under `clarifications/open.json` ([clarifications.md](clarifications.md)).

Schema: `schemas/run-state.schema.json` (copied into orchestrator skill `references/` as `run-state.schema.json`). Layout: [contract-layout.md](contract-layout.md).

**Deterministic next:** when available, run `scripts/solidsdd-next.sh next --change <id>` at step start and `validate --declared …` before launching a producer Task. Do not rely on chat memory for phase sequencing when next succeeds.

**Constrained state writes:** mutate `run-state.json` (and optionally WorkPlan item `status` / `status.json`) only via `scripts/solidsdd-run-state.sh` — see [Constrained mutations](#constrained-mutations-solidsdd-run-state) below. Do **not** use free-form `python -c` / open-ended heredoc scripts for these files (host allowlists treat unbounded Python as high risk and force repeated “may I run this?” prompts that are not product human gates).

## Paths

```text
.solidsdd/changes/<change_id>/
  run-state.json
  critique-change-context.json          # optional persisted outer critiques
  critique-change-brief.json
  critique-work-plan.json
  knowledge-consult.md
  knowledge-harvest.json
  critique-knowledge-harvest.json       # optional
  integration-verification-report.json
  critique-integration-verification.json
  items/<item_id>/
    application-plan.json
    critique-application-plan.json
    critique-api-contracts.json         # when that subject ran
    critique-dbc-contracts.json
    critique-derived-tests.json
    critique-formal-specs.json
    verification-report.json
    critique-verification-report.json
```

`<item_id>` matches the WorkPlan item `id` (e.g. `W1`). Solo `solidsdd-loop` without a WorkPlan item may use `items/ad-hoc/` or a caller-supplied id; prefer inventing a WorkPlan via `solidsdd-run` for multi-criterion work.

## Read / write convention

1. **Start of each orchestrator step:** read `run-state.json` if present (create with defaults on first write after intake via `solidsdd-run-state init`).
2. **End of each step** (including after critique/verify fail handling): update `run-state.json` with `phase`, `wave_index`, `run_retry` / `items.*.loop_retry`, item statuses, and paths under `integration` when relevant — prefer **`scripts/solidsdd-run-state.sh`** for these fields.
3. **After each producer / critique Task:** write the JSON artifact to the paths above with the **Write / StrReplace** file tools (or the producer Task). Do not leave ApplicationPlan / CritiqueReport / VerificationReport only in chat.
4. **Decrement retry `remaining`** when consuming an auto-retry (verify-fail or critique-fail or isolation re-run). Never invent a higher remaining than `max`.
5. **Resume:** if `phase` is not `done` and `status.json` is still `active`, continue from `phase` / item `loop_phase` using persisted plans—do not re-judge density from memory when `items/<id>/application-plan.json` exists unless critique failed and a producer re-run is required.

## Constrained mutations (`solidsdd-run-state`)

Wrapper: `scripts/solidsdd-run-state.sh` (impl: `scripts/solidsdd-run-state/run_state.py`). Writes are schema-validated against `schemas/run-state.schema.json`. `solidsdd-next` remains **read-only**.

| Command | Purpose |
|---------|---------|
| `init [--force]` | Create defaults (`phase: intake`, empty `items`) |
| `set-phase --phase <enum>` | Set top-level `phase` |
| `set-wave --index <n>` | Set `wave_index` |
| `note --append <text>` | Append deduped `isolation_notes` (e.g. `cost_skip:B4`) |
| `sync-items` | Populate/refresh `items` from `work-plan.json` |
| `set-item --id W1 [--status …] [--loop-phase …] [--sync-work-plan]` | Update one item; optional WorkPlan status sync |
| `set-host-toolchain` | Snapshot `.solidsdd/host-toolchain.json` into `host_toolchain` |
| `mark-change-done` | `status.json` → `done` and `phase: done` |

Common flags: `--project-root` (default `.`), `--change-id` (default active change).

**Allowed for state files:** this CLI, or **Write/StrReplace** on a single JSON file when the edit is visible in the tool diff.

**Forbidden:** free-form `python -c`, unbounded `python3 <<'PY'` heredocs, or other shell one-liners that can write arbitrary paths when updating `run-state.json` / WorkPlan item `status` / change `status.json`.

Example:

```bash
./scripts/solidsdd-run-state.sh --project-root . --change-id my-change init
./scripts/solidsdd-run-state.sh --project-root . sync-items
./scripts/solidsdd-run-state.sh --project-root . set-item --id W1 --status done --loop-phase done --sync-work-plan
./scripts/solidsdd-run-state.sh --project-root . note --append 'cost_skip:B4'
./scripts/solidsdd-run-state.sh --project-root . mark-change-done
```

## Defaults on create

```json
{
  "version": "1",
  "change_id": "<id>",
  "phase": "intake",
  "wave_index": 0,
  "run_retry": { "remaining": 3, "max": 3, "last_suggested_skills": [] },
  "items": {},
  "isolation_notes": []
}
```

After decompose, populate `items` from the WorkPlan (`pending` / `ready` mirroring `depends_on`). Each item should get `loop_retry: { "remaining": 3, "max": 3, "last_suggested_skills": [] }` and `artifact_dir: "items/<id>"`.

## Host toolchain

After `solidsdd-context` (or at run start), copy readiness from `.solidsdd/host-toolchain.json` into optional `host_toolchain` via:

```bash
./scripts/solidsdd-run-state.sh --project-root . set-host-toolchain
```

Result shape:

```json
"host_toolchain": {
  "ready": true,
  "source": ".solidsdd/host-toolchain.json",
  "missing": [],
  "resolved_at": "2026-08-04T00:00:00Z"
}
```

If a Subagent must rediscover tools despite that file, append `isolation_notes` with `toolchain_rediscovery:<tool>:<reason>` using `note --append`. Policy: [host-toolchain.md](host-toolchain.md).

## Retry budgets (state machine)

| Budget | Owned by | Scope |
|--------|----------|--------|
| `run_retry` | `solidsdd-run` | Outer intake/brief/decompose/integration retries |
| `items.<id>.loop_retry` | `solidsdd-loop` for that slice | Shared critique+verify retries inside the slice |

When `remaining` reaches `0`, set `loop_action` / stop to `human_gate` (see [loop-retry.md](loop-retry.md)). Do not track budgets only in conversation.

## Human gates

On gate stop, set `phase` / item `status` to reflect waiting (`stopped` / `blocked`), write `stopped_reason`, and keep ApplicationPlan on disk. Resume reads the same files ([human-gates.md](human-gates.md)).

## Discovery for report

`solidsdd-report` prefers `.solidsdd/changes/<change_id>/items/*/application-plan.json` over ad-hoc `.solidsdd/application-plan*.json` ([change-report.md](change-report.md)).
