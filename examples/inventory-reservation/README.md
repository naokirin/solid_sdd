# inventory-reservation (framing example)

Non-arithmetic sample that stresses **intake → brief → decompose → critique**, including:

- AuthZ / inventory boundaries (human gate + `gate-approval.json`)
- EARS wording in ChangeBrief `in_scope` texts
- WorkPlan `covers` / Scenario `@tags` / overlapping `touches`
- Structured `nfr.json`

**Scope of this checkout:** framing and plan artifacts only—no runnable service. Use it to exercise lint, cross-change critique guidance, and gate resume protocol. Implementation remains future work (or a separate change).

## Lint

```bash
../../scripts/solidsdd-lint.sh --project-root .
```
