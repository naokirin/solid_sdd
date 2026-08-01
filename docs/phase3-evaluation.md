# Phase 3 evaluation notes (checker + sample)

## Checker decision

| Option | Outcome |
|--------|---------|
| **TLA+ / TLC** | **Selected** as default — CLI via `tla2tools.jar`, fits concurrency models, pinned fetch in `tools/tla/` |
| Apalache | Deferred (optional later) |
| Alloy | Deferred as alternate `adapter_hint` |

See [../tools/tla/README.md](../tools/tla/README.md).

## Sample: `examples/memory-formal`

Exclusive shared-memory increments (`ExclusiveMemory.tla` / `.cfg`).

| Check | Result |
|-------|--------|
| `./verify.sh` (TLC) | **pass** — "Model checking completed. No error has been found." (Clients=2, MaxAdds=2; 21 distinct states) |
| Invariants | `Inv` (TypeOK), `FinalOK` |

## VerificationReport sketch

```json
{
  "version": "1",
  "result": "pass",
  "checks": [
    {
      "name": "ExclusiveMemory TLC",
      "kind": "formal",
      "result": "pass",
      "detail": "No error; Inv + FinalOK"
    }
  ]
}
```

## Judge sketch (when enabling formal apply)

`kind=formal`, `adapter_hint=tla`, `status=apply`, `signals=["concurrency_safety"]`, `human_gate.required=true`, density `strict`.

## Remaining

- Full `solidsdd-loop` formal path with live human gate
- Optional Apalache / Alloy adapters
- Wire consuming projects without committing `tla2tools.jar`
