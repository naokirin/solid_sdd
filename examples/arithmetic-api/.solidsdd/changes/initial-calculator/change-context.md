# Change context: initial-calculator

## 1. Demand and problem

Clients need a small arithmetic calculator service they can call over HTTP: the usual binary operations plus remainder, with clear failure when a divisor is zero, and a simple single-slot memory (clear / recall / add / subtract) starting at zero. Opaque language/runtime errors are not acceptable for those invalid uses.

## 2. Drivers and constraints (from stakeholders / environment)

- Evaluation / sample service for solid_sdd (contracts must be machine-checkable).
- No product auth, multi-tenant memory, history, or persistence requirements.
- Prefer reusing an existing TypeScript HTTP sample layout when present.

## 3. Functional intent (summary)

- Binary ops: add, subtract, multiply, divide, remainder.
- Named domain error on division/remainder by zero.
- Single in-process memory slot: initial 0, clear, recall, add-to-memory, subtract-from-memory.
- Detail and acceptance properties live in ChangeBrief + Gherkin; this section stays a summary.

## 4. Non-functional requirements

Projection of `nfr.json` (SoT). Do not edit this table without updating `nfr.json`.

| Id | Quality | Status | Requirement | Rationale | Threshold / measurement |
|----|---------|--------|-------------|-----------|-------------------------|
| NFR1 | reliability | in_scope | Named domain error on invalid arithmetic (esp. / and rem by 0) | Stable signal for callers/tests | Domain error always; Vitest + OpenAPI + OCL `pre` |
| NFR2 | security | out_of_scope | N/A — auth out of scope | Explicitly excluded | — |
| NFR3 | performance | out_of_scope | N/A — no latency/throughput targets | Sample workload | — |
| NFR4 | operability | in_scope | Checkable HTTP/API + module contracts | solid_sdd evaluate path | OpenAPI + contract tests present/passing |
| NFR5 | compatibility | in_scope | Additive sample API documented in OpenAPI | Greenfield sample | OpenAPI structural lint when tooling available |
| NFR6 | maintainability | in_scope | UML OCL SoT; tests derived | solid_sdd adapter policy | `contracts/**/*.ocl` + derived Vitest |

## 5. Technology selection

| Decision | Choice | Alternatives considered | Rationale | Source |
|----------|--------|-------------------------|-----------|--------|
| Language / runtime | TypeScript / Node | Ruby-only sample, Go, etc. | Existing arithmetic-api evaluation stack; Vitest contracts | `repo_existing` |
| API style | HTTP + OpenAPI 3.x | GraphQL SDL, Protobuf | Sample already OpenAPI-oriented; HTTP boundary easy to lint | `repo_existing` + `agent_default` |
| Persistence | None (in-process memory) | DB-backed memory | Out of scope; single-slot in-process is enough | `user` (scope) |
| Module contracts | UML OCL → Vitest contract tests | Language-native contracts gem/keywords | solid_sdd default DbC path; no gem required | `agent_default` (solid_sdd policy) |
| Formal methods | Not applied this change | TLA+ for memory concurrency | Single-thread memory assumption; concurrency_safety not in demand | `agent_default` |

## 6. Key judgments and trade-offs

- Treat “checkable HTTP + module contracts” as a success criterion, but leave **density / adapter apply** to `solidsdd-judge` (do not over-specify OpenAPI field lists here).
- Prefer **named domain errors** over raw `ZeroDivisionError` so API and tests share one failure vocabulary.
- Exclude auth, multi-user memory, history, and durable storage to keep the sample bounded.
- Working language: en (from sample / default)

## 7. Open questions and deferred decisions

- Remainder / division sign conventions for negatives: leave to OCL / implementation convention (e.g. JS `%`) unless a later change tightens it.
- Exact HTTP paths and error JSON shape: deferred to OpenAPI apply.

## 8. Links

- NFR SoT: `.solidsdd/changes/initial-calculator/nfr.json`
- Change Context gate: `.solidsdd/changes/initial-calculator/change-context-gate.json`
- ChangeBrief: `.solidsdd/changes/initial-calculator/change-brief.json`
- WorkPlan: `.solidsdd/changes/initial-calculator/work-plan.json`
- Features: `requirements/calculator.feature`, `requirements/memory.feature`
