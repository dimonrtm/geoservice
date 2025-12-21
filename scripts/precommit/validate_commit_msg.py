#!/usr/bin/env python
from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOWED_TYPES = ("feat", "fix", "docs", "chore", "ci", "refactor", "test")
PATTERN = re.compile(rf"^({'|'.join(ALLOWED_TYPES)}):\s+\S.+$")

BANNED_EXACT = {"fix", "update", "wip", "temp"}


def main() -> int:
    # commit-msg stage passes the path to the commit message file
    if len(sys.argv) < 2:
        print("commit-msg hook: missing commit message file path")
        return 1

    msg_file = Path(sys.argv[1])
    raw = msg_file.read_text(encoding="utf-8", errors="ignore")
    # ignore comments
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    if not lines:
        print("❌ Commit message is empty.")
        return 1

    first = lines[0]

    if first.strip().lower() in BANNED_EXACT:
        print(f"❌ Bad commit message '{first}'. Use format: <type>: <description>")
        print(f"Allowed types: {', '.join(ALLOWED_TYPES)}")
        return 1

    if not PATTERN.match(first):
        print("❌ Commit message must match: <type>: <description>")
        print(f"Allowed types: {', '.join(ALLOWED_TYPES)}")
        print(f"Got: {first}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
