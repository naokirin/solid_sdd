#!/usr/bin/env bash
# Build (if needed) and run solidsdd-kg against the repo.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="${HOME}/.local/go/bin:${PATH:-}"
BIN="${ROOT}/bin/solidsdd-kg"
MOD="${ROOT}/tools/solidsdd-kg"

if [[ ! -x "${BIN}" ]] || [[ "${MOD}/cmd/solidsdd-kg/main.go" -nt "${BIN}" ]]; then
  mkdir -p "${ROOT}/bin"
  (cd "${MOD}" && go build -o "${BIN}" ./cmd/solidsdd-kg)
fi

exec "${BIN}" "$@"
