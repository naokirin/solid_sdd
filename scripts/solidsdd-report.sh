#!/usr/bin/env bash
# solidsdd-report tooling CLI: collect / highlight / diagram / render.
# Usage:
#   scripts/solidsdd-report.sh collect --change-id ID [--project-root DIR] [--out PATH] [--pretty]
#   scripts/solidsdd-report.sh highlight PATH [--display-path REL] [--max-bytes N] [--out PATH] [--pretty] [--css-only]
#   scripts/solidsdd-report.sh diagram [--in PATH] [--out PATH] [--pretty]   # payload JSON on stdin when --in omitted
#   scripts/solidsdd-report.sh render --change-id ID [--project-root DIR] [--narrative PATH] [--format markdown|html|both]
#     Writes report.md/report.html directly under .solidsdd/changes/ID/ — see scripts/solidsdd-report/README.md.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then PY=python3; fi
exec "$PY" "$ROOT/scripts/solidsdd-report/cli.py" "$@"
