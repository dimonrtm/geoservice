#!/usr/bin/env python3
"""Print a deterministic read-only audit of repo-local agent memory."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from memory_audit import audit, format_markdown, format_text


def parse_today(value: str) -> date:
    return date.fromisoformat(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument(
        "--today",
        type=parse_today,
        help="ISO date override for deterministic audits.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "markdown"),
        default="text",
        help="Report format written to stdout.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        parser.error(f"Repository root does not exist: {root}")

    report = audit(root, today=args.today)
    formatter = format_markdown if args.format == "markdown" else format_text
    print(formatter(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
