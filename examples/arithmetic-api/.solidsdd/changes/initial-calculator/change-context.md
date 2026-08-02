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

| Quality | Requirement | Rationale | Verification / deferred |
|---------|-------------|-----------|-------------------------|
| Reliability / error handling | Invalid arithmetic (esp. / and rem by 0) fails with a **named domain error**, not opaque language errors | Callers and contract tests need a stable signal | Contract tests + API error channel; OCL `pre` |
| Security | N/A for this change | Auth explicitly out of scope | Deferred / out of scope |
| Performance | No special latency/throughput targets | Sample workload | N/A |
| Operability | Behaviors checkable via HTTP/API and module contracts without opaque internals | solid_sdd evaluate path | OpenAPI + OCL-derived tests |
| Compatibility | Additive sample API; no stated external clients yet | Greenfield sample | OpenAPI documents surface |
| Maintainability | Prefer UML OCL as DbC SoT; tests derived | Matches solid_sdd adapter policy | OCL + derive-tests |

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

## 7. Open questions and deferred decisions

- Remainder / division sign conventions for negatives: leave to OCL / implementation convention (e.g. JS `%`) unless a later change tightens it.
- Exact HTTP paths and error JSON shape: deferred to OpenAPI apply.

## 8. Links

- Change Context gate: `.solidsdd/changes/initial-calculator/change-context-gate.json`
- ChangeBrief: `.solidsdd/changes/initial-calculator/change-brief.json`
- WorkPlan: `.solidsdd/changes/initial-calculator/work-plan.json`
- Features: `requirements/calculator.feature`, `requirements/memory.feature`
