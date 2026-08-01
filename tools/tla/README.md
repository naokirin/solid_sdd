# TLC tooling (Phase 3)

Default formal checker for solid_sdd: **TLA+ / TLC** via `tla2tools.jar`.

## Why TLC

| Option | Decision |
|--------|----------|
| **TLC (chosen)** | Matches TLA+ specs; mature CLI; small models run locally with JDK |
| Apalache | Strong for inductive invariants; heavier setup; later optional |
| Alloy Analyzer | Different modeling style; not first default |

## Setup

1. JDK 17+ (Temurin recommended), e.g. `mise install java@temurin-21`
2. Fetch the jar (gitignored — do not commit):

```bash
tools/tla/fetch-tla2tools.sh
```

3. Run a model:

```bash
tools/tla/tlc.sh path/to/Spec.tla
```

Or from an example that wraps it (see `examples/memory-formal`).

## Layout

| Path | Purpose |
|------|---------|
| `fetch-tla2tools.sh` | Download pinned `tla2tools.jar` |
| `tlc.sh` | Invoke `tlc2.TLC` with mise/java discovery |
| `tla2tools.jar` | Local cache (gitignored) |
