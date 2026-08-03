# Run state and per-item artifacts (solidsdd.run / solidsdd.loop)

Orchestrators **persist** progress so retries, human gates, and mid-run crashes do not rely on chat memory. Source of truth for budgets and phase is `run-state.json`; ApplicationPlan / Critique / Verification JSON for each WorkPlan item live under `items/<item_id>/`.

Schema: `schemas/run-state.schema.json` (copied into orchestrator skill `references/` as `run-state.schema.json`). Layout: [contract-layout.md](contract-layout.md).

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

1. **Start of each orchestrator step:** read `run-state.json` if present (create with defaults on first write after intake).
2. **End of each step** (including after critique/verify fail handling): write `run-state.json` with updated `phase`, `wave_index`, `run_retry` / `items.*.loop_retry`, item statuses, and paths under `integration` when relevant.
3. **After each producer / critique Task:** write the JSON artifact to the paths above (do not leave ApplicationPlan / CritiqueReport / VerificationReport only in chat).
4. **Decrement retry `remaining`** when consuming an auto-retry (verify-fail or critique-fail or isolation re-run). Never invent a higher remaining than `max`.
5. **Resume:** if `phase` is not `done` and `status.json` is still `active`, continue from `phase` / item `loop_phase` using persisted plans—do not re-judge density from memory when `items/<id>/application-plan.json` exists unless critique failed and a producer re-run is required.

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

After `solidsdd-context` (or at run start), copy readiness from `.solidsdd/host-toolchain.json` into optional `host_toolchain`:

```json
"host_toolchain": {
  "ready": true,
  "source": ".solidsdd/host-toolchain.json",
  "missing": [],
  "resolved_at": "2026-08-04T00:00:00Z"
}
```

If a Subagent must rediscover tools despite that file, append `isolation_notes` with `toolchain_rediscovery:<tool>:<reason>`. Policy: [host-toolchain.md](host-toolchain.md).

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
