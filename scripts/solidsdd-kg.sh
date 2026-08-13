#!/usr/bin/env bash
# Build (if needed) and run solidsdd-kg against the repo.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# `init` is a pure file-copy scaffold step — no Go build/binary needed, so a
# project can adopt knowledge/kg for the first time without the compiled tool.
if [[ "${1:-}" == "init" ]]; then
  shift
  target="."
  force=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --root) target="$2"; shift 2 ;;
      --force) force=1; shift ;;
      *) echo "solidsdd-kg init: unknown flag: $1" >&2; exit 2 ;;
    esac
  done
  target="$(cd "${target}" && pwd)"
  templates="${ROOT}/skills/solidsdd-knowledge/references/kg-templates"
  kg_dir="${target}/.solidsdd/kg"
  mkdir -p "${kg_dir}"

  to_json_array() {
    local first=1 out="["
    for x in "$@"; do
      [[ ${first} -eq 0 ]] && out+=","
      out+="\"${x}\""
      first=0
    done
    out+="]"
    printf '%s' "${out}"
  }

  wrote=()
  skipped=()
  for f in schema.yaml config.yaml links.yaml; do
    dest="${kg_dir}/${f}"
    if [[ -f "${dest}" && "${force}" -eq 0 ]]; then
      skipped+=("${f}")
      continue
    fi
    cp "${templates}/${f}" "${dest}"
    wrote+=("${f}")
  done

  printf '{"ok":true,"kg_dir":"%s","wrote":%s,"skipped":%s}\n' \
    "${kg_dir}" "$(to_json_array "${wrote[@]}")" "$(to_json_array "${skipped[@]}")"
  exit 0
fi

export PATH="${HOME}/.local/go/bin:${PATH:-}"
BIN="${ROOT}/bin/solidsdd-kg"
MOD="${ROOT}/tools/solidsdd-kg"

if [[ ! -x "${BIN}" ]] || [[ "${MOD}/cmd/solidsdd-kg/main.go" -nt "${BIN}" ]]; then
  mkdir -p "${ROOT}/bin"
  (cd "${MOD}" && go build -o "${BIN}" ./cmd/solidsdd-kg)
fi

exec "${BIN}" "$@"
