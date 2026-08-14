# solidsdd-report tooling

Deterministic helpers for `solidsdd-report`, plus a `render` step that writes
`report.md` / `report.html` itself. Moving highlighting/diagramming into
scripts only pays off if the report-writing agent never has to *transcribe*
their output through its own generation stream — so `render.py` assembles
the finished file directly from `collect.py`'s data (tables, verbatim Change
Context prose, verbatim Gherkin, coverage matrix, raw contract embeds,
diagrams) plus a small, agent-authored "narrative" JSON containing only the
handful of sections that genuinely need LLM synthesis (API contract / DbC /
Formal natural-language summaries, the status-overview paragraph). The
report is a *view*, not new authored content, so most of it never needed an
LLM pass in the first place.

## Usage

From a consuming project root (directory that contains `.solidsdd/`):

```bash
scripts/solidsdd-report.sh collect --change-id ID [--project-root .] [--out PATH] [--pretty]
scripts/solidsdd-report.sh highlight PATH [--display-path REL] [--max-bytes N] [--out PATH] [--pretty]
scripts/solidsdd-report.sh highlight --css-only   # print TOKEN_CSS to inline once in report.html
scripts/solidsdd-report.sh diagram [--in PATH] [--pretty] [--allow-network]   # payload JSON on stdin when --in omitted
scripts/solidsdd-report.sh render --change-id ID [--project-root .] [--narrative PATH] [--format markdown|html|both] [--allow-network]
```

`render` writes `.solidsdd/changes/ID/report.md` and/or `report.html`
directly — the caller doesn't paste generated content into a Write call.
`--narrative` is optional; omit it (or omit fields) and those sections fall
back to a "no natural-language summary supplied" stub the agent can leave as
a TODO or a follow-up edit. `collect` / `highlight` / `diagram` remain
available standalone for a caller that wants to inspect or post-process the
intermediate data before rendering.

Requires Python 3 + [`PyYAML`](https://pypi.org/project/PyYAML/) (same as
`solidsdd-lint` / `solidsdd-architecture`). No other third-party Python
dependency — `highlight.py`'s tokenizers are regex-based on purpose, so no
Pygments/CDN install is needed in a consuming project.

**Optional: [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) (`mmdc`)
for SVG diagrams.** Node placement, edge routing, and label placement
without collisions is a genuinely hard layout problem — earlier versions of
`diagram.py` hand-computed SVG coordinates and repeatedly produced diagrams
that were technically non-overlapping but still hard to read. `diagram.py`
now delegates that entirely to Mermaid's own renderer via `mmdc`, run
through the same Mermaid source already generated for the no-SVG fallback
path. Install it globally (`npm install -g @mermaid-js/mermaid-cli`) or as
a project devDependency (`npm install -D @mermaid-js/mermaid-cli`) — it
needs a Chromium/Puppeteer runtime under the hood either way. `diagram.py`
looks for a `mmdc` binary directly on `PATH` first (covers the global
install, or a local install once its `node_modules/.bin` is on `PATH`);
if that's not found but `npx` is, it runs `npx --offline @mermaid-js/mermaid-cli`
instead, which picks up a project devDependency without needing it on
`PATH` — `--offline` means this only ever uses an already-installed
local/cached copy, never a network fetch. When neither path can invoke the
tool, or the render fails for any reason (no browser runtime, timeout),
`diagram` returns `svg: null` and the caller keeps the Mermaid source only
— exactly as change-report.md already allows for the no-SVG case, so a
project without `mmdc` installed still gets a complete, correct report.

Pass `--allow-network` to `render`/`diagram` to let a first-run `npx`
install `@mermaid-js/mermaid-cli` on demand instead of requiring it to
already be cached — this is an explicit opt-in the caller should only set
after a human has agreed to it (it drops `--offline`, adds `--yes` to skip
npx's interactive install prompt, and raises the timeout to accommodate a
first-run install plus a Chromium download). Never enable it by default in
an unattended context.

One report can carry several diagrams. `shutil.which` lookups are cheap,
but actually spawning `mmdc`/`npx` and having it fail (no browser runtime)
isn't — so the outcome of the *first* SVG attempt per `allow_network` mode
is memoized for the lifetime of one `render`/`diagram` process; every
later diagram in that same run skips straight to `svg: null` once that's
established, instead of paying for its own failed spawn.

### Troubleshooting: SVG never renders (always falls back to Mermaid-only)

Two environment issues account for most of these — both are about the
Puppeteer/Chromium runtime `mmdc` needs, not about `diagram.py` itself
(confirmed by reproducing and fixing each one directly):

