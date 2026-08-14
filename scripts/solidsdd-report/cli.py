#!/usr/bin/env python3
"""CLI entry point for solidsdd-report tooling: `collect` / `highlight` / `diagram`."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import collect as collectmod  # noqa: E402
import diagram as diagrammod  # noqa: E402
import highlight as highlightmod  # noqa: E402
import render as rendermod  # noqa: E402

_COMMANDS = ("collect", "highlight", "diagram", "render")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in _COMMANDS:
        print(
            "usage: solidsdd-report.sh {collect|highlight|diagram|render} [options]",
            file=sys.stderr,
        )
        return 2
    command, rest = args[0], args[1:]
    if command == "collect":
        return collectmod.main(rest)
    if command == "highlight":
        return highlightmod.main(rest)
    if command == "diagram":
        return diagrammod.main(rest)
    return rendermod.main(rest)


if __name__ == "__main__":
    raise SystemExit(main())
