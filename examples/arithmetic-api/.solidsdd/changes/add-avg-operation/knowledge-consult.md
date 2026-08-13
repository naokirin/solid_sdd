# Knowledge consult: add-avg-operation

Ran: `scripts/solidsdd-kg.sh build --root .` (nodes=35, edges=1, parse_issues=0) then `scope product.arithmetic_api`, `context <id> --budget 8k`, and `impact <id> --direction both --hops 3` for both existing knowledge nodes. `.solidsdd/kg/` and `knowledge/` were already present (scaffolded; not re-initialized by this Task). CLI (`tools/solidsdd-kg`) is available and built successfully.

`scope product.arithmetic_api` returned **no applicable policies** — expected, since no `policy`/`decision`/`invariant` nodes exist yet in this project (`knowledge/policies/`, `knowledge/decisions/` are empty). The two existing nodes are a `pattern` and a `lesson`, surfaced instead via `context`.

## Policies / decisions / invariants (Means)

No `policy` / `decision` / `invariant` nodes exist in `knowledge/` yet (both dirs contain only `.gitkeep`). Two other Means-bearing nodes are directly applicable to this change and are treated here as the equivalent framing input:

| id | type | maturity | facets | Applicability to `add-avg-operation` |
|----|------|----------|--------|----------------------------------------|
| `PAT-OPERATION-PRECONDITION-SCOPE` | pattern | canonical | decider | Directly governs the open question "does `avg` need a precondition?". States: decide each new operation's precondition scope from its own mathematically undefined/invalid input region, never by analogy/copying a sibling operation's precondition set; absence of a precondition must be a deliberate, explicit statement, not a silent omission. `avg = (a+b)/2` has no undefined native-semantics input region (denominator is the constant `2`), so per this pattern it correctly gets **no** `PreconditionError`, matching the precedent already set for `pow`. |
| `LES-CONTRACT-TESTS-MISS-HTTP-DISPATCH` | lesson | canonical | acceptance-property | Directly governs NFR4 (operability / "checkable end-to-end"). Warns that green contract/unit tests against `Calculator.avg` / `calculate()` do not prove the HTTP layer (`src/server.ts`) actually routes `op: "avg"` — a hand-maintained whitelist (`OPERATIONS` set/array) must also be updated, and this should be verified with a real HTTP-level test plus a mutation spot-check (temporarily drop `avg` from the whitelist, confirm the HTTP test alone fails, restore). |

Both nodes are `maturity: canonical`, so no downgrade to hypothesized framing is needed when citing them.

## Ubiquitous language

None. `knowledge/concepts/` is empty (only `.gitkeep`) — no `concept` nodes exist in this project yet.

## Suggested citations

For `change-brief.json` (not yet written) — cite by id rather than restating full text:

- **assumptions / constraints**: `PAT-OPERATION-PRECONDITION-SCOPE` — to ground the "no precondition for `avg`" requirement (already stated in Change Context §6 in equivalent prose; the Brief should cite the node id as the durable authority for that Means rather than re-deriving it).
- **assumptions / constraints**: `LES-CONTRACT-TESTS-MISS-HTTP-DISPATCH` — to ground NFR4's HTTP-dispatch-reachability requirement and to justify a WorkPlan item for an HTTP-level `avg` test with a mutation spot-check against the `OPERATIONS` whitelist in `src/server.ts` (mirrors what `add-power-operation` R5/verification already had to catch).

Both nodes are `maturity: canonical` (not `hypothesized`), so per the harvest-provenance convention these are citable as settled Means, not tentative assumptions requiring further confirmation.

## Gaps

- No `policy` / `decision` nodes exist yet in this project — only one `pattern` and one `lesson`. Not blocking for this change (both applicable nodes above cover the relevant Means), but noted for future harvest.
- No `concept` nodes exist yet (`knowledge/concepts/` empty). Domain terms already used across OpenAPI/OCL/Gherkin without a `concept` node, relevant to this change's contract surface: `op` (the `POST /calculate` operation-selector enum, currently `add|sub|mul|div|mod|pow`, to gain `avg`), and `PreconditionError` (the named domain-error channel used by `div`/`mod`, contrasted with the generic malformed-body 400 — exactly the distinction this change must *not* muddy for `avg`, per `PAT-OPERATION-PRECONDITION-SCOPE`). Neither has recurred across enough changes yet to clearly pass the harvest bar (stability / scope risk / low churn); flagging as a watch-item rather than a consult-time blocker. Not proposing creation here — that is `solidsdd-knowledge` harvest's job, human-gated, after this change's integration verify.
- `impact` on Brief `R*` ids was not run: `change-brief.json` for `add-avg-operation` does not exist yet (noted as "not yet written" in `change-context.md` §8), so there are no `<change_id>/R*` nodes to query yet. Re-run `impact` once the Brief exists if deeper downstream link checking is wanted.
