# Adversarial critique (phase quality gate)

`solidsdd-critique` is a **read-only** quality gate over another phase’s artifact. It is the solid_sdd counterpart of SpecKit-style `/clarify` / `/analyze`: a dedicated command so evaluation is **not left to the producing agent**.

## Why

If the same agent (or the same unbroken context) both produces and accepts a phase result:

- Change Contexts omit NFR/tech rationale or required headings
- ChangeBriefs omit in/out of scope or leave blocking questions unmarked
- WorkPlans pack multiple acceptance criteria into one item, use unverifiable prose, or omit Gherkin Scenario structure
- ApplicationPlans drift thin to ease implementation
- Contracts omit hard preconditions / failure paths
- Derived tests ignore existing `pre` clauses
- Green VerificationReports hide zero coverage

## Checkpoint Reviews & Failure-Driven Critique (cost-reduction-plan.md)

Per [cost-reduction-plan.md](../docs/cost-reduction-plan.md), critique is shifted from per-artifact micro-evaluations to **checkpoint reviews** and **failure-driven diagnosis**:
1. **Checkpoint Reviews**: Critique is executed at major quality boundaries:
   - **Specification Review** (`change_context`, `change_brief`)
   - **WorkPlan Review** (`work_plan`)
   - **Integration Review** (`verification_report` after whole-system verify)
2. **Failure-Driven Critique**: Intermediate artifact critiques (e.g. `critique(application_plan)`, `critique(api_contracts)`, `critique(dbc_contracts)`) are omitted in normal green paths. Full Critique / Diagnosis subagents are launched **when a verification failure or isolation retry occurs** to identify the root cause and guide recovery.

Critique must run as an **explicit Task subagent**, separate from the producer. Finding `detail` / rationale strings use the project **working language** ([working-language.md](working-language.md)); JSON keys and enum tokens stay English.

## Deterministic lint first (required)

Before LLM review, run **`scripts/solidsdd-lint.sh`** against the consuming project (documented in solid_sdd `scripts/solidsdd-lint/README.md`; skill copy: [solidsdd-lint.md](solidsdd-lint.md) when installed via sync). Import lint findings into the CritiqueReport (`blocker`/`major`/`minor` as emitted). Lint owns: schema shape, `change_id` match, `depends_on` cycles, Gherkin shape, Brief id coverage via `covers` / Scenario tags, ambiguity lexicon hits.

The LLM pass then judges **adequacy** (thin contracts, missing `pre`, density vs signals, whether a cover is meaningful)—not whether coverage ids exist. Do **not** skip lint when the solid_sdd checkout is available; if the script cannot run (`tooling`), record a `minor` or `major` finding with category `other` and reason, and still complete LLM review when possible.

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
| Change Context framing | Required headings missing; §4 NFR or §5 tech selection empty/hand-wavy when demand or repo stack implies choices; decisions with neither alternatives nor rationale; missing `change-context-gate.json`; gate triggers fire (material `agent_default` tech, stack conflict, new security/money NFR, blocking §7) but `human_gate.required: false` | Wording polish; extra background prose; gate `false` when initial instruction already settled decisions |
| ChangeBrief scope | Empty/missing `in_scope` or `out_of_scope`; contradictory in vs out; `success_criteria` only slogans with no observable outcome; blocking `open_questions` with no `human_gate` / low confidence; bare `string[]` scope lists (schema/lint) | Brief wording polish; extra background prose |
| Vacuous constraints | `pre: true` / empty `post` when density is `standard`+ and the operation has known failure or result meaning | Type-echo invariants (`oclIsTypeOf` on an already-typed attribute); missing IEEE/NaN guards |
| Missing precondition | Known failure mode (div/mod by zero, empty required input) with **no** `pre` / no API error path at all | OCL that has `pre` but does not name `PreconditionError` in the `.ocl` text (error **class** is an implement/adapter concern; project rule covers runtime) |
| Happy-path-only API | HTTP/GraphQL operation with documented failures but **no** 4xx / error channel whatsoever | Undifferentiated `{ error: string }`; GraphQL errors only in prose while tests/impl already lock a code; undeclared 404/500 catch-alls |
| Weak derived tests | OCL/`pre` exists but tests never exercise violation; suite is only “does not throw” / empty | Few integer cases; language `%` as oracle when OCL maps to that operator; missing fractional edges |
| Density vs signals | `money_boundary` / `breaking_change` / `concurrency_safety` with `thin` or silent `skip` (no `defer` rationale) | `standard` sample without money/authz signals |
| Plan thinning | Rationale cites implementation cost or “keep tests green” to lower density | Brief rationales that still cite axes |
| Formal gap (plan) | Shared mutable multi-client protocol omitted with neither `formal` nor `defer`+reason | Formal model that checks a documented invariant set for a smoke sample |
| Formal specs | CFG/spec checks **nothing** meaningful (no invariant/property), or claims exclusive/safety but has **zero** related invariant | Missing liveness/WF; toy `Clients=2`; TypeOK+domain invariant without a separate named mutex lemma |
| Knowledge harvest | Durable candidate is a pasted Brief/Scenario; gate false while candidates non-empty; silent duplicate of active knowledge; tautology / domain axiom with no choice boundary; `rationale` omits why this change harvested the candidate | Empty harvest; wording polish on a real policy draft; skip with `skipped_reasons` for trivial restatement |
| Soft verify | Required checks `skipped` without tooling reason; `pass` with **zero** contract tests while OCL files exist | Redocly/npx unavailable → API lint `skipped` with reason; single skipped optional adapter; green run with a non-empty contract suite |
| WorkPlan slice | Item with **uncheckable** acceptance prose; **no Gherkin** Given/When/Then when a Scenario could express the check; **two+** independent Scenarios in one item; dependency **cycle**; ChangeBrief `in_scope` / `success_criteria` ids not in any `item.covers`; Scenario tags missing those ids; items that `covers` Brief `out_of_scope` | Preferring fewer items when each Scenario is still checkable; property-level wording vs concrete Examples; writing step prose in the working language while keeping English keywords ([working-language.md](working-language.md)). **Existence** of id coverage is primarily `scripts/solidsdd-lint.sh`; critique focuses on whether the cover is *adequate*. Greenfield smell: many `ready` items share intersecting `touches` with empty `depends_on` → **minor** (suggest foundation `depends_on` / narrow touches; not major if Scenarios remain checkable) |
| Scope drift | WorkPlan / ApplicationPlan invents features listed in Brief `out_of_scope`, or drops Brief `in_scope` without rationale | Naming differences that still match Brief intent |

