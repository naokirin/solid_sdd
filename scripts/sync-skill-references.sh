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
# Transforms: none (sources must already be skill-self-contained)
stage_file() {
  local src="$1"
  local transform="${2:-none}"
  local out="$tmpdir/out"
  mkdir -p "$(dirname "$out")"
  case "$transform" in
    none)
      cp "$src" "$out"
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

# GraphQL adapter (Phase 2 skeleton)
sync_one adapters/graphql/README.md skills/solidsdd-apply-api/references/graphql-adapter.md
sync_one adapters/graphql/README.md skills/solidsdd-implement/references/graphql-adapter.md
sync_one adapters/graphql/README.md skills/solidsdd-verify/references/graphql-adapter.md

# Ruby / RSpec test-target adapter (Phase 2)
sync_one adapters/ruby-rspec/README.md skills/solidsdd-derive-tests/references/ruby-rspec-adapter.md
sync_one adapters/ruby-rspec/README.md skills/solidsdd-apply-dbc/references/ruby-rspec-adapter.md
sync_one adapters/ruby-rspec/README.md skills/solidsdd-verify/references/ruby-rspec-adapter.md
sync_one adapters/ruby-rspec/README.md skills/solidsdd-implement/references/ruby-rspec-adapter.md

# OCL adapter
sync_one adapters/ocl/README.md skills/solidsdd-apply-dbc/references/ocl-adapter.md
sync_one adapters/ocl/README.md skills/solidsdd-derive-tests/references/ocl-adapter.md
sync_one adapters/ocl/README.md skills/solidsdd-implement/references/ocl-adapter.md
sync_one adapters/ocl/README.md skills/solidsdd-verify/references/ocl-adapter.md

# Formal adapter (Phase 3 design)
sync_one adapters/formal/README.md skills/solidsdd-apply-formal/references/formal-adapter.md
sync_one adapters/formal/README.md skills/solidsdd-verify-formal/references/formal-adapter.md
sync_one schemas/verification-report.schema.json skills/solidsdd-verify-formal/references/verification-report.schema.json
sync_one reference-src/loop-retry.md skills/solidsdd-verify-formal/references/loop-retry.md

# Docs / schemas / rules
sync_one docs/execution-model.md skills/solidsdd-loop/references/execution-model.md
sync_one docs/execution-model.md skills/solidsdd-run/references/execution-model.md
sync_one schemas/application-plan.schema.json skills/solidsdd-judge/references/application-plan.schema.json
sync_one schemas/work-plan.schema.json skills/solidsdd-decompose/references/work-plan.schema.json
sync_one schemas/work-plan.schema.json skills/solidsdd-run/references/work-plan.schema.json
sync_one schemas/change-brief.schema.json skills/solidsdd-brief/references/change-brief.schema.json
sync_one schemas/change-brief.schema.json skills/solidsdd-run/references/change-brief.schema.json
sync_one schemas/change-brief.schema.json skills/solidsdd-decompose/references/change-brief.schema.json
sync_one schemas/active-change.schema.json skills/solidsdd-brief/references/active-change.schema.json
sync_one schemas/active-change.schema.json skills/solidsdd-run/references/active-change.schema.json
sync_one schemas/active-change.schema.json skills/solidsdd-decompose/references/active-change.schema.json
sync_one schemas/active-change.schema.json skills/solidsdd-intake/references/active-change.schema.json
sync_one schemas/change-status.schema.json skills/solidsdd-brief/references/change-status.schema.json
sync_one schemas/change-status.schema.json skills/solidsdd-run/references/change-status.schema.json
sync_one schemas/change-status.schema.json skills/solidsdd-intake/references/change-status.schema.json
sync_one schemas/change-context-gate.schema.json skills/solidsdd-intake/references/change-context-gate.schema.json
sync_one schemas/change-context-gate.schema.json skills/solidsdd-run/references/change-context-gate.schema.json
sync_one schemas/change-context-gate.schema.json skills/solidsdd-critique/references/change-context-gate.schema.json
sync_one schemas/change-context-gate.schema.json skills/solidsdd-brief/references/change-context-gate.schema.json
sync_one schemas/nfr.schema.json skills/solidsdd-intake/references/nfr.schema.json
sync_one schemas/nfr.schema.json skills/solidsdd-critique/references/nfr.schema.json
sync_one schemas/nfr.schema.json skills/solidsdd-run/references/nfr.schema.json
sync_one schemas/verification-report.schema.json skills/solidsdd-verify/references/verification-report.schema.json
sync_one schemas/critique-report.schema.json skills/solidsdd-critique/references/critique-report.schema.json
sync_one rules/solidsdd.mdc skills/solidsdd-loop/references/project-rule.mdc
sync_one rules/solidsdd.mdc skills/solidsdd-run/references/project-rule.mdc