1. **Architecture mismatch on ARM64 hosts, especially inside
   Docker/devcontainers** — Puppeteer's own Chromium download can resolve
   to an x86-64 build on an arm64 host (`file` on the downloaded binary
   will show `x86-64` even when it landed in a path named for arm64); the
   symptom is `rosetta error: failed to open elf at
   /lib64/ld-linux-x86-64.so.2`. This is a known, documented issue for
   Apple Silicon / ARM64 + Docker, not specific to any one setup — see
   [this writeup](https://zenn.dev/frog/articles/24a20e8a2811b5). Fix: install
   a real, architecture-matching Chromium yourself and point Puppeteer at
   it instead of letting it download one:
   ```bash
   sudo apt-get install -y chromium   # or your distro's equivalent
   export PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser  # path may vary
   export PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
   ```
2. **Sandboxed/Snap-packaged Chromium can't read `mmdc`'s own files** — on
   Ubuntu, `apt install chromium` installs a transitional package backed by
   a **Snap**, and Snap's confinement (AppArmor) restricts which
   filesystem paths Chromium may read. Mermaid CLI loads a bundled
   `dist/index.html` from wherever `@mermaid-js/mermaid-cli` is installed;
   if that's under `/tmp` or under npx's own cache (`~/.npm/_npx/...`),
   Snap-confined Chromium may refuse it (`net::ERR_FILE_NOT_FOUND` /
   `net::ERR_ACCESS_DENIED`), even though the same command works from a
   plain directory under `$HOME`. Fix: install
   `@mermaid-js/mermaid-cli` under a project/home directory Snap can read
   (`npm install -D @mermaid-js/mermaid-cli` in a project under `$HOME`,
   with its `node_modules/.bin` on `PATH` so `diagram.py` finds `mmdc`
   directly instead of going through `npx`'s own cache path) — or install
   a non-Snap Chromium/Chrome build if your distro offers one.

Both were reproduced and resolved this way in a containerized ARM64
sandbox during development; the same `render`/`diagram` commands produced
real inline SVGs once both fixes were in place.

## Modules

| File | Role |
|------|------|
| `collect.py` | Resolves `change_id`, reads Change Context / ChangeBrief / WorkPlan / `nfr.json` / tied Features / ApplicationPlan(s) / ArchitecturePlan / contracts, computes Present / Not-performed per report section, the Brief-id coverage matrix, working-language hint, verbatim Change Context section text, verbatim tied Gherkin Scenario blocks, and diagram-eligibility + node/edge data. Emits one JSON blob. |
| `highlight.py` | Regex tokenizer for JSON / YAML / Gherkin / OCL / GraphQL → HTML `<span class="tok-*">`-wrapped source, with a fixed `TOKEN_CSS` block (cyan keys, salmon strings, muted amber keywords — no yellow/chartreuse). Truncates raw embeds at `--max-bytes` (default 100KB) per change-report.md. |
| `diagram.py` | Mermaid source (always) for the three diagram kinds change-report.md defines (`dependency_graph`, `target_mapping`, `state_diagram`), plus an inline SVG rendered via the optional Mermaid CLI (`mmdc`) when it's available — `svg: null` otherwise, with Mermaid-only as the fallback. |
| `render.py` | Combines `collect.py` + `highlight.py` + `diagram.py` output with the narrative JSON and writes `report.md`/`report.html` directly to disk. |
| `cli.py` | `collect` / `highlight` / `diagram` / `render` subcommands, dispatched by `scripts/solidsdd-report.sh`. |

## Narrative JSON (render's only free-text input)

```json
{
  "language": "en",
  "status_overview": "One paragraph on where this change stands.",
  "api_contract_summary": "Natural-language summary of operations/types exposed.",
  "dbc_summary": "Natural-language summary of OCL types/invariants/preconditions.",
  "formal_summary": "Natural-language summary of the formal spec.",
  "formal_state_diagram": {"states": ["Idle", "Owned"], "transitions": [{"from": "Idle", "to": "Owned", "label": "Acquire"}]}
}
```

All fields are optional. `formal_state_diagram` is only worth supplying when
a Formal spec has an identifiable mode/status variable driving a small
number of states (see change-report.md "State diagrams") — deciding that
still requires reading the `.tla`/`.als` source, which stays the agent's job.

## Output

`collect`: see the JSON shape produced by `collect()` — `sections` (per
report section: `state: "present"\|"not_performed"` + owning skill),
`coverage_matrix` (Brief `R*`/`SC*` id → covering WorkPlan items → tied
Scenario), `diagrams` (per-kind `eligible` flag + ready-to-render node/edge
data), `artifacts` (parsed content + resolved paths + verbatim section text),
`source_artifacts` (flat list for report §8).

`highlight`: `{"path", "language", "truncated", "original_bytes", "html"}`.

`diagram`: `{"mermaid", "svg"}` (`svg` is `null` when `mmdc` isn't available
or the render failed — keep the Mermaid source only in that case, exactly
as change-report.md already allows).

`render`: `{"markdown": "<path written>", "html": "<path written>"}` for
whichever `--format` was requested.

## What this does *not* do

No natural-language synthesis beyond the narrative JSON's few fields — that
stays the report-writing agent's job. It also does not cache across runs
(re-collecting/re-rendering is still a full pass every time) — see
change-report.md for that as a separate, later concern.