### Named domain errors

- **Runtime / tests / implement**: prefer named domain errors (e.g. `PreconditionError`) — see project rule and loop-retry.
- **Critique of OCL text**: do **not** `fail` only because the `.ocl` file does not spell the exception type. Fail if the **`pre` itself is missing** while failures are in scope.

## Subjects and when orchestrators must call it

| `subject` | After | Producer skill(s) | Orchestrator |
|-----------|-------|-------------------|--------------|
| `change_context` | `solidsdd-intake` | intake | `solidsdd-run` |
| `change_brief` | `solidsdd-brief` | brief | `solidsdd-run` |
| `work_plan` | `solidsdd-decompose` | decompose | `solidsdd-run` |
| `application_plan` | `solidsdd-judge` | judge | `solidsdd-loop` |
| `api_contracts` | `solidsdd-apply-api` (if any api apply) | apply-api | `solidsdd-loop` |
| `dbc_contracts` | `solidsdd-apply-dbc` (if any dbc apply) | apply-dbc | `solidsdd-loop` |
| `derived_tests` | `solidsdd-derive-tests` | derive-tests | `solidsdd-loop` |
| `formal_specs` | `solidsdd-apply-formal` | apply-formal | `solidsdd-loop` |
| `verification_report` | `solidsdd-verify` / `solidsdd-verify-formal` | verify* | loop; also **run** after integration verify |
| `isolation` | Parent detects inline execution of a subagent-required skill | — | loop or run |
| `cross_change_consistency` | After `work_plan` critique when prior Features / prior changes exist | — | `solidsdd-run` (optional but recommended on follow-on changes) |
| `knowledge_harvest` | `solidsdd-knowledge` harvest (before human gate / done) | knowledge | `solidsdd-run` (recommended when candidates exist) |
| `knowledge_consistency` | After consult + Context/Brief exist when consult cites confirmed/canonical knowledge | — | `solidsdd-run` (recommended when consult is non-empty) |

Skip a subject only when that producer step did not run in this orchestrator iteration.

### `knowledge_consistency` (major examples)

| Check | `major` | Not major |
|-------|---------|-----------|
| Context/Brief contradicts a **confirmed** or **canonical** consulted policy without assumption/gate | Silent override of AuthZ / Means / ADR | Explicit Brief assumption + gate; `hypothesized` knowledge treated as soft |
| Contracts / WorkPlan implement the opposite of a cited canonical invariant | Drift from durable knowledge | Rename / restate that still obeys the norm |
| Consult pack ignored while inventing conflicting Means in §6 | Framing reinvents settled policy | Citing policy ids and refining scope |
| Brief/Gherkin uses domain terms with no consulted `concept` / vocabulary gap unlisted | Silent vocabulary reinvention when canonical concepts exist | Explicit gap in consult; `hypothesized` concept as Brief assumption |
| Concept body duplicates OpenAPI/OCL paragraph | Living contract copy in knowledge | Short definition + schema/type pointer only |

