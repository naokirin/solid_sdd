#!/usr/bin/env bash
# Constrained mutations for solidsdd run-state.json (no free-form Python).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$ROOT/scripts/solidsdd-run-state/run_state.py" "$@"
