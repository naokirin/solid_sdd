# Structurizr CLI (optional)

`solid_sdd`'s Architecture Model (`.solidsdd/architecture/workspace.dsl`) is
parsed and validated by `scripts/solidsdd-architecture/` — a self-contained
Python parser, no JVM required. That parser is the **primary, always-run**
validator (wired into `scripts/solidsdd-lint.sh`).

The real Structurizr CLI is **optional, additional** verification — useful
for a second, independently-implemented check, or for rendering diagrams
from the model. It is never a hard dependency: `solidsdd-architecture` edits
DSL files whether or not this CLI is installed, and CI does not require it.

## Why optional

| Option | Decision |
|--------|----------|
| **Self-built Python parser (primary)** | No JVM/Java dependency for the common case; matches the rest of `scripts/` |
| **Structurizr CLI (optional)** | Real, independently-maintained implementation of the full grammar; useful as a second opinion or for rendering, when a JDK happens to be available |

## Setup

1. JDK 17+ (Temurin recommended), e.g. `mise install java@temurin-21`
2. Fetch the CLI (gitignored — do not commit):

```bash
tools/structurizr/fetch-structurizr-cli.sh
```

3. Validate a workspace directly:

```bash
tools/structurizr/structurizr.sh validate -w path/to/workspace.dsl
```

4. Or fold it into `scripts/solidsdd-architecture.sh validate` as a second check:

```bash
export STRUCTURIZR_CLI="$(pwd)/tools/structurizr/structurizr.sh"
scripts/solidsdd-architecture.sh validate --project-root . --with-structurizr-cli
```

`STRUCTURIZR_CLI` can point at any `structurizr.sh`/`structurizr-cli`
binary; it doesn't have to be this repo's copy. Without
`--with-structurizr-cli`, `solidsdd-architecture.sh validate` never looks
for this tool at all.

## Layout

| Path | Purpose |
|------|---------|
| `fetch-structurizr-cli.sh` | Download the pinned release zip and unpack it |
| `structurizr.sh` | Thin wrapper around the unpacked CLI |
| `cli/` | Local unpacked copy (gitignored) |
