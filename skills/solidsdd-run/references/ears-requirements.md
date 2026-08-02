# EARS requirement sentences (optional)

[EARS](https://en.wikipedia.org/wiki/EARS_(software_requirements)) (Easy Approach to Requirements Syntax) structures **what the system shall do**. solid_sdd keeps **Gherkin** as acceptance / slicing ([gherkin-requirements.md](gherkin-requirements.md)). The two layers compose; they do not compete.

| Layer | Answers | Format |
|-------|---------|--------|
| EARS (optional) | What shall the system do? | Brief `in_scope[].text` (and optionally `success_criteria[].text`) |
| Gherkin | How do we check? | Feature / Scenario / Given–When–Then |
| Contracts | How does the machine check? | OpenAPI / OCL / formal |

## When to use

Prefer EARS wording in ChangeBrief scope texts when:

- Failure / unwanted paths are easy to omit in prose
- State-dependent behavior matters (`WHILE`, `WHERE`)
- AuthZ / money / safety boundaries need explicit triggers (`IF` / `WHEN`)

Skip EARS for tiny sample deltas where a short property sentence already maps 1:1 to a Scenario.

## Patterns (use English keywords; body in working language)

| Pattern | Template |
|---------|----------|
| Ubiquitous | `The <system> shall <action>` |
| Event-driven | `WHEN <trigger> THE <system> SHALL <action>` |
| Unwanted | `IF <unwanted trigger> THEN THE <system> SHALL <action>` |
| State-driven | `WHILE <state> THE <system> SHALL <action>` |
| Optional | `WHERE <feature included> THE <system> SHALL <action>` |

**Unwanted** and **state-driven** are the highest leverage vs today’s “name failure paths” prose rule.

## Mapping to ids

Keep mechanical coverage via ids (`R1`, `SC1`) and Scenario tags. EARS only changes the **`text`** of scoped items—not the id/`covers` chain.

Example:

```json
{
  "id": "R2",
  "text": "IF the client requests division or remainder with divisor zero THEN THE calculator service SHALL fail with a named domain error"
}
```

```gherkin
  @R2 @SC2
  Scenario: Division by zero fails with a named domain error
    …
```

## Critique / lint

Lint does **not** require EARS syntax. Critique may list missing unwanted/state patterns as **minor** (or major only when checkability of a known failure mode is lost—same F10 calibration as Gherkin).

## Relation to Workstream G

This note is the optional entry point. Expanding lint for EARS pattern detection remains future work.
