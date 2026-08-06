#!/usr/bin/env bash
# Deterministic solid_sdd lint (critique Step 0/1).
# Usage:
#   scripts/solidsdd-lint.sh [--project-root DIR] [--change-id ID] [--pretty]
# Exit: 0 pass, 1 fail (blocker/major), 2 tooling error
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then PY=python3; fi
exec "$PY" "$ROOT/scripts/solidsdd-lint/lint.py" "$@"
