# Architecture depth

`solidsdd-architecture` decides how deep a given change needs to go, not
just whether it changes structure at all. Most changes stop at Level 0.
Judge depth from the WorkPlan `touches` / Brief scope actually in front of
you — do not default to a deeper level "to be safe."

| Level | Name | When | What happens |
|---|---|---|---|
| 0 | No structural change | No trigger in [architecture-axes.md](architecture-axes.md) applies | Emit `status: unchanged` directly; do not touch `workspace.dsl`/`invariants.yaml`/`architecture-reasoning.md` |
| 1 | Structural delta | Small change to an existing module's dependency, boundary, or ownership | Edit `workspace.dsl` (tag touched elements/relationships), write a short `architecture-reasoning.md` covering the specific decision, skip full Logical Decomposition |
| 2 | Logical decomposition | Responsibility/boundary/ownership genuinely needs re-deciding (e.g. a module is doing two unrelated things) | Work through Logical Decomposition (Responsibility / State Ownership / Knowledge Ownership / Change Locality — see [architecture-axes.md](architecture-axes.md)) before touching the DSL |
| 3 | Physical decomposition | The logical split from Level 2 needs a concrete new module/package/component, not just a documented boundary | Level 2, then also add the new `container`/`component` element(s) in `workspace.dsl`; Physical Module Design (directory/file layout) is a separate, later concern — do not let directory structure drive the logical decision |
| 4 | Formal architectural reasoning | Concurrency, distributed state, complex state transitions, race conditions, ordering guarantees, safety/liveness concerns | Levels 2–3 as needed, then hand off to TLA+/Alloy (`solidsdd.judge` / `ApplicationPlan`) for the state/temporal properties — Architecture states *who owns the state and where the boundary is*, not the transition semantics |

Depth is about how much reasoning and modeling a change needs, not about
which Structurizr element kind (`softwareSystem`/`container`/`component`)
gets used — a Level 1 change might still touch a `component`, and a Level 3
change might still only need one new `container`.
