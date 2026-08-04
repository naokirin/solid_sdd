# Change context (solidsdd.intake)

`solidsdd-intake` turns a raw change request (plus `solidsdd-context` stack facts) into a **Change Context** Markdown document. It records **why** and **how** the change is framed—demand, non-functional requirements, technology selection, and key judgments—**before** ChangeBrief / Gherkin.

Natural language is expected in the project’s **working language** (see [working-language.md](working-language.md)). Headings are **fixed English**; agents and humans must not invent alternate top-level section titles.

## Why

ChangeBrief and Gherkin capture scope and acceptance. They do not explain:

- what demand or problem triggered the work
- which non-functional qualities matter and why
- which technologies were chosen (or kept) and what was rejected
- which judgments were made while still implicit in chat

Without this document, later phases (and future readers) only see outcomes, not premises.

## Role split (required)

| Layer | Artifact | Answers |
|-------|----------|---------|
| Stack facts | `solidsdd-context` summary | What exists in the repo? |
| **Framing / rationale** | **`change-context.md`** | Demand, NFRs, tech choices, judgments |
| Change premise | ChangeBrief | What are we doing / not doing this change? |
| Acceptance | Gherkin | Which properties must hold? |
| Loop authority | OpenAPI / OCL / formal | How do we check implementation? |

Change Context is **not** a living product PRD and **not** a substitute for Brief or contracts. It is history + return point for **this change’s framing**. Additional requirements start a **new** change (new `change_id`).

## Default artifact path

| Artifact | Path |
|----------|------|
| Change Context | `.solidsdd/changes/<change_id>/change-context.md` |
| NFR SoT | `.solidsdd/changes/<change_id>/nfr.json` — structured NFRs; §4 is a **projection** ([nfr.schema.json](../schemas/nfr.schema.json)) |
| Change Context gate | `.solidsdd/changes/<change_id>/change-context-gate.json` |
| Active pointer / status | same lifecycle as Brief — [change-lifecycle.md](change-lifecycle.md) |

`solidsdd-intake` **owns** creating `change_id`, the change directory, `status.json` (`active`), `active-change.json`, `nfr.json`, and `change-context-gate.json`. `solidsdd-brief` then writes `change-brief.json` into that directory (must not invent a conflicting id).

## Required document shape

Use exactly these top-level headings (English). Subheadings under §4 / §5 are recommended but flexible.

```markdown
# Change context: <change_id>

## 1. Demand and problem
## 2. Drivers and constraints (from stakeholders / environment)
## 3. Functional intent (summary)
## 4. Non-functional requirements
## 5. Technology selection
## 6. Key judgments and trade-offs
## 7. Open questions and deferred decisions
## 8. Links
```

### Section guidance

| Section | Must include |
|---------|----------------|
| **1. Demand and problem** | Who/what hurts; desired outcome in prose (not Scenario lists) |
| **2. Drivers and constraints** | External constraints (compliance, timeline, “must reuse stack X”); explicit “none” if empty |
| **3. Functional intent** | Short summary of capabilities; detail belongs in Brief / Gherkin |
| **4. Non-functional requirements** | **Projection of `nfr.json` (SoT).** Include all six qualities (`reliability`, `security`, `performance`, `operability`, `compatibility`, `maintainability`). For `in_scope` items, `threshold` + `measurement` are required in JSON; render them in the Markdown table. `out_of_scope` / `deferred` need requirement + rationale (N/A OK). Do not invent §4 rows that are absent from `nfr.json` |
| **5. Technology selection** | **This change’s stack choices** (language/runtime, API style, persistence, test stack, contract approach): **decision**, **alternatives considered**, **rationale**, **source** (`user` / `repo_existing` / `agent_default` + why). If inheriting the repo stack, say so explicitly—do not leave blank. These are usually **not** harvest candidates (one-off or repo-local) |
| **6. Key judgments** | Non-obvious calls and **Means** (reusable decision criteria: e.g. “server is authority”, “opaque principal AuthZ only”, named domain errors vs raw exceptions). Prefer tagging each judgment with maturity `hypothesized` \| `confirmed` \| `canonical` when useful. Include `Working language: <tag> (from …)` per [working-language.md](working-language.md). Means-like judgments are the primary `knowledge/` harvest source — see [knowledge.md](knowledge.md) / [POL-KG-PERSISTENCE](../knowledge/policies/POL-KG-PERSISTENCE.md) |
| **7. Open questions** | Unresolved items; align with Brief `open_questions` / gates when blocking |
| **8. Links** | Paths to Brief, WorkPlan, Features, `nfr.json`, optional report (fill placeholders as artifacts appear). On follow-on changes, link prior change dirs / Features that remain in force |