Prefer **Task** critique with this subject after Brief (or after work_plan) when `knowledge-consult.md` lists applicable confirmed/canonical nodes.

### `knowledge_harvest` (major examples)

| Check | `major` | Not major |
|-------|---------|-----------|
| Living-PRD leakage | Candidate body is essentially a Brief `in_scope` item or full Scenario pasted as “policy” | Short restatement that points at Brief ids |
| One-off tech as policy | Candidate is a Change Context §5 stack pick (language/API/persistence for this repo) with no reusable Means | Means/criterion from §6 (e.g. authz stance) correctly harvested |
| Missing universality | Candidate is clearly change-ephemeral (sample path, one-off id) with no rationale for reuse | Conservative empty candidate list |
| Missing candidacy reason | `rationale` restates universality alone (or is empty/hand-wavy) with **no** extraction provenance from this change and **no** non-obvious bound — human cannot tell why it was proposed | Rationale cites Grill Q / Brief Means / Context §6 / existing POL extension (or similar) plus reuse and non-obvious boundary |
| Trivial / tautological | Candidate restates a domain axiom or “do it correctly” with **no** non-obvious choice, exception, or boundary (and `rationale` does not explain non-triviality) | Skip via `skipped_reasons`; policy that fixes a repeated AuthZ/error/verification boundary |
| Duplicate without linkage | Same concept/policy already exists and candidate does not `supersedes` / merge / skip | Near-duplicate flagged for human merge |
| Concept without vocabulary facet | `type: concept` candidate omits `facets: ["vocabulary"]` | Policy/decision with incidental term mention |
| Means as concept | Candidate is ADR/AuthZ bound but typed `concept` with no term-definition role | Correct `policy` / `decision` / `invariant` typing |
| Gate omitted | `candidates.length >= 1` but `human_gate.required: false` | Empty candidates, `required: false` |

Prefer **Task** critique with this subject after harvest emit and **before** the knowledge human gate.

### `cross_change_consistency` (major examples)

| Check | `major` | Not major |
|-------|---------|-----------|
| New Brief `in_scope` contradicts an existing Scenario that remains in force without Brief/assumption saying it changes | Silent rewrite of prior acceptance | Explicit breaking note in Brief + gate |
| Implementation / WorkPlan pulls in prior change’s `out_of_scope` (e.g. auth when previously excluded and still excluded) | Scope drift across changes | New change that deliberately opens that scope in its own Brief |
| Active Brief `out_of_scope` conflicts with newly added Scenario tags/`covers` | Items covering `X*` or implementing excluded themes | Renames that still match intent |

Prefer **Task** critique with this subject after decompose on iterative products; intake should list prior Features / prior `out_of_scope` under Context §2 or §8.

## Stance

- Try to falsify adequacy, then **classify severity honestly**
- Prefer listing thinness as `minor` when checkability remains
- Do **not** edit artifacts; report only
- Do **not** fail to force “perfect” contracts; fail only for the major table above
- Do **not** rubber-stamp empty/`pre: true` contracts as pass

## Result rules

- Any `blocker` or `major` → `result: fail`, set `loop_action` + `suggested_next_skills`
- Only `minor` (or empty findings) → `result: pass` (minors may still be listed)
- Map producers: change context → `solidsdd-intake`; change brief → `solidsdd-brief`; work plan → `solidsdd-decompose`; plan → `solidsdd-judge`; API → `solidsdd-apply-api`; OCL → `solidsdd-apply-dbc` (± `derive-tests`); tests → `solidsdd-derive-tests` or `apply-dbc`; formal → `solidsdd-apply-formal`; verify softness → re-`verify` or fix upstream contracts; scope drift → `solidsdd-brief` and/or `solidsdd-decompose`; framing/NFR/tech gaps → `solidsdd-intake`; knowledge harvest → `solidsdd-knowledge`

## Isolation violations

If the parent ran a subagent-required skill inline:

1. Emit CritiqueReport `subject: isolation`, `category: isolation_violation`, severity `blocker`
2. `loop_action: retry`, suggest re-running that skill as a **new Task**
3. Count toward the shared auto-retry budget (see [loop-retry.md](loop-retry.md))
