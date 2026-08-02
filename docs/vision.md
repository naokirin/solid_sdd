# Vision

## Background

The direction laid out in [Agile Lab’s SDD overview](https://www.agilelab.jp/index.php/2025/09/15/sdd/)—treating specs as first-class artifacts and aligning early with formal-leaning, machine-readable specs—matches this project’s problem framing.

Representative techniques and benefits from that article map as follows.

| Element in the article | Reading in this project |
|------------------------|-------------------------|
| Formal specification languages | Deep pre-implementation checking. Valuable but heavy. Deferred for MVP |
| API-spec-driven development | Contracts at system boundaries. Broad applicability; automation-friendly |
| Design by Contract (DbC) | Module-level pre/post/invariants. Verification close to the implementation |
| Earlier defect detection | **Natural language alone is weak**. Machine-readable specs plus checks make it work |
| Effective in complex domains | Scope must be explicit. Technique choice and density judgment are essential |

Typical SDD write-ups almost never cover:

1. **Technique selection** (what to put where, at what granularity, on which technology)
2. **How to apply this in a real development workflow**
3. **Connection to AI automation (loop engineering)**

## Current gaps

### Tooling

Mainstream SDD tools such as Kiro focus on natural-language spec → design / implementation / test loops. They rarely support formal specs, consistent API-contract checking, or DbC application and verification.

### Stack dependence of contracts

API and module contracts depend heavily on the tech stack: OpenAPI / GraphQL SDL / Protobuf, language-level contracts, asserts, type systems, and so on. A general mechanism must **abstract the stack while materializing via concrete adapters**.

### Limits of human application judgment

Even with a mechanism, asking people to decide “OpenAPI here,” “DbC here,” “formal here” for every change does not scale with AI-driven development volume and speed.

We therefore need:

- Systematizing application judgment itself
- An operating mode where post-application checks and feedback mostly run without people in the loop

Human involvement should concentrate on exceptions, policy changes, and accepting risk.

### Weak requirement structure

Free-form natural language as the only requirement input leaves agents to invent missing Given/When/Then structure mid-loop. Requirements need a **ChangeBrief** (goals / in / out of scope) plus **property-level Gherkin** before contract judgment—without turning those formats into perpetual product documentation or an executable test SoT.

## Goals

**Generally, make “machine-readable-spec application judgment → materialization → verification → feedback” executable as rules and skills.**

More specifically:

1. **Make the scope of each specification technique explicit**  
   Distinguish NL-only SDD from structured requirements (Gherkin), API contracts / DbC (and later formal specs), with conditions for when each pays off encoded in the system.
2. **Make selection reproducible**  
   Decide application density from axes such as risk, boundaries, and change frequency (not tacit human judgment).
3. **Use the same skills manually or automatically**  
   Users can invoke phase skills; agents can run the same skills inside a loop.
4. **Absorb stack dependence in adapters**  
   Separate the abstraction “there is a contract” from the concrete “write it like this in OpenAPI 3.x.”
5. **Evaluate only when the end-state pieces connect**  
   Success is judged on a connected judgment → apply → verify path, not isolated feature demos.
6. **Structure requirements without over-owning docs**  
   Use a ChangeBrief for scope (in/out), property-level Gherkin for acceptance, and machine-checkable contracts as **authority for the active change**—not everlasting living documents people maintain for reading.

## What machine-checkable artifacts are for

solid_sdd emits structured artifacts (ChangeBrief, Gherkin, OpenAPI, OCL, formal specs, derived tests) so agents can:

1. **Reduce silent omissions** via constrained formats
2. **Check implementation mechanically** against those formats
3. **Return to an explicit premise** (ChangeBrief) when later judgment is ambiguous

They are **not** primarily meant as long-lived human documentation. A snapshot of “how this change was judged and specified” is valuable as history; continuous editorial ownership of every past contract as product docs is not a goal. Human-readable projections (Markdown / HTML) may be added later as optional skills without changing loop authority.

**Contract reuse is situational.** Reusing contracts from an actively developed line of work is healthy. Blindly reusing poorly maintained contracts from a dormant project (e.g. a year-old abandoned slice) is usually harmful. The toolkit does **not** decide reuse policy for every repo—consuming projects and humans judge fitness for the current change (`solidsdd-context` / gates when stale or conflicting).

## Selection axes (draft)

Initial axes the system uses instead of ad-hoc human judgment.

| Nature of the target | Natural fit | Status |
|----------------------|-------------|--------|
| Change premise (goals, in/out of scope) | ChangeBrief | In scope |
| Requirement intake / acceptance structure | Property-level Gherkin Features / Scenarios | In scope |
| System boundary, I/O, compatibility | API specs (OpenAPI, etc.) | In scope |
| Module I/O invariants and failure conditions | DbC (OCL→contract tests) | In scope |
| Concurrency, distribution, faults, state explosion | Formal specs (TLA+ / Alloy, etc.) | Optional (Phase 3) |
| Deep domain-rule consistency | Formal specs or constraint-solver leaning | Optional / partial via DbC |
| High churn, exploratory | Thin Brief + thin Gherkin + thin contracts / `natural_only` | In scope (avoid over-formalizing) |

The principle is not “formalize everything,” but **set application density from risk and change frequency**.

## Non-goals (for now)

- Optimizing only as a plugin for a specific IDE or SDD product
- Making education/adoption of formal languages the primary goal (kept as a future extension point)
- Closing the product around NL-spec authoring assistance alone

## Definition of success (vision-stage hypothesis)

A state where the loop runs **without people deciding case by case**:

1. For changes or new features, a ChangeBrief records goals and in/out of scope; requirements are structured as property-level Gherkin Scenarios; the judgment skill emits whether/at what grain API / DbC / (later) formal specs are needed
2. Stack-appropriate adapters generate or update contract artifacts for the active change
3. The verify skill detects contract–implementation drift and feeds it back into the loop
4. When judgment is ambiguous, agents re-read or re-run the ChangeBrief instead of inventing scope from chat alone
5. Users may run skills alone or rely on automatic orchestration

Evaluation detail: [roadmap.md](roadmap.md).
