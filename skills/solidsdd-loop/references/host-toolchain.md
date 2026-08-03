# Host toolchain (preflight)

solid_sdd launches many Task subagents. Each Subagent often starts a **non-interactive shell** without the user’s mise/asdf PATH hooks. If every verify/implement Task rediscovers `npm`/`node` with `find` / multi-path `which`, wall-clock and tokens look like “solid_sdd is slow” when the real issue is **host toolchain thrash**.

## Artifact

| Path | Role |
|------|------|
| `.solidsdd/host-toolchain.json` | Machine-local probe result (typically **gitignored**) |
| `schemas/host-toolchain.schema.json` | Shape |
| `scripts/solidsdd-host-toolchain.sh` | Deterministic probe (no LLM) |

```bash
# From consuming project root (or pass --project-root):
/path/to/solid_sdd/scripts/solidsdd-host-toolchain.sh --project-root .
/path/to/solid_sdd/scripts/solidsdd-host-toolchain.sh --project-root . --check   # exit 1 if not ready
```

## Rules for agents

1. **`solidsdd-context` (parent)** runs the script once (or equivalent short `command -v` / mise probe) and includes a **Toolchain** section in its summary: `ready`, `missing`, and the `commands` block to paste into Tasks.
2. **`solidsdd-run` / `solidsdd-loop` parents** copy that block (or the JSON `commands`) into **every** Task that runs shell verify/implement/derive/openapi lint. Also set `run-state.host_toolchain` from the JSON (`ready`, `missing`, `source`).
3. **Subagents must not** search the filesystem for `npm`/`node`/`bundle` when `commands` are provided. On failure: report immediately; parent may append `isolation_notes` entry `toolchain_rediscovery:<tool>:<reason>` only if rediscovery was unavoidable.
4. If `ready=false` at context time: treat as a **host gap** — fix PATH / mise **before** a long run. Do not start dozens of Tasks that each rediscover tools.

## Distinguishing cost vs thrash

See **Host toolchain thrash vs orchestration cost** in `docs/run-cost.md` (synced into orchestrator skill `references/run-cost.md`).
