#!/usr/bin/env bash
# Run the official Structurizr CLI. Usage: structurizr.sh validate -w path/to/workspace.dsl
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
CLI="${ROOT}/cli/structurizr.sh"

if [[ ! -x "$CLI" ]]; then
  echo "Missing $CLI — run: tools/structurizr/fetch-structurizr-cli.sh" >&2
  exit 2
fi

exec "$CLI" "$@"
