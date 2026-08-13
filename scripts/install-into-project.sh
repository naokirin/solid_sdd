#!/usr/bin/env bash
# Install solid_sdd (skills + mechanical tooling) into a consuming project.
# Does not use a skill-only CLI — one managed tree keeps skills and tooling in sync.
#
# Usage (from a solid_sdd checkout):
#   scripts/install-into-project.sh --project-root DIR --agent cursor
#   scripts/install-into-project.sh --project-root DIR --agent cursor,claude-code \
#       --from-local /path/to/solid_sdd
#   scripts/install-into-project.sh --project-root DIR --agent copilot \
#       --repo naokirin/solid_sdd --ref main
#
# Usage (no checkout — fetch script from GitHub):
#   curl -fsSL https://raw.githubusercontent.com/naokirin/solid_sdd/main/scripts/install-into-project.sh | \
#     bash -s -- --project-root DIR --agent cursor
#
# Default vendor: <project>/.solidsdd/vendor/solid_sdd
# Override with --vendor-dir (project-relative or absolute).
set -euo pipefail

# Resolve local solid_sdd root when this file lives in a checkout.
# Empty for curl|bash / standalone download (no install-manifest beside the script).
SOLIDSDD_SRC=""
_SCRIPT="${BASH_SOURCE[0]:-}"
if [[ -n "$_SCRIPT" && -f "$_SCRIPT" ]]; then
  case "$_SCRIPT" in
    /dev/fd/*|/proc/self/fd/*) ;;
    *)
      _candidate="$(cd "$(dirname "$_SCRIPT")/.." && pwd)"
      if [[ -f "$_candidate/scripts/install-manifest.txt" ]]; then
        SOLIDSDD_SRC="$_candidate"
      fi
      ;;
  esac
fi
unset _SCRIPT _candidate

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
LANGUAGE=""

usage() {
  cat <<'EOF'
Install solid_sdd (skills + mechanical tooling) into a consuming project.

Usage:
  scripts/install-into-project.sh --project-root DIR --agent cursor
  curl -fsSL https://raw.githubusercontent.com/naokirin/solid_sdd/main/scripts/install-into-project.sh | \
    bash -s -- --project-root DIR --agent cursor

Options:
  --project-root DIR   Consuming project root (required)
  --vendor-dir PATH    Vendor install path (default: .solidsdd/vendor/solid_sdd)
  --agent LIST         Comma-separated: cursor, claude-code, copilot, codex, devin
                       (repeatable; at least one required unless --skip-skills)
  --from-local DIR     Copy from a local solid_sdd checkout
                       (default: this repository when run from a checkout)
  --repo OWNER/REPO    Fetch from GitHub instead of local (default: naokirin/solid_sdd)
  --ref REF            Git ref/tag/SHA for remote install (implies remote fetch;
                       default: main when remote / no local checkout)
  --with-kg            Also vendor tools/solidsdd-kg and build bin/solidsdd-kg if Go present
  --skip-pip           Do not create vendor .venv / install PyYAML+jsonschema
  --skip-skills        Do not copy skills into agent directories
  --skip-rule          Do not install/update the project rule for any agent
  --language TAG       Working language for solid_sdd artifacts (e.g. en, ja).
                       Written to .solidsdd/config.yaml -> working_language
                       (shared by every agent's rule). If omitted and a
                       terminal is available, you'll be prompted; otherwise
                       defaults to `en` (existing value is left untouched on
                       a silent, non-interactive re-install).
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
    --language) LANGUAGE="${2:-}"; shift 2 ;;
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

# Resolve working language: --language > interactive prompt (/dev/tty, if
# available) > default `en`. Asked up front so the (possibly slow) fetch
# below doesn't leave the prompt stranded after a long wait.
#
# LANGUAGE_EXPLICIT distinguishes "user actually chose this" (flag, or had a
# chance to answer the prompt) from "silently defaulted because no terminal
# was available" — only the former is allowed to overwrite an already
# configured `working_language` in an existing .solidsdd/config.yaml (see
# below), so a non-interactive re-install (e.g. CI) can never quietly reset
# a project's language back to `en`.
LANGUAGE_EXPLICIT=0
if [[ $SKIP_RULE -eq 0 ]]; then
  if [[ -n "$LANGUAGE" ]]; then
    LANGUAGE_EXPLICIT=1
  else
    # `test -r/-w /dev/tty` checks the special file's permission bits, which
    # are typically world-readable regardless of whether this process has a
    # controlling terminal — so it's not a reliable "are we interactive?"
    # signal by itself. Instead, attempt the read and trust *its* exit
    # status: opening /dev/tty for redirection fails outright (no controlling
    # terminal → command never runs → nonzero) when there's nothing to
    # prompt on, e.g. under CI or a non-pty tool sandbox.
    if read -r -p "Working language for solid_sdd artifacts (BCP-47 tag, e.g. en, ja) [en]: " LANGUAGE < /dev/tty > /dev/tty 2>/dev/null; then
      LANGUAGE="${LANGUAGE:-en}"
      LANGUAGE_EXPLICIT=1
    else
      LANGUAGE="en"
    fi
  fi
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
RULE_TMP=""
cleanup() {
  if [[ -n "${TMP_SRC}" && -d "${TMP_SRC}" ]]; then
    rm -rf "${TMP_SRC}"
  fi
  if [[ -n "${RULE_TMP}" && -f "${RULE_TMP}" ]]; then
    rm -f "${RULE_TMP}"
  fi
}
trap cleanup EXIT

# No local checkout (curl|bash / standalone) → remote fetch with --ref defaulting to main
if [[ -z "$FROM_LOCAL" && -z "$SOLIDSDD_SRC" ]]; then
  USE_REMOTE=1
fi

if [[ -n "$FROM_LOCAL" ]]; then
  SOURCE_ROOT="$(cd "$FROM_LOCAL" && pwd)"
  SOURCE_KIND="local:${SOURCE_ROOT}"
elif [[ $USE_REMOTE -eq 1 ]]; then
  REF_EFF="${REF:-main}"
  TMP_SRC="$(mktemp -d "${TMPDIR:-/tmp}/solidsdd-install.XXXXXX")"
  echo "Fetching ${REPO}@${REF_EFF} (sparse)…" >&2
  command -v git >/dev/null 2>&1 || die "git is required for remote install (or pass --from-local)"
  git clone --depth 1 --filter=blob:none --sparse --branch "$REF_EFF" \
    "https://github.com/${REPO}.git" "$TMP_SRC/repo" >&2
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
CFG_CREATED=0
mkdir -p "$PROJECT_ROOT/.solidsdd"
if [[ ! -f "$CFG" ]]; then
  CFG_CREATED=1
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

# Working language lives in config.yaml only (single SoT every agent's rule
# points at) — set it on a fresh config.yaml, or when the caller explicitly
# chose a language this run. Never touch it on a silent (no-flag, no-tty)
# re-install of an existing config.yaml, so CI re-runs can't reset it.
if [[ $SKIP_RULE -eq 0 && ( $CFG_CREATED -eq 1 || $LANGUAGE_EXPLICIT -eq 1 ) ]]; then
  python3 - "$CFG" "$LANGUAGE" <<'PY'
import re, sys, pathlib
cfg, lang = sys.argv[1], sys.argv[2]
p = pathlib.Path(cfg)
text = p.read_text(encoding="utf-8")
line = f'working_language: "{lang}"'
if re.search(r"(?m)^working_language:.*$", text):
    text = re.sub(r"(?m)^working_language:.*$", line, text, count=1)
else:
    m = re.search(r"(?m)^version:.*$", text)
    if m:
        text = text[: m.end()] + "\n" + line + text[m.end():]
    else:
        text = line + "\n" + text
p.write_text(text, encoding="utf-8")
PY
  echo "Set .solidsdd/config.yaml -> working_language: \"${LANGUAGE}\"" >&2
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

# Project rule (per agent). The rule body is identical across every agent
# and every install — it points at `.solidsdd/config.yaml` -> working_language
# rather than embedding a literal language value, so there is nothing here
# to template per install.
#
# Cursor / Devin get a dedicated solid_sdd-only file (safe to overwrite each
# install). Claude Code / Codex / Copilot share a general-purpose project
# instructions file the user likely already has content in, so we upsert a
# marked block instead of overwriting the whole file.
if [[ $SKIP_RULE -eq 0 ]]; then
  RULE_SRC="$VENDOR_ROOT/rules/solidsdd.mdc"
  [[ -f "$RULE_SRC" ]] || RULE_SRC="$VENDOR_ROOT/skills/solidsdd-loop/references/project-rule.mdc"

  if [[ -f "$RULE_SRC" ]]; then
    RULE_TMP="$(mktemp "${TMPDIR:-/tmp}/solidsdd-rule.XXXXXX")"

    # Body without the Cursor-specific YAML frontmatter.
    render_rule_body() {
      awk '
        NR == 1 && $0 == "---" { fm = 1; next }
        fm == 1 && $0 == "---" { fm = 0; next }
        fm == 1 { next }
        { print }
      ' "$RULE_SRC"
    }
    render_rule_body > "$RULE_TMP"

    # Insert/replace a marked block in $1, preserving any surrounding
    # user content. Creates the file if missing.
    upsert_marked_block() {
      local target="$1"
      python3 - "$target" "$RULE_TMP" <<'PY'
import sys, pathlib
target, body_path = sys.argv[1], sys.argv[2]
body = pathlib.Path(body_path).read_text(encoding="utf-8").rstrip("\n")
begin = "<!-- solid_sdd:begin (auto-generated by install-into-project.sh; edit the source in your solid_sdd checkout, not here) -->"
end = "<!-- solid_sdd:end -->"
block = f"{begin}\n{body}\n{end}\n"
p = pathlib.Path(target)
if p.exists():
    text = p.read_text(encoding="utf-8")
    if begin in text and end in text:
        pre, rest = text.split(begin, 1)
        _, post = rest.split(end, 1)
        new_text = pre + block + post
    else:
        sep = "\n" if text.endswith("\n") else "\n\n"
        new_text = text + sep + block
else:
    new_text = block
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(new_text, encoding="utf-8")
PY
    }

    install_rule_for_agent() {
      local agent="$1"
      case "$agent" in
        cursor)
          mkdir -p "$PROJECT_ROOT/.cursor/rules"
          cp "$RULE_SRC" "$PROJECT_ROOT/.cursor/rules/solidsdd.mdc"
          echo "Installed .cursor/rules/solidsdd.mdc" >&2
          ;;
        devin)
          mkdir -p "$PROJECT_ROOT/.devin/rules"
          cp "$RULE_TMP" "$PROJECT_ROOT/.devin/rules/solidsdd.md"
          echo "Installed .devin/rules/solidsdd.md" >&2
          ;;
        claude-code)
          upsert_marked_block "$PROJECT_ROOT/CLAUDE.md"
          echo "Updated CLAUDE.md (solid_sdd block)" >&2
          ;;
        codex)
          upsert_marked_block "$PROJECT_ROOT/AGENTS.md"
          echo "Updated AGENTS.md (solid_sdd block)" >&2
          ;;
        copilot)
          upsert_marked_block "$PROJECT_ROOT/.github/copilot-instructions.md"
          echo "Updated .github/copilot-instructions.md (solid_sdd block)" >&2
          ;;
      esac
    }

    for agent in "${NORMALIZED[@]+"${NORMALIZED[@]}"}"; do
      install_rule_for_agent "$agent"
    done
  else
    echo "warning: rule source missing in vendor; skip project rule install" >&2
  fi
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
