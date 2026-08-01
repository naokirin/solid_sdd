# Coexistence with other SDD tools

solid_sdd complements—not replaces—natural-language Spec-Driven Development loops (e.g. Kiro-style: NL spec → design/implement/test).

## Ownership split

| Concern | Typical NL SDD tool | solid_sdd |
|---------|---------------------|-----------|
| Product intent, UX copy, exploratory design | Primary | Thin / `natural_only` or skip |
| HTTP/GraphQL boundary contracts | Optional / generated docs | **Primary** (OpenAPI / GraphQL SDL) |
| Module pre/post (DbC) | Rare | **Primary** (OCL → contract tests) |
| Concurrency / safety properties | Rare | **Optional formal** (TLA+/TLC), human-gated |
| “Make the feature work” coding loop | Primary implementer | `solidsdd-implement` only after contracts exist |
| Apply density (where to put contracts) | Human judgment | **`solidsdd-judge` + axes** |

## Recommended patterns

### 1. NL loop first, contracts at boundaries

1. Explore with the host SDD / agent using natural language.
2. When the HTTP or domain boundary stabilizes, run `solidsdd-judge` (or `solidsdd-loop`).
3. Keep NL specs as product docs; treat OpenAPI/OCL/TLA+ as machine-checkable SoT for those boundaries.

### 2. Contracts first for risky changes

For breaking API, money, or authz surfaces: run solid_sdd **before** broad implementation so verify catches drift early.

### 3. Do not double-own the same artifact

| If… | Then… |
|-----|-------|
| OpenAPI is SoT | Do not also maintain a conflicting hand-written “API markdown contract” as SoT |
| OCL is SoT | Do not hand-edit derived contract tests as primary |
| NL tool regenerates OpenAPI loosely | Prefer solid_sdd `apply-api` or merge carefully; verify must win |

### 4. Formal stays rare

Leave TLA+/TLC to `concurrency_safety` (or policy-marked safety-critical) paths. NL SDD tools should not be expected to author formal models.

## Conflict resolution

1. **Verify fails** → fix implementation or correct the contract via apply skills; never weaken contracts only to green the NL loop.
2. **Critique fails** (thin contracts, density bias, weak tests) → re-run the **source** solid_sdd skill (`judge` / `apply-*` / `derive-tests`); do not paper over with implement-only fixes.
3. **NL agent and solid_sdd disagree on density** → re-run `solidsdd-judge` as a subagent; do not thin the plan in the parent.
4. **Human gate** → NL automation must pause the same way `solidsdd-loop` does.

## Non-goals

- Replacing the host IDE’s agent product
- Forcing every change through formal specs
- Mandating language-native contract gems
