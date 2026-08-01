# Adversarial critique (phase quality gate)

`solidsdd-critique` is a **read-only** quality gate over another phase’s artifact. It is the solid_sdd counterpart of SpecKit-style `/clarify` / `/analyze`: a dedicated command so evaluation is **not left to the producing agent**.

## Why

If the same agent (or the same unbroken context) both produces and accepts a phase result:

- ApplicationPlans drift thin to ease implementation
- Contracts omit hard preconditions / error shapes
- Derived tests mirror weak OCL instead of challenging it
- Green VerificationReports are trusted without checking coverage

Critique must run as an **explicit Task subagent**, separate from the producer.

## Subjects and when `solidsdd-loop` must call it

| `subject` | After | Producer skill(s) |
|-----------|-------|-------------------|
| `application_plan` | `solidsdd-judge` | judge |
| `api_contracts` | `solidsdd-apply-api` (if any api apply) | apply-api |
| `dbc_contracts` | `solidsdd-apply-dbc` (if any dbc apply) | apply-dbc |
| `derived_tests` | `solidsdd-derive-tests` | derive-tests |
| `formal_specs` | `solidsdd-apply-formal` | apply-formal |
| `verification_report` | `solidsdd-verify` / `solidsdd-verify-formal` | verify* |
| `isolation` | Parent detects inline execution of a subagent-required skill | — |

Skip a subject only when that producer step did not run in this loop iteration.

## Stance

- Assume the artifact may be **too weak**; try to falsify adequacy
- Prefer **contract_gap / thin_contract** findings over silence
- Do **not** edit artifacts; report only
- Do **not** rubber-stamp because downstream implement would be harder

## Contract-weakness checklist (required)

Raise at least `major` (usually `thin_contract` or `missing_precondition`) when any apply:

| Check | Examples |
|-------|----------|
| Empty or vacuous constraints | `pre: true`, empty `post`, SDL with no error fields where failures exist |
| Missing domain errors | Division / empty / auth failures only as language builtins; no named precondition error |
| Density vs signals | `money_boundary` / `breaking_change` / `concurrency_safety` with `thin` or unjustified `skip`/`defer` |
| Happy-path-only API | No 4xx/error union for documented failure modes |
| Weak derived tests | Assert only “does not throw”; no boundary / precondition cases from OCL |
| Plan thinning | Rationale cites implementation cost or “keep tests green” |
| Formal gap | Shared mutable multi-client protocol with silent omit of `formal` (no `defer` rationale) |
| Soft verify | Required checks `skipped` without tooling reason; pass with zero contract tests when OCL exists |

`minor` is for polish (naming, comment clarity) that does not reduce checkability.

## Result rules

- Any `blocker` or `major` → `result: fail`, set `loop_action` + `suggested_next_skills`
- Only `minor` (or empty findings) → `result: pass` (minors may still be listed)
- Map producers: plan → `solidsdd-judge`; API → `solidsdd-apply-api`; OCL → `solidsdd-apply-dbc` (+ `derive-tests` if tests already exist); tests → `solidsdd-derive-tests` or `apply-dbc`; formal → `solidsdd-apply-formal`; verify softness → re-`verify` or fix upstream contracts

## Isolation violations

If the parent ran a subagent-required skill inline:

1. Emit CritiqueReport `subject: isolation`, `category: isolation_violation`, severity `blocker`
2. `loop_action: retry`, suggest re-running that skill as a **new Task**
3. Count toward the shared auto-retry budget (see [loop-retry.md](loop-retry.md))
