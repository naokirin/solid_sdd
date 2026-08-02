# memory-formal (Phase 3 evaluation sample)

Minimal TLA+ model of **exclusive add** to a shared memory register, checked with TLC.  
arithmetic-api Memory (OCL) assumes a single thread; this sample targets `concurrency_safety`.

## Checker

**TLA+ / TLC** (repo default; rationale: [../../tools/tla/README.md](../../tools/tla/README.md)).

## Artifacts

| Kind | Path |
|------|------|
| TLA+ | `formal/ExclusiveMemory.tla` |
| TLC config | `formal/ExclusiveMemory.cfg` |

## Setup

```bash
# from repo root
tools/tla/fetch-tla2tools.sh   # requires JDK 17+
./verify.sh
```

## Properties

- `Inv` / `TypeOK`: memory bounds and owner / remaining types
- `FinalOK`: after all clients finish, `mem = Clients * MaxAdds`

## solid_sdd

- Judge: `kind=formal`, `adapter_hint=tla`, `status=apply` + **human_gate** (early Phase 3)
- Apply: `solidsdd-apply-formal`
- Verify: `solidsdd-verify-formal` → equivalent to `./verify.sh` in this directory
