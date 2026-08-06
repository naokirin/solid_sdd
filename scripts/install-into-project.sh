#!/usr/bin/env bash
# Install solid_sdd (skills + mechanical tooling) into a consuming project.
# Does not use a skill-only CLI — one managed tree keeps skills and tooling in sync.
#
# Usage:
#   scripts/install-into-project.sh --project-root DIR --agent cursor
#   scripts/install-into-project.sh --project-root DIR --agent cursor,claude-code \
#       --from-local /path/to/solid_sdd
#   scripts/install-into-project.sh --project-root DIR --agent copilot \
#       --repo naokirin/solid_sdd --ref main
#
# Default vendor: <project>/.solidsdd/vendor/solid_sdd
# Override with --vendor-dir (project-relative or absolute).
set -euo pipefail

SOLIDSDD_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="${SOLIDSDD_SRC}/scripts/install-manifest.txt"

PROJECT_ROOT=""
VENDOR_DIR_REL=".solidsdd/vendor/solid_sdd"
AGENTS=()
FROM_LOCAL=""
REPO="naokirin/solid_sdd"
REF=""
USE_REMOTE=0
FORCE=0
WITH_KG=0
SKIP_PIP=0
SKIP_SKILLS=0
SKIP_RULE=0

usage() {
  sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
  cat <<'EOF'

Options:
  --project-root DIR   Consuming project root (required)
  --vendor-dir PATH    Vendor install path (default: .solidsdd/vendor/solid_sdd)
  --agent LIST         Comma-separated: cursor, claude-code, copilot, codex, devin
                       (repeatable; at least one required unless --skip-skills)
  --from-local DIR     Copy from a local solid_sdd checkout
                       (default: this repository when --repo/--ref omitted)
  --repo OWNER/REPO    Fetch from GitHub instead of local (default: naokirin/solid_sdd)
  --ref REF            Git ref/tag/SHA for remote install (implies remote fetch)
  --with-kg            Also vendor tools/solidsdd-kg and build bin/solidsdd-kg if Go present
  --skip-pip           Do not create vendor .venv / install PyYAML+jsonschema
  --skip-skills        Do not copy skills into agent directories
  --skip-rule          Do not install project rule for Cursor
  --force              Overwrite existing vendor / skills
  -h, --help           Show help
EOF
}

die() { echo "error: $*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-root) PROJECT_ROOT="${2:-}"; shift 2 ;;
    --vendor-dir) VENDOR_DIR_REL="${2:-}"; shift 2 ;;
    --agent)
      IFS=',' read -r -a _a <<< "${2:-}"
      AGENTS+=("${_a[@]}")
      shift 2
      ;;
    --from-local) FROM_LOCAL="${2:-}"; shift 2 ;;
    --repo) REPO="${2:-}"; USE_REMOTE=1; shift 2 ;;
    --ref) REF="${2:-}"; USE_REMOTE=1; shift 2 ;;
    --with-kg) WITH_KG=1; shift ;;
    --skip-pip) SKIP_PIP=1; shift ;;
    --skip-skills) SKIP_SKILLS=1; shift ;;
    --skip-rule) SKIP_RULE=1; shift ;;
    --force) FORCE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[[ -n "$PROJECT_ROOT" ]] || die "--project-root is required"
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

# Normalize agent aliases
normalize_agent() {
  case "$1" in
    cursor) echo cursor ;;
    claude-code|claude) echo claude-code ;;
    copilot|github-copilot) echo copilot ;;
    codex) echo codex ;;
    devin) echo devin ;;
    *) die "unsupported --agent: $1 (cursor|claude-code|copilot|codex|devin)" ;;
  esac
}

NORMALIZED=()
for a in "${AGENTS[@]+"${AGENTS[@]}"}"; do
  [[ -z "$a" ]] && continue
  NORMALIZED+=("$(normalize_agent "$a")")
