#!/usr/bin/env bash
# Run TLC on a TLA+ spec. Usage: tlc.sh Spec.tla [-config Spec.cfg ...]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
JAR="${ROOT}/tla2tools.jar"

if [[ ! -f "$JAR" ]]; then
  echo "Missing $JAR — run: tools/tla/fetch-tla2tools.sh" >&2
  exit 2
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 Spec.tla [TLC args...]" >&2
  exit 2
fi

run_java() {
  if command -v mise >/dev/null 2>&1; then
    mise exec java -- java "$@"
  elif command -v java >/dev/null 2>&1; then
    java "$@"
  else
    echo "Java not found. Install JDK 17+ (e.g. mise install java@temurin-21)." >&2
    exit 2
  fi
}

SPEC="$1"
shift
run_java -cp "$JAR" tlc2.TLC -workers auto "$@" "$SPEC"
