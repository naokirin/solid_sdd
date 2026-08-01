# Phase 3 — human_gate → formal dry-run

Orchestrator dry-run against `examples/memory-formal` (2026-08-02).

## Intent

Maintain TLA+ exclusive shared-memory adds (`Clients=2`); TLC via `./verify.sh`.

## Step A — Judge (Task subagent)

`solidsdd-judge` returned (abridged):

```json
{
  "version": "1",
  "confidence": "high",
  "human_gate": {
    "required": true,
    "reason": "Phase 3 early rollout: formal apply requires human approval before solidsdd-apply-formal"
  },
  "targets": [
    {
      "kind": "formal",
      "location": "formal/ExclusiveMemory.tla|formal/ExclusiveMemory.cfg",
      "density": "strict",
      "adapter_hint": "tla",
      "status": "apply",
      "signals": ["concurrency_safety", "stable_core"],
      "human_gate": {
        "required": true,
        "reason": "formal apply under Phase 3 early rollout policy"
      }
    }
  ]
}
```

No API/DbC targets (formal-only sample).

## Step B — Orchestrator STOP

Because `human_gate.required` is true at plan and target level, `solidsdd-loop` **must not** launch `solidsdd-apply-formal` yet.

Observed parent behavior (this dry-run):

- Did not edit `formal/**`
- Surfaced gate reason to the human
- Waited for explicit approval before continuing

## Step C — Human approval (simulated)

Approval message (example): “Approve formal apply for ExclusiveMemory; proceed with apply-formal and verify-formal.”

## Step D — Apply + verify (after gate)

| Skill | Action in this sample | Result |
|-------|----------------------|--------|
| `solidsdd-apply-formal` | Artifacts already present; no rewrite required | n/a (idempotent keep) |
| `solidsdd-verify-formal` | `examples/memory-formal/verify.sh` | **pass** — TLC no error (21 distinct states) |

## VerificationReport (post-gate)

```json
{
  "version": "1",
  "result": "pass",
  "checks": [
    {
      "name": "ExclusiveMemory TLC",
      "kind": "formal",
      "result": "pass",
      "detail": "No error; Inv + FinalOK after human_gate approval"
    }
  ]
}
```

## Pass criteria

| Criterion | Met? |
|-----------|------|
| Judge sets formal `apply` + `human_gate` | yes |
| Loop stops before apply-formal | yes |
| After approval, TLC verify passes | yes |
| Gate reason left visible (not thinned away) | yes |

## Resume protocol (for `solidsdd-loop`)

Documented in [../reference-src/human-gates.md](../reference-src/human-gates.md): after approval, continue from the stopped step (formal apply → verify-formal) without re-thinning the plan.