# Skill-local shared sources
sync_one reference-src/contract-layout.md skills/solidsdd-context/references/contract-layout.md
sync_one reference-src/contract-layout.md skills/solidsdd-implement/references/contract-layout.md
sync_one reference-src/contract-layout.md skills/solidsdd-loop/references/contract-layout.md
sync_one reference-src/contract-layout.md skills/solidsdd-run/references/contract-layout.md
sync_one reference-src/run-state.md skills/solidsdd-loop/references/run-state.md
sync_one reference-src/run-state.md skills/solidsdd-run/references/run-state.md
sync_one schemas/run-state.schema.json skills/solidsdd-loop/references/run-state.schema.json
sync_one schemas/run-state.schema.json skills/solidsdd-run/references/run-state.schema.json
sync_one reference-src/change-lifecycle.md skills/solidsdd-brief/references/change-lifecycle.md
sync_one reference-src/change-lifecycle.md skills/solidsdd-run/references/change-lifecycle.md
sync_one reference-src/change-lifecycle.md skills/solidsdd-decompose/references/change-lifecycle.md
sync_one reference-src/change-lifecycle.md skills/solidsdd-context/references/change-lifecycle.md
sync_one reference-src/change-lifecycle.md skills/solidsdd-loop/references/change-lifecycle.md
sync_one reference-src/change-lifecycle.md skills/solidsdd-intake/references/change-lifecycle.md
sync_one reference-src/change-context.md skills/solidsdd-intake/references/change-context.md
sync_one reference-src/change-context.md skills/solidsdd-run/references/change-context.md
sync_one reference-src/change-context.md skills/solidsdd-brief/references/change-context.md
sync_one reference-src/change-context.md skills/solidsdd-critique/references/change-context.md
sync_one reference-src/change-context.md skills/solidsdd-judge/references/change-context.md
sync_one reference-src/judgment-axes.md skills/solidsdd-judge/references/judgment-axes.md
sync_one reference-src/judgment-axes.md skills/solidsdd-critique/references/judgment-axes.md
sync_one reference-src/human-gates.md skills/solidsdd-judge/references/human-gates.md
sync_one reference-src/human-gates.md skills/solidsdd-loop/references/human-gates.md
sync_one reference-src/human-gates.md skills/solidsdd-decompose/references/human-gates.md
sync_one reference-src/human-gates.md skills/solidsdd-run/references/human-gates.md
sync_one reference-src/human-gates.md skills/solidsdd-brief/references/human-gates.md
sync_one reference-src/human-gates.md skills/solidsdd-intake/references/human-gates.md
sync_one reference-src/change-brief.md skills/solidsdd-brief/references/change-brief.md
sync_one reference-src/change-brief.md skills/solidsdd-run/references/change-brief.md
sync_one reference-src/change-brief.md skills/solidsdd-decompose/references/change-brief.md
sync_one reference-src/change-brief.md skills/solidsdd-critique/references/change-brief.md
sync_one reference-src/change-brief.md skills/solidsdd-judge/references/change-brief.md
sync_one reference-src/loop-retry.md skills/solidsdd-verify/references/loop-retry.md
sync_one reference-src/loop-retry.md skills/solidsdd-loop/references/loop-retry.md
sync_one reference-src/loop-retry.md skills/solidsdd-critique/references/loop-retry.md
sync_one reference-src/loop-retry.md skills/solidsdd-run/references/loop-retry.md
sync_one reference-src/adversarial-critique.md skills/solidsdd-critique/references/adversarial-critique.md
sync_one reference-src/adversarial-critique.md skills/solidsdd-loop/references/adversarial-critique.md
sync_one reference-src/adversarial-critique.md skills/solidsdd-run/references/adversarial-critique.md
sync_one scripts/solidsdd-lint/README.md skills/solidsdd-critique/references/solidsdd-lint.md
sync_one reference-src/work-decomposition.md skills/solidsdd-decompose/references/work-decomposition.md
sync_one reference-src/work-decomposition.md skills/solidsdd-run/references/work-decomposition.md
sync_one reference-src/gherkin-requirements.md skills/solidsdd-decompose/references/gherkin-requirements.md
sync_one reference-src/gherkin-requirements.md skills/solidsdd-run/references/gherkin-requirements.md
sync_one reference-src/gherkin-requirements.md skills/solidsdd-critique/references/gherkin-requirements.md
sync_one reference-src/gherkin-requirements.md skills/solidsdd-report/references/gherkin-requirements.md
sync_one reference-src/change-report.md skills/solidsdd-report/references/change-report.md
sync_one reference-src/change-lifecycle.md skills/solidsdd-report/references/change-lifecycle.md
sync_one reference-src/contract-layout.md skills/solidsdd-report/references/contract-layout.md
sync_one reference-src/change-context.md skills/solidsdd-report/references/change-context.md
sync_one reference-src/change-brief.md skills/solidsdd-report/references/change-brief.md

# Working language (prose policy)
sync_one reference-src/working-language.md skills/solidsdd-intake/references/working-language.md
sync_one reference-src/working-language.md skills/solidsdd-brief/references/working-language.md
sync_one reference-src/working-language.md skills/solidsdd-decompose/references/working-language.md
sync_one reference-src/working-language.md skills/solidsdd-critique/references/working-language.md
sync_one reference-src/working-language.md skills/solidsdd-judge/references/working-language.md
sync_one reference-src/working-language.md skills/solidsdd-report/references/working-language.md
sync_one reference-src/working-language.md skills/solidsdd-run/references/working-language.md
sync_one reference-src/working-language.md skills/solidsdd-loop/references/working-language.md

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
