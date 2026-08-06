#!/usr/bin/env bash
# Constrained mutations for solidsdd run-state.json (no free-form Python).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then PY=python3; fi
exec "$PY" "$ROOT/scripts/solidsdd-run-state/run_state.py" "$@"
