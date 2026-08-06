#!/usr/bin/env bash
# Deterministic next-action hint for solidsdd-run (read-only).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then PY=python3; fi
exec "$PY" "$ROOT/scripts/solidsdd-next/next.py" "$@"
