# memory-formal (evaluation sample)

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

- Judge: `kind=formal`, `adapter_hint=tla`, `status=apply` + **human_gate**
- Apply: `solidsdd-apply-formal`
- Verify: `solidsdd-verify-formal` → equivalent to `./verify.sh` in this directory

## Architecture → BDD → TLA+ (concurrency example)

`.solidsdd/changes/establish-exclusive-memory-architecture/` adds the
Architecture layer above this formal model, demonstrating how the three
layers connect for a concurrency-sensitive resource — without letting any
one layer absorb another's job (see the Role separation table in
[reference-src/architecture-axes.md](../../reference-src/architecture-axes.md)):

| Layer | Artifact | Answers |
|-------|----------|---------|
| Architecture | [`.solidsdd/architecture/workspace.dsl`](.solidsdd/architecture/workspace.dsl) + [`architecture-reasoning.md`](.solidsdd/changes/establish-exclusive-memory-architecture/architecture-reasoning.md) | Which module owns `mem`, and where the boundary is (`MemoryRegister` owns it; `Client` depends on its acquire/add/release surface) |
| BDD | [`requirements/exclusive-memory.feature`](requirements/exclusive-memory.feature) | What behavior is required, in Given/When/Then form |
| TLA+ | [`formal/ExclusiveMemory.tla`](formal/ExclusiveMemory.tla) | The exact state/transition property (`TypeOK`, `FinalOK`) that formalizes mutual exclusion and no lost updates |

The formal model (`.tla`/`.cfg`) is unchanged by this addition — only the
Architecture layer and a Gherkin restatement of its behavior were added on
top of it. Validate the Architecture Model with
`scripts/solidsdd-architecture.sh validate --project-root examples/memory-formal`.
