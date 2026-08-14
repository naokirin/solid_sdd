#!/usr/bin/env bash
# Architecture Model CLI (Structurizr DSL subset): validate / project.
# Usage:
#   scripts/solidsdd-architecture.sh validate [--project-root DIR] [--pretty]
#   scripts/solidsdd-architecture.sh project --change-id ID [--project-root DIR] [--out PATH] [--pretty]
# Exit (validate): 0 pass, 1 fail (blocker/major), 2 tooling error
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then PY=python3; fi
exec "$PY" "$ROOT/scripts/solidsdd-architecture/cli.py" "$@"
