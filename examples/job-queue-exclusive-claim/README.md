# job-queue-exclusive-claim (evaluation sample)

Greenfield job queue: producers submit jobs, a worker pool claims and
processes them, and completed results are recorded — with a hard
guarantee that a given job is never claimed by two workers at once, even
when claim attempts race across workers that may run as separate OS
processes or separate machines.

Design-only sample: this project has no `src/` and stops before
`solidsdd-implement`. It exists to show **all four** design layers
connected for one non-trivial (concurrency-sensitive) change, without
letting any one layer absorb another's job (see the Role separation table
in [reference-src/architecture-axes.md](../../reference-src/architecture-axes.md)
and [judgment-axes.md](../../reference-src/judgment-axes.md)):

| Layer | Artifact | Answers |
|-------|----------|---------|
| Architecture (Logical) | [`.solidsdd/architecture/workspace.dsl`](.solidsdd/architecture/workspace.dsl) + [`architecture-reasoning.md`](.solidsdd/changes/establish-job-queue/architecture-reasoning.md) | Which module owns what state, and where the boundary is (`JobQueue` owns `Job`; `ClaimCoordinator` — a component of `JobQueue` — owns `ClaimState` and is the sole Concurrency Boundary; `ResultStore` owns `JobResult`, deliberately disjoint) |
| Architecture (Physical) | [`physical-design.md`](.solidsdd/changes/establish-job-queue/physical-design.md) | How the Concurrency Boundary is actually realized — an atomic conditional update on shared job storage, not a dedicated resident coordinator process, and why |
| Gherkin | [`requirements/job-queue.feature`](requirements/job-queue.feature) | What behavior is required, in Given/When/Then form (submission, exclusive claim, result retrieval) |
| DbC (OCL) | [`contracts/JobQueue.ocl`](contracts/JobQueue.ocl) | The single-call pre/post shape of each operation (`submitJob`, `claimJob`, `recordResult`, `getResult`) — deliberately **not** the cross-call exclusivity property, which OCL cannot express |
| Formal (TLA+) | [`formal/ClaimCoordinator.tla`](formal/ClaimCoordinator.tla) | The exact state/transition safety property (`AtMostOneClaimant`) that formalizes "at most one worker ever claims a given job," plus a liveness property (`EventuallyAllJobsClaimed`) |

## Why both DbC and Formal for the same operation (`claimJob`)

This is the crux of the example. `application-plan.json` explicitly splits
`claimJob`'s contract in two, because OCL and TLA+ answer different
questions about the same operation:

- **OCL** (`contracts/JobQueue.ocl`): "for one call, given the job is
  unclaimed, does it end up claimed by the caller — and if already
  claimed, does the call fail with a named error?" A single-call, sequential
  question.
- **TLA+** (`formal/ClaimCoordinator.tla`): "across every possible
  interleaving of concurrent calls from multiple workers, can two of them
  ever both succeed for the same job?" A property over *all* interleavings,
  which OCL structurally cannot express (see `contracts/JobQueue.ocl`'s
  `SCOPE NOTE` comment).

Neither layer alone answers the requirement (R2/SC1/SC2/NFR1); both are
necessary, and neither duplicates the other.

## Judge → Apply chain

`application-plan.json` targets, decided by `solidsdd-judge`
([judgment-axes.md](../../reference-src/judgment-axes.md)):

| Target | kind | status | Why |
|--------|------|--------|-----|
| `submitJob` | `dbc` | `apply` | `domain_contract` (NFR2); no HTTP/GraphQL boundary exists in this project, so `dbc` — not `api` — is the primary contract |
| `claimJob` | `dbc` | `apply` | Single-call pre/post shape only; concurrency safety explicitly deferred to the `formal` target below |
| `claimJob` (concurrency) | `formal` | `apply`, `human_gate: required` | `concurrency_safety` (NFR1); all four Phase 3 `apply` conditions hold (signal present, TLA+/TLC adapter documented and already used in this repo, scope is one shared resource, human gate set) |
| `recordResult` | `dbc` | `apply` | `domain_contract` (NFR2); no concurrency signal — `ResultStore` doesn't share `ClaimCoordinator`'s consistency boundary |
| `getResult` | `dbc` | `apply` | `domain_contract`; read-only query, disambiguates the not-yet-recorded case |

Human gates recorded in
[`gate-approvals/`](.solidsdd/changes/establish-job-queue/gate-approvals/):
one for the Architecture Model (a project's first-ever model, and
`ClaimJob` is an external-facing boundary — see
[human-gates.md](../../reference-src/human-gates.md)), one for the formal
apply (mandatory under early Phase 3 policy).

## Checker

**TLA+ / TLC** (repo default; rationale:
[../../tools/tla/README.md](../../tools/tla/README.md)).

```bash
# from repo root
tools/tla/fetch-tla2tools.sh   # requires JDK 17+
examples/job-queue-exclusive-claim/verify.sh
```

## Properties (`formal/ClaimCoordinator.tla`)

- `TypeOK` / `AtMostOneClaimant` (`Inv`): every job's set of accepted
  claimants never exceeds size 1, across the whole run (the `claims` log
  only grows — this rules out a job being claimed, released, and
  re-claimed by someone else, not just an instantaneous double-claim)
- `FinalOK`: once every job is claimed, each has *exactly* one claimant
- `EventuallyAllJobsClaimed`: liveness / no-starvation under fair
  scheduling (supplementary — NFR1 itself is a safety property)

## Working language

This project's `.solidsdd/config.yaml` sets `working_language: "ja"` —
`change-brief.json` / `nfr.json` / `work-plan.json` / `architecture-reasoning.md`
/ `physical-design.md` / `application-plan.json` prose and
`requirements/job-queue.feature`'s titles/step text are in Japanese; DSL
identifiers, JSON keys, OCL/TLA+ keywords, and Gherkin keywords stay
English, per [working-language.md](../../reference-src/working-language.md).
`report.md` / `report.html` (generated via `scripts/solidsdd-report.sh`)
are in Japanese too.

## What stops here

This sample ends after `solidsdd-apply-formal`. No `solidsdd-derive-tests`
(no contract tests generated from the OCL) and no `solidsdd-implement` (no
`src/`) — it demonstrates the four design layers connecting correctly,
not a runnable system.
