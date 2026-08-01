# Feedback → rule tuning

## Source of this pass

External production projects are not yet onboarded. **Pass 1** uses feedback from solid_sdd’s own evaluation corpus (proxy for early real use):

| Source | Doc |
|--------|-----|
| MVP OpenAPI + OCL | [mvp-evaluation.md](mvp-evaluation.md) |
| GraphQL / Ruby adapters | [phase2-evaluation.md](phase2-evaluation.md) |
| TLC sample | [phase3-evaluation.md](phase3-evaluation.md) |
| Formal human_gate dry-run | [phase3-gate-dryrun.md](phase3-gate-dryrun.md) |

When an external project contributes feedback, append a row under [Intake log](#intake-log) and apply or reject a tuning with rationale.

## Pass 1 findings → decisions

| ID | Feedback | Tuning |
|----|----------|--------|
| F1 | Additive API/DbC changes (mod, memory) rarely need human gates | Defaults: no gate for additive non-breaking `api`/`dbc` when confidence ≥ medium |
| F2 | Concurrent memory correctly stays `formal` **defer** until TLC path exists; with TLC sample, apply is gated | Keep formal early-rollout **always gate**; context must detect `formal/` + TLC tooling |
| F3 | Break/repair: wrong/missing precondition → `implement`, not weaken tests | Project rule + loop-retry: domain `PreconditionError` (or project equivalent), not raw `ZeroDivisionError` / bare asserts |
| F4 | Stack discovery missed GraphQL / RSpec if context only looked at OpenAPI+Vitest | `solidsdd-context` detects `graphql/`, `spec/contracts`, `formal/`, and test commands |
| F5 | Verify without `loop_action` slows orchestration | Require `loop_action` + `failure_class` on verify **fail** (already schema; now mandatory in project rule) |
| F6 | Parent thinning of ApplicationPlan is the main bias risk | Reaffirm in project rule; resume-after-gate must not strip formal |
| F7 | max retries=3 worked conceptually; same skill twice → gate | Keep max_auto_retries=3; escalate on repeated same skill (loop-retry) |
| F8 | Ruby `%` raised `ZeroDivisionError` when guard removed—tests expect domain error | OCL derive/implement: map `pre` failures to a **named domain error** |
| F9 | Phase evaluation left to the producing agent; contracts can stay thin | Dedicated `solidsdd-critique` Task after judge/apply/derive/verify; contract-weakness checklist; shared max_auto_retries=3 |

## Intake template (external projects)

```markdown
### YYYY-MM-DD — <project>
- Stack:
- What hurt:
- Proposed change (rule / axis / skill):
- Decision: accept / defer / reject
- Links:
```

## Intake log

| Date | Project | Summary | Decision |
|------|---------|---------|----------|
| 2026-08-02 | solid_sdd examples (Pass 1) | See table above | Applied to rules, axes, context, loop-retry, OCL adapter notes |
| 2026-08-02 | solid_sdd design (F9) | Adversarial critique as explicit skill | Added `solidsdd-critique`, loop integration, shared retry budget |
