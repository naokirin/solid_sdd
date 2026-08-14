# Architecture Reasoning template

`architecture-reasoning.md` (`.solidsdd/changes/<change_id>/architecture-reasoning.md`)
records **why** this change's structure is the way it is. It does not
restate structure — modules, dependencies, and constraints live in
`.solidsdd/architecture/workspace.dsl` and `invariants.yaml`
(see [structurizr-dsl.md](structurizr-dsl.md)); do not duplicate them here.

Write this file only at [Architecture Depth](architecture-depth.md) Level 1
or higher (i.e. whenever `ArchitecturePlan.status` becomes `changed`). Skip
it entirely at Level 0.

Keep sections short — one or two sentences each is normal. Omit a section
that genuinely doesn't apply to this change rather than padding it.

```markdown
# Architecture Reasoning

## Change

<change_id>

## Design Problem

What is the structural problem this change needs to solve?

## Decision Drivers

Constraints, goals, or evaluation criteria this change's boundary/dependency
decision must satisfy (see [architecture-axes.md](architecture-axes.md)
Decision Drivers) — not a restatement of the Requirement. Omit when the
trigger itself is justification enough (most Level 1 deltas).

## Logical Decomposition

### Responsibility

Who is responsible for what, and why does that split make sense here?

### State Ownership

Who owns which state? (Only if this change moves or introduces ownership.)

### Knowledge Ownership

Which domain rule/knowledge is being kept in one place, and why there?

### Change Locality

What change reason does this boundary keep local, that would otherwise
spill into an unrelated module?

### Consistency Boundary

Which state must stay consistent together, and does it live in the same
boundary? (Only when this change's boundary decision hinges on a
consistency requirement.)

### Concurrency Boundary

Which boundary coordinates concurrent access, if any? States *where*, not
the transition semantics (that is TLA+/Alloy — see Role separation in
[architecture-axes.md](architecture-axes.md)). Omit when this change has no
concurrency concern.

## Boundary Decisions

Where is the boundary, and why there rather than somewhere else?

## Dependency Decisions

For each new/changed dependency: why does A depend on B, and could the
direction be reversed?

## Alternatives Considered

What other decomposition/boundary was considered and rejected, and why?

## Trade-offs

What is being given up by this decision?

## Architecture Invariants

Any invariant this change adds to or relies on in `invariants.yaml`
(reference by the same wording, don't restate structure).
```

## Relation to ADRs

A change-local decision that only matters for this change stays in
`architecture-reasoning.md`. A decision with durable, cross-change
consequences (a standing rule the project should keep honoring later)
should be promoted to an ADR when the project has one — do not treat every
`architecture-reasoning.md` as an ADR by default.
