# Clarifications (persistent Q/A)

solid_sdd keeps **blocking framing questions** on disk so resume does not depend on chat memory. Inspired by Intent CLI `clarify`, but scoped to a **change** — not a living product intent-tree.

## Path

| Artifact | Path |
|----------|------|
| Clarifications queue | `.solidsdd/changes/<change_id>/clarifications/open.json` |

Schema: [clarifications.schema.json](../schemas/clarifications.schema.json). Layout: [contract-layout.md](contract-layout.md).

## When to write

1. **`solidsdd-grill`** — each structured question becomes an `items[]` entry (`status: open` until answered).
2. **`solidsdd-intake`** — blocking §7 questions should also appear here (ids may align with Brief `open_questions`).
3. Human or agent resolves an item → set `status: resolved`, `decision`, optional `rationale` / `maturity`.

## Blocking vs non-blocking

- `blocking: true` + `status: open` → set `human_gate.required: true` on the clarifications file; orchestrator **stops** (typically after Grill / before Brief, or mid-intake when framing cannot proceed). Write `run-state.phase` to `stopped` or keep `grill` / `intake` with `stopped_reason` citing clarifications.
- Resume when all blocking items are `resolved` **or** a `gate-approval.json` with `scope: clarifications` records approve / approve_partial.

## Relation to other artifacts

| Artifact | Role |
|----------|------|
| Change Context §7 | Human-readable open questions (projection / summary) |
| ChangeBrief `open_questions` | Scope-level open items |
| `change-context-gate.json` | Pause before Brief for framing confirmation |
| `clarifications/open.json` | **Durable** Q/A with recommendation + evidence + resolution trail |

Do not delete resolved items immediately — keep them for audit; later changes start a new `change_id` rather than editing done-change clarifications into a PRD.

## Grill question shape

When recording from Grill, prefer:

- `question` — one focused ask
- `options` — 2–4 concrete choices
- `recommended_answer` + `evidence` — agent suggestion with repo facts
- After human answer → `decision`, `rationale`, `maturity` (`confirmed` typical)
