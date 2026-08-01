#!/usr/bin/env bash
# Sync editing sources into skills/*/references/ for gh skill self-containment.
#
# Usage:
#   scripts/sync-skill-references.sh          # write copies
#   scripts/sync-skill-references.sh --check  # exit 1 if copies are stale
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODE="sync"
if [[ "${1:-}" == "--check" ]]; then
  MODE="check"
elif [[ -n "${1:-}" ]]; then
  echo "usage: $0 [--check]" >&2
  exit 2
fi

tmpdir=
cleanup() {
  if [[ -n "${tmpdir}" && -d "${tmpdir}" ]]; then
    rm -rf "${tmpdir}"
  fi
}
trap cleanup EXIT

tmpdir="$(mktemp -d)"
mismatch=0
updated=0

# Build a staged copy of `src` into `$tmpdir/out` applying optional transforms.
# Transforms: none | ocl-exec-path
stage_file() {
  local src="$1"
  local transform="${2:-none}"
  local out="$tmpdir/out"
  mkdir -p "$(dirname "$out")"
  case "$transform" in
    none)
      cp "$src" "$out"
      ;;
    ocl-exec-path)
      # Point loop execution-model at the installed skill reference, not docs/
      sed 's|(see `docs/execution-model.md`)|(see solidsdd-loop `references/execution-model.md`)|g' \
        "$src" >"$out"
      ;;
    *)
      echo "unknown transform: $transform" >&2
      exit 2
      ;;
  esac
}

sync_one() {
  local src="$1"
  local dest="$2"
  local transform="${3:-none}"

  if [[ ! -f "$src" ]]; then
    echo "missing source: $src" >&2
    exit 1
  fi

  stage_file "$src" "$transform"
  local staged="$tmpdir/out"

  if [[ "$MODE" == "check" ]]; then
    if [[ ! -f "$dest" ]]; then
      echo "MISSING  $dest  (from $src)"
      mismatch=1
      return
    fi
    if ! cmp -s "$staged" "$dest"; then
      echo "STALE    $dest  (from $src)"
      mismatch=1
    else
      echo "ok       $dest"
    fi
    return
  fi

  mkdir -p "$(dirname "$dest")"
  if [[ -f "$dest" ]] && cmp -s "$staged" "$dest"; then
    echo "unchanged $dest"
  else
    cp "$staged" "$dest"
    echo "updated   $dest"
    updated=$((updated + 1))
  fi
}

echo "== solid_sdd skill references ($MODE) =="

# OpenAPI adapter
sync_one adapters/openapi/README.md skills/solidsdd-apply-api/references/openapi-adapter.md
sync_one adapters/openapi/README.md skills/solidsdd-implement/references/openapi-adapter.md
sync_one adapters/openapi/README.md skills/solidsdd-verify/references/openapi-adapter.md

# OCL adapter (path rewrite for execution-model)
sync_one adapters/ocl/README.md skills/solidsdd-apply-dbc/references/ocl-adapter.md ocl-exec-path
sync_one adapters/ocl/README.md skills/solidsdd-derive-tests/references/ocl-adapter.md ocl-exec-path
sync_one adapters/ocl/README.md skills/solidsdd-implement/references/ocl-adapter.md ocl-exec-path
sync_one adapters/ocl/README.md skills/solidsdd-verify/references/ocl-adapter.md ocl-exec-path

# Docs / schemas / rules
sync_one docs/execution-model.md skills/solidsdd-loop/references/execution-model.md
sync_one schemas/application-plan.schema.json skills/solidsdd-judge/references/application-plan.schema.json
sync_one schemas/verification-report.schema.json skills/solidsdd-verify/references/verification-report.schema.json
sync_one rules/solidsdd.mdc skills/solidsdd-loop/references/project-rule.mdc

# Skill-local shared sources
sync_one reference-src/contract-layout.md skills/solidsdd-context/references/contract-layout.md
sync_one reference-src/contract-layout.md skills/solidsdd-implement/references/contract-layout.md
sync_one reference-src/contract-layout.md skills/solidsdd-loop/references/contract-layout.md
sync_one reference-src/judgment-axes.md skills/solidsdd-judge/references/judgment-axes.md

if [[ "$MODE" == "check" ]]; then
  if [[ "$mismatch" -ne 0 ]]; then
    echo
    echo "Skill references are out of date. Run: scripts/sync-skill-references.sh" >&2
    exit 1
  fi
  echo
  echo "All skill references are in sync."
  exit 0
fi

echo
echo "Done. Updated $updated file(s)."
