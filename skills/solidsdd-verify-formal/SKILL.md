---
name: solidsdd-verify-formal
description: >-
  Run formal verification (model check / analyze) for solid_sdd Phase 3.
  When called from solidsdd-loop, must run as an explicit Task subagent. Emits
  VerificationReport entries; does not weaken specs to force a pass.
license: MIT
---

# solidsdd.verify.formal

## Execution

**subagent required** when invoked from `solidsdd.loop`. Parent must use Task. Solo user invocation may run in the current agent.

## Purpose

Check formal specs and report pass/fail without modifying artifacts.

## References

- [formal-adapter.md](references/formal-adapter.md)
- [verification-report.schema.json](references/verification-report.schema.json)
- [loop-retry.md](references/loop-retry.md)

## Constraints

- Do not modify formal specs, API contracts, OCL, tests, or implementation to force green
- If the checker is not installed, fail with `failure_class: tooling` and `loop_action: stop` or `human_gate`
- Report only

## Steps

1. Locate formal artifacts (`formal/**` or plan locations).
2. Run project-documented checker, or report tooling missing.
3. Emit VerificationReport (`checks[].kind` may be `other` until a `formal` kind is added).
4. On fail, set `suggested_next_skills`, `loop_action`, `failure_class` per [loop-retry.md](references/loop-retry.md).

## Success criteria

- Each formal check is listed with pass/fail/skipped
- Failures are actionable for loop or human gate
