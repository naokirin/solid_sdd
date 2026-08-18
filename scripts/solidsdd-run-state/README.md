Constrained mutations for solidsdd run-state.json (schema-validated).

Usage:
  ./scripts/solidsdd-run-state.sh [--project-root DIR] [--change-id ID] <command> ...

Commands: init | set-phase | set-wave | note | sync-items | set-item | set-host-toolchain | set-execution-profile | mark-change-done

`init --phase triage` starts the reduced Thin (L1) run-state shape instead of the default `intake` (Standard/Full). `set-execution-profile` writes/updates the Triage-derived `execution_profile` object (`--requested` / `--effective` / `--required-minimum`, optional `--change-type` / `--risk` / `--complexity` / `--contract-impact` / `--architecture-impact` / `--uncertain` / repeatable `--reason` / `--escalated-from` / `--escalation-reason`); it refuses to write `--effective` below `--required-minimum`. See reference-src/triage.md.

Requires `jsonschema` + `PyYAML` (`pip install -r scripts/requirements.txt`). Resolves change dirs via `.solidsdd/config.yaml` when present.

See scripts/solidsdd-run-state/run_state.py and reference-src/run-state.md.

