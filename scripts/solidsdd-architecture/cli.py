#!/usr/bin/env python3
"""CLI entry point for the Architecture Model: `validate` / `project` subcommands."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import project as projectmod  # noqa: E402
import validate as validatemod  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in ("validate", "project"):
        print(
            "usage: solidsdd-architecture.sh {validate|project} [options]",
            file=sys.stderr,
        )
        return 2
    command, rest = args[0], args[1:]
    if command == "validate":
        return validatemod.main(rest)
    return projectmod.main(rest)


if __name__ == "__main__":
    raise SystemExit(main())
