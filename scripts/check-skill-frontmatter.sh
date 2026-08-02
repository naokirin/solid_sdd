#!/usr/bin/env bash
# Validate solidsdd-* SKILL.md YAML frontmatter basics.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import re
import sys

skills = sorted(Path("skills").glob("solidsdd-*/SKILL.md"))
names = []
errors = []
for path in skills:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(f"{path}: missing opening frontmatter")
        continue
    end = text.find("\n---\n", 4)
    if end < 0:
        errors.append(f"{path}: missing closing frontmatter")
        continue
    fm = text[4:end]
    m = re.search(r"^name:\s*(\S+)\s*$", fm, re.M)
    if not m:
        errors.append(f"{path}: missing name")
        continue
    name = m.group(1)
    names.append(name)
    d = re.search(r"^description:\s*>-\s*\n((?:  .*\n)+)", fm, re.M)
    if not d:
        # allow folded description on one line
        d2 = re.search(r"^description:\s*(.+)$", fm, re.M)
        if not d2:
            errors.append(f"{path}: missing description")
            continue
        desc = d2.group(1).strip()
    else:
        desc = " ".join(line.strip() for line in d.group(1).splitlines())
    if len(desc) < 20:
        errors.append(f"{path}: description too short ({len(desc)})")
    if len(desc) > 1024:
        errors.append(f"{path}: description too long ({len(desc)})")
    expected_dir = path.parent.name
    if name != expected_dir and name.replace(".", "-") != expected_dir:
        # allow solidsdd.brief vs solidsdd-brief mismatch? Our names use solidsdd-brief style
        if name != expected_dir:
            # frontmatter name should match directory for gh skill
            if name != expected_dir:
                errors.append(f"{path}: name {name!r} != dir {expected_dir!r}")

dupes = {n for n in names if names.count(n) > 1}
if dupes:
    errors.append(f"duplicate skill names: {sorted(dupes)}")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"ok  {len(skills)} skills, unique names")
PY