done
# unique
if [[ ${#NORMALIZED[@]} -gt 0 ]]; then
  # shellcheck disable=SC2207
  NORMALIZED=($(printf '%s\n' "${NORMALIZED[@]}" | awk 'NF && !seen[$0]++'))
fi

if [[ $SKIP_SKILLS -eq 0 && ${#NORMALIZED[@]} -eq 0 ]]; then
  die "specify at least one --agent (or pass --skip-skills)"
fi

# Project-relative skill dir for agent (Agent Skills conventions)
agent_skills_dir() {
  case "$1" in
    cursor|copilot|codex) echo ".agents/skills" ;;
    claude-code) echo ".claude/skills" ;;
    devin) echo ".devin/skills" ;;
  esac
}

TMP_SRC=""
cleanup() {
  if [[ -n "${TMP_SRC}" && -d "${TMP_SRC}" ]]; then
    rm -rf "${TMP_SRC}"
  fi
}
trap cleanup EXIT

if [[ -n "$FROM_LOCAL" ]]; then
  SOURCE_ROOT="$(cd "$FROM_LOCAL" && pwd)"
  SOURCE_KIND="local:${SOURCE_ROOT}"
elif [[ $USE_REMOTE -eq 1 ]]; then
  REF_EFF="${REF:-}"
  TMP_SRC="$(mktemp -d "${TMPDIR:-/tmp}/solidsdd-install.XXXXXX")"
  echo "Fetching ${REPO}@${REF_EFF:-HEAD} (sparse)…" >&2
  command -v git >/dev/null 2>&1 || die "git is required for remote install (or pass --from-local)"
  CLONE_ARGS=(--depth 1 --filter=blob:none --sparse)
  if [[ -n "$REF_EFF" ]]; then
    CLONE_ARGS+=(--branch "$REF_EFF")
  fi
  git clone "${CLONE_ARGS[@]}" "https://github.com/${REPO}.git" "$TMP_SRC/repo" >&2
  git -C "$TMP_SRC/repo" sparse-checkout set skills schemas rules scripts tools/solidsdd-kg >&2 || \
    git -C "$TMP_SRC/repo" sparse-checkout set skills schemas rules scripts >&2
  SOURCE_ROOT="$(cd "$TMP_SRC/repo" && pwd)"
  SOURCE_KIND="github:${REPO}@$(git -C "$SOURCE_ROOT" rev-parse --short HEAD)"
else
  SOURCE_ROOT="$SOLIDSDD_SRC"
  SOURCE_KIND="local:${SOURCE_ROOT}"
fi

[[ -f "$SOURCE_ROOT/scripts/install-manifest.txt" ]] || \
  die "install-manifest.txt missing in source: $SOURCE_ROOT"
MANIFEST="$SOURCE_ROOT/scripts/install-manifest.txt"

# Resolve vendor path
if [[ "$VENDOR_DIR_REL" = /* ]]; then
  VENDOR_ROOT="$VENDOR_DIR_REL"
else
  VENDOR_ROOT="$PROJECT_ROOT/$VENDOR_DIR_REL"
fi
VENDOR_REL="${VENDOR_ROOT#"$PROJECT_ROOT"/}"
if [[ "$VENDOR_REL" == "$VENDOR_ROOT" ]]; then
  # absolute outside project — store absolute in tooling
  VENDOR_REL_FOR_META="$VENDOR_ROOT"
else
  VENDOR_REL_FOR_META="$VENDOR_REL"
fi

if [[ -e "$VENDOR_ROOT" && $FORCE -eq 0 ]]; then
  die "vendor exists: $VENDOR_ROOT (pass --force to replace)"
fi
if [[ -e "$VENDOR_ROOT" && $FORCE -eq 1 ]]; then
  rm -rf "$VENDOR_ROOT"
fi
mkdir -p "$VENDOR_ROOT"

copy_path() {
  local rel="$1"
  local src="$SOURCE_ROOT/$rel"
  local dst="$VENDOR_ROOT/$rel"
  if [[ ! -e "$src" ]]; then
    echo "warning: missing in source (skip): $rel" >&2
    return 0
  fi
  mkdir -p "$(dirname "$dst")"
  if [[ -d "$src" ]]; then
    mkdir -p "$dst"
    # Copy tree but drop obvious non-runtime junk
    if command -v rsync >/dev/null 2>&1; then
      rsync -a \
        --exclude '__pycache__/' \
        --exclude '*.pyc' \
        --exclude 'test_*.py' \
        --exclude '*_test.go' \
        --exclude '.git/' \
        "$src"/ "$dst"/
    else
      cp -a "$src"/. "$dst"/
      find "$dst" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
      find "$dst" -name 'test_*.py' -delete 2>/dev/null || true
    fi
  else
    cp -a "$src" "$dst"
  fi
}

echo "Vendoring into $VENDOR_ROOT …" >&2
while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line%%#*}"
  line="$(echo "$line" | sed 's/[[:space:]]*$//;s/^[[:space:]]*//')"
  [[ -z "$line" ]] && continue
  copy_path "$line"
done < "$MANIFEST"

if [[ $WITH_KG -eq 1 ]]; then
  echo "Vendoring tools/solidsdd-kg …" >&2
  copy_path "tools/solidsdd-kg"
  # Drop tests inside kg module if rsync didn't
  find "$VENDOR_ROOT/tools/solidsdd-kg" -name '*_test.go' -delete 2>/dev/null || true
  if command -v go >/dev/null 2>&1; then
    mkdir -p "$VENDOR_ROOT/bin"
    (cd "$VENDOR_ROOT/tools/solidsdd-kg" && go build -o "$VENDOR_ROOT/bin/solidsdd-kg" ./cmd/solidsdd-kg)
    echo "Built $VENDOR_ROOT/bin/solidsdd-kg" >&2
  else
    echo "warning: Go not found; kg sources vendored but binary not built" >&2
  fi
fi

# Ensure config.yaml exists (defaults)
CFG="$PROJECT_ROOT/.solidsdd/config.yaml"
mkdir -p "$PROJECT_ROOT/.solidsdd"
if [[ ! -f "$CFG" ]]; then
  if [[ -f "$SOURCE_ROOT/.solidsdd/config.yaml" ]]; then
    cp "$SOURCE_ROOT/.solidsdd/config.yaml" "$CFG"
  else
    cat > "$CFG" <<'YAML'
version: "1"
paths:
  solidsdd: .solidsdd
  active_change: .solidsdd/active-change.json
  changes: .solidsdd/changes
  host_toolchain: .solidsdd/host-toolchain.json
  kg: .solidsdd/kg
  cache: .solidsdd-cache
  knowledge:
    - knowledge
  requirements: requirements
  requirements_glob: requirements/**/*.feature
  openapi: openapi/openapi.yaml
  graphql: graphql/schema.graphql
  contracts: contracts
  formal: formal
  contract_tests_ts: tests/contracts
  contract_tests_ruby: spec/contracts
YAML
  fi
  echo "Wrote $CFG" >&2
fi

# tooling metadata
TOOLING="$PROJECT_ROOT/.solidsdd/tooling.json"
INSTALLED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
python3 - "$TOOLING" "$VENDOR_REL_FOR_META" "$SOURCE_KIND" "$INSTALLED_AT" "$WITH_KG" "${NORMALIZED[@]+"${NORMALIZED[@]}"}" <<'PY'
import json, sys
path, vendor, source, installed_at, with_kg, *agents = sys.argv[1:]
data = {
    "version": "1",
    "vendor_root": vendor,
    "source": source,
    "installed_at": installed_at,
    "agents": agents,
    "with_kg": with_kg == "1",
    "scripts_dir": f"{vendor.rstrip('/')}/scripts",
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY
echo "Wrote $TOOLING" >&2

install_skills_for_agent() {
  local agent="$1"
  local dest_rel
  dest_rel="$(agent_skills_dir "$agent")"
  local dest="$PROJECT_ROOT/$dest_rel"
  mkdir -p "$dest"
  local skill
  for skill in "$VENDOR_ROOT"/skills/solidsdd-*; do
    [[ -d "$skill" ]] || continue
    local name
    name="$(basename "$skill")"
    if [[ -e "$dest/$name" && $FORCE -eq 0 ]]; then
      die "skill exists: $dest/$name (pass --force)"
    fi
    rm -rf "$dest/$name"
    cp -a "$skill" "$dest/$name"
  done
  echo "Installed skills → $dest_rel/ (agent=$agent)" >&2
}

if [[ $SKIP_SKILLS -eq 0 ]]; then
  # Deduplicate destination dirs (cursor/copilot/codex share .agents/skills)
  SEEN_DEST=""
  for agent in "${NORMALIZED[@]}"; do
    d="$(agent_skills_dir "$agent")"
    case " $SEEN_DEST " in
      *" $d "*) echo "Skills already installed at $d (shared by $agent)" >&2; continue ;;
    esac
    SEEN_DEST="$SEEN_DEST $d"
    install_skills_for_agent "$agent"
  done
fi

# Cursor project rule
if [[ $SKIP_RULE -eq 0 ]]; then
  for agent in "${NORMALIZED[@]+"${NORMALIZED[@]}"}"; do
    if [[ "$agent" == "cursor" ]]; then
      RULE_SRC="$VENDOR_ROOT/rules/solidsdd.mdc"
      [[ -f "$RULE_SRC" ]] || RULE_SRC="$VENDOR_ROOT/skills/solidsdd-loop/references/project-rule.mdc"
      if [[ -f "$RULE_SRC" ]]; then
        mkdir -p "$PROJECT_ROOT/.cursor/rules"
        cp "$RULE_SRC" "$PROJECT_ROOT/.cursor/rules/solidsdd.mdc"
        echo "Installed .cursor/rules/solidsdd.mdc" >&2
      fi
    fi
  done
fi

# Python venv inside vendor
if [[ $SKIP_PIP -eq 0 ]]; then
  REQ="$VENDOR_ROOT/scripts/requirements.txt"
  if [[ -f "$REQ" ]] && command -v python3 >/dev/null 2>&1; then
    VENV="$VENDOR_ROOT/.venv"
    if [[ ! -d "$VENV" ]]; then
      python3 -m venv "$VENV"
    fi
    "$VENV/bin/pip" install -q -r "$REQ"
    echo "Python deps installed in $VENV" >&2
  else
    echo "warning: skip pip (no python3 or requirements.txt)" >&2
  fi
fi

# Smoke: lint --help / run-state --help
LINT="$VENDOR_ROOT/scripts/solidsdd-lint.sh"
if [[ -x "$LINT" ]] || [[ -f "$LINT" ]]; then
  chmod +x "$VENDOR_ROOT"/scripts/solidsdd-*.sh 2>/dev/null || true
  if "$LINT" --help >/dev/null 2>&1 || "$LINT" -h >/dev/null 2>&1; then
    :
  else
    # lint has no --help; try importing via dry run expecting exit on missing change
    if [[ -x "$VENDOR_ROOT/.venv/bin/python" ]]; then
      "$VENDOR_ROOT/.venv/bin/python" -c "import jsonschema, yaml" 2>/dev/null \
        && echo "Smoke: Python deps OK" >&2 \
        || echo "warning: Python deps import failed" >&2
    fi
  fi
fi

cat <<EOF >&2
Install complete.

  vendor:  $VENDOR_REL_FOR_META
  tooling: .solidsdd/tooling.json
  config:  .solidsdd/config.yaml

Run mechanical tools from the project root, e.g.:
  ${VENDOR_REL_FOR_META}/scripts/solidsdd-lint.sh --project-root .
  ${VENDOR_REL_FOR_META}/scripts/solidsdd-host-toolchain.sh --project-root .
  ${VENDOR_REL_FOR_META}/scripts/solidsdd-run-state.sh --project-root . …

Agents should prefer scripts under vendor_root from tooling.json (not a separate solid_sdd clone).
EOF
