#!/usr/bin/env bash
# Deterministic host toolchain probe for solid_sdd.
# Usage:
#   scripts/solidsdd-host-toolchain.sh [--project-root DIR] [--check] [--stdout] [--pretty]
# Writes: host-toolchain.json (path from .solidsdd/config.yaml; default .solidsdd/host-toolchain.json)
# Exit: 0 ok, 1 ready=false with --check, 2 tooling error
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then PY=python3; fi
exec "$PY" "$ROOT/scripts/solidsdd-host-toolchain/host_toolchain.py" "$@"
