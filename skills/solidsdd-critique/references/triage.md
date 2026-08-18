# Triage and Execution Profile

`solidsdd-run` decides, before spending any Task-class effort, how much of
its own orchestration a change actually needs. This decision is called
**Triage**; its output is an **Execution Profile**. The two terms
"Execution Profile" and "Assurance Level" refer to the same thing —
this doc and the schema use "Execution Profile."

Triage itself must stay **light**. It is a parent-only judgment step (no
Task, no subagent) that reads the change request, the current repo state,
and any explicit profile the user asked for, then writes
[triage-result.schema.json](../schemas/triage-result.schema.json). Running
Full-SDD-equivalent processing (a Task, a full Context read, a Brief draft)
just to decide Triage defeats its purpose — judge from the request text and
a quick look at what paths it touches, not from producing artifacts.

## Execution Profiles

| Profile | Name | What runs |
|---|---|---|
| L0 | `direct` | No SDD orchestration. Implement inline, run the project's own test/lint/typecheck, done. No `run-state.json`. |
| L1 | `thin` | Minimal Context/Impact note → Task `solidsdd-implement` → Task `solidsdd-verify`. Critique only on failure/uncertainty. |
| L2 | `standard` | Today's full `solidsdd-run` Sequence: Intake → Brief → Decompose → Architecture Judgment → per-item `solidsdd-loop` → Integration Verify → Knowledge Harvest. |
| L3 | `full` | Same Sequence as L2, with optional steps (cross-change consistency critique, knowledge-consistency critique, formal verification when triggered) treated as required, not recommended. |

L2 and L3 are the **same** Sequence — see `skills/solidsdd-run/SKILL.md`
"Standard / Full execution (L2/L3)". Nothing about the existing Canonical
Consolidated Slice Model changes for those two profiles.

## Change Type

| Type | Meaning | Examples |
|---|---|---|
| **Local** | Existing contracts / boundaries / architecture are untouched | UI text, CSS, logging, internal refactor, existing-function implementation tweak |
| **Contract** | An existing contract changes or is extended | API request/response shape, public method signature, DB schema, validation rule, module boundary |
| **System** | System structure, concurrency, or external boundaries change | New service, async/queue introduction, transaction boundary change, authentication change, distributed processing, architecture change |

## Complexity signals

Judge, do not count precisely: files changed, modules touched, new code
volume, new domain rules, new dependencies, new architecture components,
cross-module fan-out, inter-change-intent dependencies, ordering
requirements, migration need. More than a couple of these present at once
→ `complexity: high`; one or two localized ones → `medium`; none → `low`.

## Risk categories

Any of the following present, at any strength → treat as a **high** risk
factor. These mirror [human-gates.md](human-gates.md)'s trigger table on
purpose — Triage and the human-gate rules must never disagree about what
counts as high-stakes:

security · authentication / authorization · data integrity · financial /
billing / ledger operation · external system integration · public API
compatibility · backward compatibility · concurrency · transaction boundary
· asynchronous / distributed processing · production critical path ·
destructive operation · data migration

## Existing contract impact check

Mechanical, not judgment: does this change touch (or plausibly need to
touch) `contracts/`, `openapi/`, `*.graphql`, OCL/DbC files, formal specs,
`.solidsdd/architecture/workspace.dsl`/`invariants.yaml`, or any file that is
itself a public interface (exported API surface, public method signature)?
If yes → `contract_impact: true`. Separately: does it touch structure,
module boundaries, or dependency direction — the same trigger check
`solidsdd-architecture`'s Level 0 shortcut uses (see
[architecture-axes.md](architecture-axes.md) "When architecture changes")?
If yes → `architecture_impact: true`.

## Priority decision table

Apply in order; stop at the first row that fires:

