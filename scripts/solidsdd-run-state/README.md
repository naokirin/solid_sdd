Constrained mutations for solidsdd run-state.json (schema-validated).

Usage:
  ./scripts/solidsdd-run-state.sh [--project-root DIR] [--change-id ID] <command> ...

Commands: init | set-phase | set-wave | note | sync-items | set-item | set-host-toolchain | mark-change-done

Requires `jsonschema` + `PyYAML` (`pip install -r scripts/requirements.txt`). Resolves change dirs via `.solidsdd/config.yaml` when present.

See scripts/solidsdd-run-state/run_state.py and reference-src/run-state.md.

