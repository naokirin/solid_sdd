# Adversarial critique (phase quality gate)

`solidsdd-critique` is a **read-only** quality gate over another phase’s artifact. It is the solid_sdd counterpart of SpecKit-style `/clarify` / `/analyze`: a dedicated command so evaluation is **not left to the producing agent**.

## Why

If the same agent (or the same unbroken context) both produces and accepts a phase result:

- WorkPlans pack multiple acceptance criteria into one item or use unverifiable prose
- ApplicationPlans drift thin to ease implementation
- Contracts omit hard preconditions / failure paths
- Derived tests ignore existing `pre` clauses
- Green VerificationReports hide zero coverage

Critique must run as an **explicit Task subagent**, separate from the producer.

## Severity calibration (loop must progress)

Critique is adversarial, but **must not fail the loop for polish**. Default density for additive work is `standard`. Calibrate as follows:

| Severity | When | Loop effect |
|----------|------|-------------|
| `blocker` | Isolation violation; artifact missing when the phase claimed to produce it | `fail` |
| `major` | **Checkability is lost** for this density (see major table below) | `fail` → retry |
| `minor` | Stronger typing, more edges, clearer naming, nicer error unions | `pass` (list only) |

**Bias toward `pass` with `minor`s** when the artifact is already machine-checkable at `standard` density. Prefer over-reporting as **minor**, not as **major**.

Do **not** raise `major` solely because a consuming example or production sample could be stricter. Escalation to `major` needs a concrete checkability hole.

### `major` only when checkability is lost

| Check | `major` examples | **Not** `major` (use `minor` or omit) |
|-------|------------------|--------------------------------------|
| Vacuous constraints | `pre: true` / empty `post` when density is `standard`+ and the operation has known failure or result meaning | Type-echo invariants (`oclIsTypeOf` on an already-typed attribute); missing IEEE/NaN guards |
| Missing precondition | Known failure mode (div/mod by zero, empty required input) with **no** `pre` / no API error path at all | OCL that has `pre` but does not name `PreconditionError` in the `.ocl` text (error **class** is an implement/adapter concern; project rule covers runtime) |
| Happy-path-only API | HTTP/GraphQL operation with documented failures but **no** 4xx / error channel whatsoever | Undifferentiated `{ error: string }`; GraphQL errors only in prose while tests/impl already lock a code; undeclared 404/500 catch-alls |
| Weak derived tests | OCL/`pre` exists but tests never exercise violation; suite is only “does not throw” / empty | Few integer cases; language `%` as oracle when OCL maps to that operator; missing fractional edges |
| Density vs signals | `money_boundary` / `breaking_change` / `concurrency_safety` with `thin` or silent `skip` (no `defer` rationale) | `standard` sample without money/authz signals |
| Plan thinning | Rationale cites implementation cost or “keep tests green” to lower density | Brief rationales that still cite axes |
| Formal gap (plan) | Shared mutable multi-client protocol omitted with neither `formal` nor `defer`+reason | Formal model that checks a documented invariant set for a smoke sample |
| Formal specs | CFG/spec checks **nothing** meaningful (no invariant/property), or claims exclusive/safety but has **zero** related invariant | Missing liveness/WF; toy `Clients=2`; TypeOK+domain invariant without a separate named mutex lemma |
| Soft verify | Required checks `skipped` without tooling reason; `pass` with **zero** contract tests while OCL files exist | Single skipped optional adapter; green run with a non-empty contract suite |
| WorkPlan slice | Item with **uncheckable** acceptance prose; **two+** independent ACs in one item; dependency **cycle**; whole requirement not covered by items/`acceptance_of_whole` | Preferring fewer items when each AC is still checkable; brief intents that still name the check |

### Named domain errors

- **Runtime / tests / implement**: prefer named domain errors (e.g. `PreconditionError`) — see project rule and loop-retry.
- **Critique of OCL text**: do **not** `fail` only because the `.ocl` file does not spell the exception type. Fail if the **`pre` itself is missing** while failures are in scope.

## Subjects and when orchestrators must call it

| `subject` | After | Producer skill(s) | Orchestrator |
|-----------|-------|-------------------|--------------|
| `work_plan` | `solidsdd-decompose` | decompose | `solidsdd-run` |
| `application_plan` | `solidsdd-judge` | judge | `solidsdd-loop` |
| `api_contracts` | `solidsdd-apply-api` (if any api apply) | apply-api | `solidsdd-loop` |
| `dbc_contracts` | `solidsdd-apply-dbc` (if any dbc apply) | apply-dbc | `solidsdd-loop` |
| `derived_tests` | `solidsdd-derive-tests` | derive-tests | `solidsdd-loop` |
| `formal_specs` | `solidsdd-apply-formal` | apply-formal | `solidsdd-loop` |
| `verification_report` | `solidsdd-verify` / `solidsdd-verify-formal` | verify* | loop; also **run** after integration verify |
| `isolation` | Parent detects inline execution of a subagent-required skill | — | loop or run |

Skip a subject only when that producer step did not run in this orchestrator iteration.

## Stance

- Try to falsify adequacy, then **classify severity honestly**
- Prefer listing thinness as `minor` when checkability remains
- Do **not** edit artifacts; report only
- Do **not** fail to force “perfect” contracts; fail only for the major table above
- Do **not** rubber-stamp empty/`pre: true` contracts as pass

## Result rules

- Any `blocker` or `major` → `result: fail`, set `loop_action` + `suggested_next_skills`
- Only `minor` (or empty findings) → `result: pass` (minors may still be listed)
- Map producers: work plan → `solidsdd-decompose`; plan → `solidsdd-judge`; API → `solidsdd-apply-api`; OCL → `solidsdd-apply-dbc` (± `derive-tests`); tests → `solidsdd-derive-tests` or `apply-dbc`; formal → `solidsdd-apply-formal`; verify softness → re-`verify` or fix upstream contracts

## Isolation violations

If the parent ran a subagent-required skill inline:

1. Emit CritiqueReport `subject: isolation`, `category: isolation_violation`, severity `blocker`
2. `loop_action: retry`, suggest re-running that skill as a **new Task**
3. Count toward the shared auto-retry budget (see [loop-retry.md](loop-retry.md))