Keep sections concise. Prefer bullets. Do not paste full OpenAPI/OCL.

### Cross-change framing (follow-on changes)

When the repo already has Features or prior `.solidsdd/changes/*/`:

1. In §2 or §8, list **prior Scenarios / prior `out_of_scope`** that must not be silently contradicted.
2. Put only this delta in the upcoming Brief; use assumptions/constraints for “keep existing behavior”.
3. Expect `solidsdd-run` to run `solidsdd-critique` with `subject: cross_change_consistency` after the work_plan critique ([adversarial-critique.md](adversarial-critique.md)).

## Human gate after intake (optional, situational)

Not every change needs a human pause. **If the initial user instruction already made the framing clear, do not gate.**

`solidsdd-intake` always writes `change-context-gate.json` ([change-context-gate.schema.json](../schemas/change-context-gate.schema.json)). `solidsdd-run` stops **after** `critique(change_context)` and **before** `solidsdd-brief` when `human_gate.required` is true.

### When to set `human_gate.required: true`

Any of:

| Trigger | Example |
|---------|---------|
| Material `agent_default` tech choice | Language/runtime, API style (OpenAPI vs GraphQL), persistence, or contract approach chosen by the agent without user/`repo_existing` clarity |
| User intent vs repo stack conflict | User implies GraphQL but repo is OpenAPI-only (or the reverse) without an explicit “migrate” ask |
| New security / money-adjacent NFR | §4 introduces authz, payments, PII handling as in-scope qualities |
| Blocking open questions | §7 items that must be answered before Brief scope is honest |
| Low confidence on framing | Competing interpretations of demand or NFR bar |

### When to set `human_gate.required: false`

All of the following (typical default):

- User stated stack/API style **or** decisions are clearly `repo_existing` / `user` with no conflict
- No new security/money NFR beyond explicit user ask
- §7 has no blocking questions (deferrals OK)
- Confidence is `medium` or `high`

Fill `decisions_to_confirm` only when `required: true` (concrete questions for the human). On approval, resume without thinning Change Context; on amendment, re-run `solidsdd-intake` (or edit Context under human direction then re-critique).

## When later skills must re-read

- `solidsdd-brief` — scope must not contradict §3–§6; `out_of_scope` should reflect deliberate exclusions from context; honor Change Context gate before starting when under `solidsdd-run`
- `solidsdd-judge` — density / adapter hints should respect §5 technology selection unless Brief/gates override
- `solidsdd-critique` — missing §4/§5 content, or tech/NFR with no rationale → `scope_gap` / fail when checkability of premise is lost; blocking §7 without gate → major. Missing/invalid `nfr.json` or in_scope NFR without threshold is primarily **lint** (`scripts/solidsdd-lint.sh`)
- Ambiguity in loop — re-read §5–§7 and `nfr.json` before inventing stack or NFR policy

## Critique expectations

`subject: change_context` — major when required headings are missing; when §4 or §5 are empty/hand-wavy despite a stack or quality-sensitive demand; when decisions lack both alternatives and rationale; when gate triggers above fire but `change-context-gate.json` has `required: false`; when Context §4 contradicts `nfr.json`. Polish-only wording → minor. See [adversarial-critique.md](adversarial-critique.md) and [human-gates.md](human-gates.md).
