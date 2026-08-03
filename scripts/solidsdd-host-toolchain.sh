#!/usr/bin/env bash
# Deterministic host toolchain probe for solid_sdd.
# Usage:
#   scripts/solidsdd-host-toolchain.sh [--project-root DIR] [--check] [--stdout] [--pretty]
# Writes: <project-root>/.solidsdd/host-toolchain.json
# Exit: 0 ok, 1 ready=false with --check, 2 tooling error
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$ROOT/scripts/solidsdd-host-toolchain/host_toolchain.py" "$@"