| # | Condition | Result |
|---|---|---|
| 1 | An explicit high-risk category (above) applies | `required_minimum_profile: full` |
| 2 | Architecture / system boundary changes (`architecture_impact: true`, or `change_type: system`) | `required_minimum_profile: full` (system) or `standard` (bounded architecture delta) |
| 3 | An existing public contract changes (`contract_impact: true` on an already-published surface) | `required_minimum_profile: standard` or higher |
| 4 | DB schema or data-integrity impact | `required_minimum_profile: standard` or higher |
| 5 | `change_type: local` and risk/complexity both `low` | `required_minimum_profile: direct` or `thin` |
| 6 | Small change that still touches a contract (narrow, additive, backward-compatible extension) | `required_minimum_profile: thin` or `standard` |
| 7 | Triage cannot confidently classify the change (`uncertain: true`) | Escalate — pick the higher of any candidate profiles under consideration; never `direct` or `thin` |

**Never pick a lower profile because you are unsure.** Uncertainty is a risk
factor, not a reason to default light. When two rows could plausibly apply,
take the stricter one.

## Explicit profile + safety override

The user may ask for a profile conversationally (`--profile <x>` or
`profile: <x>` in the request text; unspecified → `auto`). Extract this
token with `scripts/solidsdd-next.sh parse-profile --text "<instruction>"`
(prefer it over ad hoc prose parsing — mechanical and consistent regardless
of who reads the instruction; see
[solidsdd-next.md](../scripts/solidsdd-next/README.md)) to get
`requested_profile`. Triage always computes `required_minimum_profile` from
the table above **independent of** what was requested, then:

```text
effective_profile = max(requested_profile, required_minimum_profile)
```

using the ordering `direct < thin < standard < full`. Record `requested`,
`required_minimum`, and `effective` as three separate fields (never collapse
them) so a caller who asked for `thin` on an authentication change can see
that it was raised to `full`, and why. A low explicit profile is never a way
to bypass this floor.

## Escalation

Any of the following, discovered **after** Triage already ran, forces a
re-triage that can only move up, never down:

- verification failure
- unexpected test failure
- contract mismatch
- unexpected dependency discovered
- architecture impact discovered
- public API impact discovered
- data integrity risk discovered
- implementation scope exceeds the initial assessment
- the agent cannot judge whether continuing at the current profile is safe

On escalation: write a new `triage-result.json` with an `escalation` block
(`from`, `to`, `trigger`, `reason`, `at`); do not overwrite or discard the
prior one's `reasons` — the new file supersedes it for `run-state.json`
purposes but the change directory keeps both for audit (e.g.
`triage-result.json` = latest, or timestamp-suffixed history, matching the
`gate-approval.json` / `gate-approvals/<iso>-<scope>.json` convention in
[human-gates.md](human-gates.md)).

**Carry forward, do not redo:** whatever the lower profile already produced
stays useful input for the higher one. An L1 run's optional Context/Impact
note already lives at the canonical `context-pack-framing.md` path (same
shape used for outer Intake/Brief Tasks — see [execution-model.md](../docs/execution-model.md)
"Context pack"), not a separate file; append the L1 attempt's outcome
(touched files, diff summary, verification result) to it and pass it into
`solidsdd-intake` / `solidsdd-brief` as prior framing instead of re-deriving
framing from nothing. Treat any code already implemented under L0/L1 as the
starting point for the relevant WorkPlan item's slice (its `solidsdd-loop`
still runs Plan/Verify in full — Implement Slice may find little left to
change, which is fine, not a shortcut; that item's own `items/<item_id>/context-pack.md`
should cite the escalation record as **Precedent to adapt**). Do re-run
whatever guarantee the higher profile requires and the lower one didn't
provide (ChangeBrief, WorkPlan, Architecture Judgment, the checkpoint
critiques the Sequence at that profile requires) — escalation upgrades
assurance, it does not retroactively grant it.

`run-state.json` upgrades from the L0 shape (none) or L1 shape (`triage` →
`thin_implementation` → `thin_verification`) to the full phase set by
initializing whichever phase the escalation lands on (usually `intake` or
`brief`) via `scripts/solidsdd-run-state.sh init` / `set-phase` — never by
hand-editing JSON.
